"""
Verify a training checkpoint can be loaded and rebuilt.

Usage (from repo root or training/):
    python scripts/verify_checkpoint.py training/artifacts/checkpoints/<id>.pt
"""

from __future__ import annotations

import argparse
import os
import sys

import torch

TRAINING_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "training"))
if TRAINING_DIR not in sys.path:
    sys.path.insert(0, TRAINING_DIR)

from train import GPT, GPTConfig, load_checkpoint  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", help="Path to .pt checkpoint")
    args = parser.parse_args()

    payload = load_checkpoint(args.checkpoint, map_location="cpu")
    assert "model_state_dict" in payload, "missing model_state_dict"
    assert "config" in payload, "missing config"

    cfg = GPTConfig(**payload["config"])
    model = GPT(cfg)
    missing, unexpected = model.load_state_dict(payload["model_state_dict"], strict=False)
    # Rotary buffers are persistent=False — expect them missing from checkpoint
    missing = [m for m in missing if m not in ("cos", "sin")]
    assert not missing, f"missing keys: {missing}"
    assert not unexpected, f"unexpected keys: {unexpected}"

    model.eval()
    B, T = 1, min(16, cfg.sequence_len)
    x = torch.randint(0, cfg.vocab_size, (B, T))
    with torch.no_grad():
        logits = model(x)
    assert logits.shape == (B, T, cfg.vocab_size), logits.shape
    print("OK: checkpoint loaded, forward pass shape", tuple(logits.shape))
    if "meta" in payload:
        print("meta:", payload["meta"])


if __name__ == "__main__":
    main()
