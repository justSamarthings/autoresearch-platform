# autoresearch (platform training/)

This is the TinyStories / Colab adaptation of Karpathy AutoResearch for the
AutoResearch Experiment Platform. Training code lives under `training/`.

## Setup

To set up a new experiment, work with the user to:

1. **Agree on a run tag**: propose a tag based on today's date (e.g. `mar5`). The branch `autoresearch/<tag>` must not already exist — this is a fresh run.
2. **Create the branch**: `git checkout -b autoresearch/<tag>` from current main.
3. **Read the in-scope files**:
   - `PROJECT_CONTEXT.md` — platform context.
   - `training/prepare.py` — fixed constants, TinyStories prep, tokenizer, dataloader, evaluation. Do not modify during experiments.
   - `training/train.py` — the file you modify. Model architecture, optimizer, training loop.
4. **Verify data exists**: Check that `~/.cache/autoresearch-platform/` (or `$AUTORESEARCH_CACHE`) contains `data/train.parquet`, `data/val.parquet`, and a tokenizer. If not, run `python prepare.py` from `training/`.
5. **Initialize results.tsv**: Create `training/results.tsv` with just the header row. The baseline will be recorded after the first run.
6. **Confirm and go**: Confirm setup looks good.

Once you get confirmation, kick off the experimentation.

## Experimentation

Each experiment runs on a single NVIDIA GPU (Google Colab for this project). The training script runs for a **fixed time budget of 5 minutes** (wall clock training time, excluding startup/compilation). From `training/`:

```bash
python train.py
```

**What you CAN do:**
- Modify `train.py` — this is the only file you edit. Everything is fair game: model architecture, optimizer, hyperparameters, training loop, batch size, model size, etc.

**What you CANNOT do:**
- Modify `prepare.py`. It is read-only. It contains the fixed evaluation, data loading, tokenizer, and training constants (time budget, sequence length, etc).
- Install new packages or add dependencies beyond `training/requirements.txt` / `training/pyproject.toml`.
- Modify the evaluation harness. The `evaluate_bpb` function in `prepare.py` is the ground truth metric.
- Replace `val_bpb` with another primary metric.

**The goal is simple: get the lowest val_bpb.** Since the time budget is fixed, you don't need to worry about training time — it's always 5 minutes.

**VRAM** is a soft constraint (Colab T4/L4). Some increase is acceptable for meaningful val_bpb gains, but it should not blow up dramatically. Prefer `WINDOW_PATTERN = "L"` on smaller GPUs.

**Batch size constraint:** keep `TOTAL_BATCH_SIZE % (DEVICE_BATCH_SIZE * MAX_SEQ_LEN) == 0`.

**Simplicity criterion**: All else being equal, simpler is better.

**The first run**: Your very first run should always be to establish the baseline, so you will run the training script as is.

## Output format

Once the script finishes it prints a summary like this:

```
---
val_bpb:          0.997900
training_seconds: 300.1
total_seconds:    325.9
peak_vram_mb:     45060.2
mfu_percent:      39.80
total_tokens_M:   499.6
num_steps:        953
num_params_M:     50.3
depth:            4
```

It also writes:
- checkpoint: `training/artifacts/checkpoints/<experiment_id>.pt`
- result JSON: `training/artifacts/results/<experiment_id>.json`

Extract the key metric:

```
grep "^val_bpb:" run.log
```

## Logging results

When an experiment is done, log it to `training/results.tsv` (tab-separated, NOT comma-separated).

```
commit	val_bpb	memory_gb	status	description
```

1. git commit hash (short, 7 chars)
2. val_bpb achieved — use 0.000000 for crashes
3. peak memory in GB, round to .1f (divide peak_vram_mb by 1024)
4. status: `keep`, `discard`, or `crash`
5. short text description

Do not commit `results.tsv` or `training/artifacts/`.

## The experiment loop

LOOP FOREVER:

1. Look at the git state
2. Tune `train.py`
3. git commit
4. Run: `python train.py > run.log 2>&1`
5. Read: `grep "^val_bpb:\|^peak_vram_mb:" run.log`
6. If empty, inspect the crash and fix or discard
7. Record in results.tsv
8. If val_bpb improved (lower), keep the commit; else `git reset` back

**Timeout**: If a run exceeds 10 minutes, kill it and treat as failure.

**NEVER STOP** once the loop has begun until the human interrupts you.
