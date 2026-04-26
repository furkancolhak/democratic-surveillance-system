#!/usr/bin/env python3
"""
Evaluation entrypoint scaffold.
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


def read_labels(csv_path: Path):
    labels = []
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            labels.append(row["label"])
    return labels


def main():
    parser = argparse.ArgumentParser(description="Evaluate trained model")
    parser.add_argument("--config", required=True, help="Path to experiment_config.yaml")
    parser.add_argument("--split", choices=["train", "val", "test"], default="test")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    cfg = load_config(Path(args.config))
    csv_path = repo_root / cfg["paths"]["manifests_dir"] / f"{args.split}.csv"

    if not csv_path.exists():
        print(f"[ERROR] Missing split file: {csv_path}")
        return 1

    labels = read_labels(csv_path)
    total = len(labels)
    normal = sum(1 for x in labels if x == "normal")
    violence = sum(1 for x in labels if x == "violence")

    print("[INFO] Evaluation scaffold initialized")
    print(f"[INFO] Split: {args.split}")
    print(f"[INFO] Total: {total}")
    print(f"[INFO] normal: {normal}, violence: {violence}")
    print("[TODO] Plug model loading, inference, metrics and latency measurement here.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
