"""Offline checks for training batch math and file layout (no GPU required)."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRAINING = ROOT / "training"


def _assign_int(source: str, name: str) -> int:
    # Match NAME = <int expr> e.g. 256 or 2**14
    m = re.search(rf"^{name}\s*=\s*(.+)$", source, re.M)
    if not m:
        raise AssertionError(f"Could not find {name}")
    expr = m.group(1).split("#")[0].strip()
    node = ast.parse(expr, mode="eval")

    def _eval(n):
        if isinstance(n, ast.Expression):
            return _eval(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return int(n.value)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return -_eval(n.operand)
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Pow):
            return int(_eval(n.left) ** _eval(n.right))
        if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Mult, ast.Add, ast.Sub, ast.FloorDiv)):
            l, r = _eval(n.left), _eval(n.right)
            if isinstance(n.op, ast.Mult):
                return int(l * r)
            if isinstance(n.op, ast.Add):
                return int(l + r)
            if isinstance(n.op, ast.Sub):
                return int(l - r)
            return int(l // r)
        raise AssertionError(f"Unsupported expression for {name}: {expr}")

    return _eval(node)


def test_required_files_exist():
    required = [
        TRAINING / "prepare.py",
        TRAINING / "train.py",
        TRAINING / "program.md",
        TRAINING / "requirements.txt",
        TRAINING / "pyproject.toml",
    ]
    missing = [str(p) for p in required if not p.exists()]
    assert not missing, f"Missing training files: {missing}"


def test_batch_config_divisible():
    prepare_src = (TRAINING / "prepare.py").read_text(encoding="utf-8")
    train_src = (TRAINING / "train.py").read_text(encoding="utf-8")
    max_seq_len = _assign_int(prepare_src, "MAX_SEQ_LEN")
    device_bs = _assign_int(train_src, "DEVICE_BATCH_SIZE")
    total_bs = _assign_int(train_src, "TOTAL_BATCH_SIZE")
    tokens_per = device_bs * max_seq_len
    assert total_bs % tokens_per == 0, (
        f"TOTAL_BATCH_SIZE={total_bs} not divisible by "
        f"DEVICE_BATCH_SIZE*MAX_SEQ_LEN={device_bs}*{max_seq_len}={tokens_per}"
    )


def test_small_compute_defaults():
    prepare_src = (TRAINING / "prepare.py").read_text(encoding="utf-8")
    train_src = (TRAINING / "train.py").read_text(encoding="utf-8")
    assert _assign_int(prepare_src, "MAX_SEQ_LEN") == 256
    assert _assign_int(prepare_src, "VOCAB_SIZE") == 1024
    assert _assign_int(prepare_src, "TIME_BUDGET") == 300
    assert _assign_int(prepare_src, "EVAL_TOKENS") == 65536
    assert _assign_int(train_src, "DEPTH") == 4
    assert 'WINDOW_PATTERN = "L"' in train_src


def test_eval_tokens_compatible_with_default_batch():
    prepare_src = (TRAINING / "prepare.py").read_text(encoding="utf-8")
    train_src = (TRAINING / "train.py").read_text(encoding="utf-8")
    eval_tokens = _assign_int(prepare_src, "EVAL_TOKENS")
    max_seq_len = _assign_int(prepare_src, "MAX_SEQ_LEN")
    device_bs = _assign_int(train_src, "DEVICE_BATCH_SIZE")
    per_step = device_bs * max_seq_len
    assert eval_tokens // per_step >= 1


if __name__ == "__main__":
    tests = [
        test_required_files_exist,
        test_batch_config_divisible,
        test_small_compute_defaults,
        test_eval_tokens_compatible_with_default_batch,
    ]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception as e:
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    sys.exit(1 if failed else 0)
