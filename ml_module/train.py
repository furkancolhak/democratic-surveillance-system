#!/usr/bin/env python3
"""
Training entrypoint (config-driven model selection scaffold).
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict

import yaml


def load_config(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def count_rows(csv_path: Path) -> int:
    with csv_path.open("r", encoding="utf-8") as f:
        return max(0, sum(1 for _ in f) - 1)


def main():
    parser = argparse.ArgumentParser(description="Train selected model")
    parser.add_argument("--config", required=True, help="Path to experiment_config.yaml")
    parser.add_argument("--model", choices=["cnn", "lstm", "bilstm"], default=None)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    cfg = load_config(Path(args.config))
    model_name = args.model or cfg["models"]["default"]

    manifests = repo_root / cfg["paths"]["manifests_dir"]
    train_csv = manifests / "train.csv"
    val_csv = manifests / "val.csv"
    test_csv = manifests / "test.csv"

    if not train_csv.exists() or not val_csv.exists() or not test_csv.exists():
        print("[ERROR] Missing manifests. Run prepare_data.py first.")
        return 1

    train_n = count_rows(train_csv)
    val_n = count_rows(val_csv)
    test_n = count_rows(test_csv)

    print("[INFO] Training scaffold initialized")
    print(f"[INFO] Experiment: {cfg['experiment']['name']}")
    print(f"[INFO] Model: {model_name}")
    print(f"[INFO] Seed: {cfg['experiment']['seed']}")
    print(f"[INFO] Train/Val/Test samples: {train_n}/{val_n}/{test_n}")
    print("[TODO] Plug model implementation and training loop here.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
