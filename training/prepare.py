"""
One-time data preparation for AutoResearch experiments (TinyStories / Colab).
Downloads TinyStories, builds train/val parquet splits, and trains a BPE tokenizer.

Usage:
    python prepare.py
    python prepare.py --smoke   # tiny local sample for pipeline checks (no full download)

Data and tokenizer default to ~/.cache/autoresearch-platform/
Override with AUTORESEARCH_CACHE.
"""

import os
import sys
import time
import math
import argparse
import pickle

import requests
import pyarrow as pa
import pyarrow.parquet as pq
import rustbpe
import tiktoken
import torch

# ---------------------------------------------------------------------------
# Constants (fixed for the research loop; change intentionally, not casually)
# ---------------------------------------------------------------------------

MAX_SEQ_LEN = 256        # context length (Colab / small-compute default)
TIME_BUDGET = 300        # training time budget in seconds (5 minutes)
# Val tokens for evaluate_bpb. Must be divisible by (DEVICE_BATCH_SIZE * MAX_SEQ_LEN)
# at train time. With DEVICE_BATCH_SIZE=32 → 8192 tokens/step → 8 eval steps.
EVAL_TOKENS = 65536

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CACHE_DIR = os.environ.get(
    "AUTORESEARCH_CACHE",
    os.path.join(os.path.expanduser("~"), ".cache", "autoresearch-platform"),
)
DATA_DIR = os.path.join(CACHE_DIR, "data")
TOKENIZER_DIR = os.path.join(CACHE_DIR, "tokenizer")

# TinyStories GPT-4 clean (single parquet). Suggested row splits from the dataset card:
#   0..9,999       test
#   10,000..19,999 val
#   20,000..end    train
DATASET_URL = (
    "https://huggingface.co/datasets/karpathy/tinystories-gpt4-clean/"
    "resolve/main/tinystories_gpt4_clean.parquet"
)
RAW_FILENAME = "tinystories_gpt4_clean.parquet"
TRAIN_FILENAME = "train.parquet"
VAL_FILENAME = "val.parquet"
VAL_ROW_START = 10_000
VAL_ROW_END = 20_000
TRAIN_ROW_START = 20_000

VOCAB_SIZE = 1024

# BPE split pattern (GPT-4 style, with \p{N}{1,2} instead of {1,3})
SPLIT_PATTERN = r"""'(?i:[sdmt]|ll|ve|re)|[^\r\n\p{L}\p{N}]?+\p{L}+|\p{N}{1,2}| ?[^\s\p{L}\p{N}]++[\r\n]*|\s*[\r\n]|\s+(?!\S)|\s+"""

SPECIAL_TOKENS = [f"<|reserved_{i}|>" for i in range(4)]
BOS_TOKEN = "<|reserved_0|>"

# ---------------------------------------------------------------------------
# Data download / split
# ---------------------------------------------------------------------------

