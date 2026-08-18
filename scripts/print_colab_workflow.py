#!/usr/bin/env python3
"""Colab/local helper: print the Phase-2 training workflow commands."""

from __future__ import annotations


def main() -> None:
    print(
        """
AutoResearch Experiment Platform — training workflow (Colab GPU)

1) Runtime → GPU
2) Clone:
     git clone https://github.com/justSamarthings/autoresearch-platform.git
     cd autoresearch-platform/training
3) Install (Torch already on Colab):
     pip install -r requirements.txt
4) Prepare TinyStories + tokenizer:
     python prepare.py
5) Train (default TIME_BUDGET=300):
     python train.py
   Smoke (short budget):
     AUTORESEARCH_TIME_BUDGET=30 AUTORESEARCH_NO_COMPILE=1 python train.py
6) Verify:
     ls artifacts/checkpoints artifacts/results
     python ../scripts/verify_checkpoint.py artifacts/checkpoints/<experiment_id>.pt

Notebook: scripts/colab_train.ipynb
""".strip()
    )


if __name__ == "__main__":
    main()