def _download_file(url, filepath):
    """Download a file with retries."""
    if os.path.exists(filepath):
        return True
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"  Downloading {os.path.basename(filepath)} (attempt {attempt}/{max_attempts})...")
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            temp_path = filepath + ".tmp"
            with open(temp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
            os.rename(temp_path, filepath)
            print(f"  Saved {filepath}")
            return True
        except (requests.RequestException, IOError) as e:
            print(f"  Attempt {attempt}/{max_attempts} failed: {e}")
            for path in [filepath + ".tmp", filepath]:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass
            if attempt < max_attempts:
                time.sleep(2 ** attempt)
    return False


def _write_table_slice(table, start, end, out_path):
    end = min(end, table.num_rows)
    start = min(start, end)
    slice_table = table.slice(start, end - start)
    pq.write_table(slice_table, out_path)
    print(f"  Wrote {out_path} ({slice_table.num_rows} rows)")


def download_and_split_data(keep_raw=False):
    """Download TinyStories parquet and write train/val split files."""
    os.makedirs(DATA_DIR, exist_ok=True)
    train_path = os.path.join(DATA_DIR, TRAIN_FILENAME)
    val_path = os.path.join(DATA_DIR, VAL_FILENAME)
    if os.path.exists(train_path) and os.path.exists(val_path):
        print(f"Data: train/val already present at {DATA_DIR}")
        return

    raw_path = os.path.join(DATA_DIR, RAW_FILENAME)
    ok = _download_file(DATASET_URL, raw_path)
    if not ok:
        print("Data: download failed.")
        sys.exit(1)

    print("Data: splitting into train/val parquet files...")
    table = pq.read_table(raw_path, columns=["text"])
    print(f"  Loaded {table.num_rows} rows")
    if table.num_rows <= TRAIN_ROW_START:
        print(f"Data: expected >{TRAIN_ROW_START} rows, got {table.num_rows}")
        sys.exit(1)

    _write_table_slice(table, TRAIN_ROW_START, table.num_rows, train_path)
    _write_table_slice(table, VAL_ROW_START, VAL_ROW_END, val_path)

    if not keep_raw and os.path.exists(raw_path):
        os.remove(raw_path)
        print(f"  Removed raw file {raw_path}")


def write_smoke_data(num_train=200, num_val=50):
    """Write a tiny synthetic TinyStories-like corpus for offline smoke tests."""
    os.makedirs(DATA_DIR, exist_ok=True)
    train_path = os.path.join(DATA_DIR, TRAIN_FILENAME)
    val_path = os.path.join(DATA_DIR, VAL_FILENAME)

    def stories(n, seed):
        texts = []
        for i in range(n):
            texts.append(
                f"Once upon a time there was a little {['cat', 'dog', 'bird', 'fox'][i % 4]} "
                f"named Buddy{seed + i}. The friends played in the garden and learned to share. "
                f"They were happy. The end."
            )
        return texts

    pq.write_table(pa.table({"text": stories(num_train, 0)}), train_path)
    pq.write_table(pa.table({"text": stories(num_val, 10_000)}), val_path)
    print(f"Data: wrote smoke train/val under {DATA_DIR}")

# ---------------------------------------------------------------------------
# Tokenizer training
# ---------------------------------------------------------------------------

def list_parquet_files():
    """Return sorted list of parquet file paths in the data directory."""
    if not os.path.isdir(DATA_DIR):
        return []
    files = sorted(
        f for f in os.listdir(DATA_DIR)
        if f.endswith(".parquet") and not f.endswith(".tmp") and f != RAW_FILENAME
    )
    return [os.path.join(DATA_DIR, f) for f in files]


def text_iterator(max_chars=200_000_000, doc_cap=10_000):
    """Yield documents from the training split only."""
    train_path = os.path.join(DATA_DIR, TRAIN_FILENAME)
    if not os.path.exists(train_path):
        return
    nchars = 0
    pf = pq.ParquetFile(train_path)
    for rg_idx in range(pf.num_row_groups):
        rg = pf.read_row_group(rg_idx)
        for text in rg.column("text").to_pylist():
            doc = text[:doc_cap] if len(text) > doc_cap else text
            nchars += len(doc)
            yield doc
            if nchars >= max_chars:
                return


def train_tokenizer():
    """Train BPE tokenizer using rustbpe, save as tiktoken pickle."""
    tokenizer_pkl = os.path.join(TOKENIZER_DIR, "tokenizer.pkl")
    token_bytes_path = os.path.join(TOKENIZER_DIR, "token_bytes.pt")

    if os.path.exists(tokenizer_pkl) and os.path.exists(token_bytes_path):
        print(f"Tokenizer: already trained at {TOKENIZER_DIR}")
        return

    os.makedirs(TOKENIZER_DIR, exist_ok=True)

    train_path = os.path.join(DATA_DIR, TRAIN_FILENAME)
    val_path = os.path.join(DATA_DIR, VAL_FILENAME)
    if not (os.path.exists(train_path) and os.path.exists(val_path)):
        print("Tokenizer: need train.parquet and val.parquet. Run prepare.py first.")
        sys.exit(1)

    print("Tokenizer: training BPE tokenizer...")
    t0 = time.time()

    tokenizer = rustbpe.Tokenizer()
    vocab_size_no_special = VOCAB_SIZE - len(SPECIAL_TOKENS)
    tokenizer.train_from_iterator(text_iterator(), vocab_size_no_special, pattern=SPLIT_PATTERN)

    pattern = tokenizer.get_pattern()
    mergeable_ranks = {bytes(k): v for k, v in tokenizer.get_mergeable_ranks()}
    tokens_offset = len(mergeable_ranks)
    special_tokens = {name: tokens_offset + i for i, name in enumerate(SPECIAL_TOKENS)}
    enc = tiktoken.Encoding(
        name="rustbpe",
        pat_str=pattern,
        mergeable_ranks=mergeable_ranks,
        special_tokens=special_tokens,
    )

    with open(tokenizer_pkl, "wb") as f:
        pickle.dump(enc, f)

    t1 = time.time()
    print(f"Tokenizer: trained in {t1 - t0:.1f}s, saved to {tokenizer_pkl}")

    print("Tokenizer: building token_bytes lookup...")
    special_set = set(SPECIAL_TOKENS)
    token_bytes_list = []
    for token_id in range(enc.n_vocab):
        token_str = enc.decode([token_id])
        if token_str in special_set:
            token_bytes_list.append(0)
        else:
            token_bytes_list.append(len(token_str.encode("utf-8")))
    token_bytes_tensor = torch.tensor(token_bytes_list, dtype=torch.int32)
    torch.save(token_bytes_tensor, token_bytes_path)
    print(f"Tokenizer: saved token_bytes to {token_bytes_path}")

    test = "Hello world! Numbers: 123."
    encoded = enc.encode_ordinary(test)
    decoded = enc.decode(encoded)
    assert decoded == test, f"Tokenizer roundtrip failed: {test!r} -> {decoded!r}"
    print(f"Tokenizer: sanity check passed (vocab_size={enc.n_vocab})")

# ---------------------------------------------------------------------------
# Runtime utilities (imported by train.py)
# ---------------------------------------------------------------------------

class Tokenizer:
    """Minimal tokenizer wrapper. Training is handled above."""

    def __init__(self, enc):
        self.enc = enc
        self.bos_token_id = enc.encode_single_token(BOS_TOKEN)

    @classmethod
    def from_directory(cls, tokenizer_dir=TOKENIZER_DIR):
        with open(os.path.join(tokenizer_dir, "tokenizer.pkl"), "rb") as f:
            enc = pickle.load(f)
        return cls(enc)

    def get_vocab_size(self):
        return self.enc.n_vocab

    def get_bos_token_id(self):
        return self.bos_token_id

    def encode(self, text, prepend=None, num_threads=8):
        if prepend is not None:
            prepend_id = prepend if isinstance(prepend, int) else self.enc.encode_single_token(prepend)
        if isinstance(text, str):
            ids = self.enc.encode_ordinary(text)
            if prepend is not None:
                ids.insert(0, prepend_id)
        elif isinstance(text, list):
            ids = self.enc.encode_ordinary_batch(text, num_threads=num_threads)
            if prepend is not None:
                for row in ids:
                    row.insert(0, prepend_id)
        else:
            raise ValueError(f"Invalid input type: {type(text)}")
        return ids

    def decode(self, ids):
        return self.enc.decode(ids)


def get_token_bytes(device="cpu"):
    path = os.path.join(TOKENIZER_DIR, "token_bytes.pt")
    with open(path, "rb") as f:
        try:
            return torch.load(f, map_location=device, weights_only=True)
        except TypeError:
            # Older torch without weights_only=
            return torch.load(f, map_location=device)


def _document_batches(split, tokenizer_batch_size=128):
    """Infinite iterator over document batches from parquet files."""
    train_path = os.path.join(DATA_DIR, TRAIN_FILENAME)
    val_path = os.path.join(DATA_DIR, VAL_FILENAME)
    assert os.path.exists(train_path) and os.path.exists(val_path), (
        "Missing train/val parquet. Run prepare.py first."
    )
    if split == "train":
        parquet_paths = [train_path]
    else:
        parquet_paths = [val_path]
    epoch = 1
    while True:
        for filepath in parquet_paths:
            pf = pq.ParquetFile(filepath)
            for rg_idx in range(pf.num_row_groups):
                rg = pf.read_row_group(rg_idx)
                batch = rg.column("text").to_pylist()
                for i in range(0, len(batch), tokenizer_batch_size):
                    yield batch[i:i + tokenizer_batch_size], epoch
        epoch += 1


def make_dataloader(tokenizer, B, T, split, buffer_size=1000, device=None):
    """
    BOS-aligned dataloader with best-fit packing.
    Every row starts with BOS. Documents packed using best-fit to minimize cropping.
    When no document fits remaining space, crops shortest doc to fill exactly.
    100% utilization (no padding).
    """
    assert split in ["train", "val"]
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    row_capacity = T + 1
    batches = _document_batches(split)
    bos_token = tokenizer.get_bos_token_id()
    doc_buffer = []
    epoch = 1
    pin = device.type == "cuda"

    def refill_buffer():
        nonlocal epoch
        doc_batch, epoch = next(batches)
        token_lists = tokenizer.encode(doc_batch, prepend=bos_token)
        doc_buffer.extend(token_lists)

    row_buffer = torch.empty((B, row_capacity), dtype=torch.long)
    cpu_buffer = torch.empty(2 * B * T, dtype=torch.long, pin_memory=pin)
    device_buffer = torch.empty(2 * B * T, dtype=torch.long, device=device)
    cpu_inputs = cpu_buffer[:B * T].view(B, T)
    cpu_targets = cpu_buffer[B * T:].view(B, T)
    inputs = device_buffer[:B * T].view(B, T)
    targets = device_buffer[B * T:].view(B, T)

    while True:
        for row_idx in range(B):
            pos = 0
            while pos < row_capacity:
                while len(doc_buffer) < buffer_size:
                    refill_buffer()

                remaining = row_capacity - pos

                best_idx = -1
                best_len = 0
                for i, doc in enumerate(doc_buffer):
                    doc_len = len(doc)
                    if doc_len <= remaining and doc_len > best_len:
                        best_idx = i
                        best_len = doc_len

                if best_idx >= 0:
                    doc = doc_buffer.pop(best_idx)
                    row_buffer[row_idx, pos:pos + len(doc)] = torch.tensor(doc, dtype=torch.long)
                    pos += len(doc)
                else:
                    shortest_idx = min(range(len(doc_buffer)), key=lambda i: len(doc_buffer[i]))
                    doc = doc_buffer.pop(shortest_idx)
                    row_buffer[row_idx, pos:pos + remaining] = torch.tensor(doc[:remaining], dtype=torch.long)
                    pos += remaining

        cpu_inputs.copy_(row_buffer[:, :-1])
        cpu_targets.copy_(row_buffer[:, 1:])
        device_buffer.copy_(cpu_buffer, non_blocking=pin)
        yield inputs, targets, epoch

# ---------------------------------------------------------------------------
# Evaluation (primary metric: val_bpb — do not replace)
# ---------------------------------------------------------------------------

@torch.no_grad()
def evaluate_bpb(model, tokenizer, batch_size):
    """
    Bits per byte (BPB): vocab size-independent evaluation metric.
    Sums per-token cross-entropy (in nats), sums target byte lengths,
    then converts nats/byte to bits/byte. Special tokens (byte length 0)
    are excluded from both sums.
    Uses fixed MAX_SEQ_LEN so results are comparable across configs.
    """
    device = next(model.parameters()).device
    token_bytes = get_token_bytes(device=device)
    val_loader = make_dataloader(tokenizer, batch_size, MAX_SEQ_LEN, "val", device=device)
    steps = max(1, EVAL_TOKENS // (batch_size * MAX_SEQ_LEN))
    total_nats = 0.0
    total_bytes = 0
    for _ in range(steps):
        x, y, _ = next(val_loader)
        loss_flat = model(x, y, reduction="none").view(-1)
        y_flat = y.view(-1)
        nbytes = token_bytes[y_flat]
        mask = nbytes > 0
        total_nats += (loss_flat * mask).sum().item()
        total_bytes += nbytes.sum().item()
    return total_nats / (math.log(2) * total_bytes)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare TinyStories data and tokenizer")
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Write a tiny synthetic dataset instead of downloading TinyStories",
    )
    parser.add_argument(
        "--keep-raw",
        action="store_true",
        help="Keep the downloaded raw parquet after splitting",
    )
    parser.add_argument(
        "--force-tokenizer",
        action="store_true",
        help="Retrain tokenizer even if files already exist",
    )
    args = parser.parse_args()

    print(f"Cache directory: {CACHE_DIR}")
    print(f"MAX_SEQ_LEN={MAX_SEQ_LEN} VOCAB_SIZE={VOCAB_SIZE} EVAL_TOKENS={EVAL_TOKENS} TIME_BUDGET={TIME_BUDGET}")
    print()

    if args.smoke:
        write_smoke_data()
    else:
        download_and_split_data(keep_raw=args.keep_raw)
    print()

    if args.force_tokenizer:
        for name in ("tokenizer.pkl", "token_bytes.pt"):
            path = os.path.join(TOKENIZER_DIR, name)
            if os.path.exists(path):
                os.remove(path)

    train_tokenizer()
    print()
    print("Done! Ready to train.")
