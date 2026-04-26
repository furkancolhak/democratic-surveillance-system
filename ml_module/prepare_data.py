#!/usr/bin/env python3
"""
Prepare 2-class manifests with fixed seed and stratified split.
"""

from __future__ import annotations

import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

import yaml

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".mpeg", ".mpg", ".wmv"}


def load_config(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def normalize_label(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def collect_samples(cfg: Dict, repo_root: Path) -> List[Dict[str, str]]:
    raw_root = repo_root / cfg["paths"]["raw_root"]
    rows: List[Dict[str, str]] = []

    for ds_name, ds_cfg in cfg["datasets"].items():
        if not ds_cfg.get("enabled", False):
            continue

        ds_root = raw_root / ds_cfg["path"]
        if not ds_root.exists():
            print(f"[WARN] Dataset path not found, skipping: {ds_root}")
            continue

        include = {normalize_label(x) for x in ds_cfg.get("include_labels", [])}
        exclude = {normalize_label(x) for x in ds_cfg.get("exclude_labels", [])}

        for class_dir in ds_root.iterdir():
            if not class_dir.is_dir():
                continue

            label = normalize_label(class_dir.name)
            if include and label not in include:
                continue
            if label in exclude:
                continue

            for file_path in class_dir.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in VIDEO_EXTENSIONS:
                    rows.append(
                        {
                            "dataset": ds_name,
                            "label": label,
                            "video_path": str(file_path.resolve()),
                        }
                    )

    return rows


def stratified_split(rows: List[Dict[str, str]], seed: int, train_ratio: float, val_ratio: float):
    rnd = random.Random(seed)
    by_label: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_label[row["label"]].append(row)

    train_rows, val_rows, test_rows = [], [], []

    for label_rows in by_label.values():
        rnd.shuffle(label_rows)
        n = len(label_rows)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)

        train_rows.extend(label_rows[:n_train])
        val_rows.extend(label_rows[n_train : n_train + n_val])
        test_rows.extend(label_rows[n_train + n_val :])

    rnd.shuffle(train_rows)
    rnd.shuffle(val_rows)
    rnd.shuffle(test_rows)
    return train_rows, val_rows, test_rows


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["dataset", "label", "video_path"])
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Prepare dataset manifests")
    parser.add_argument("--config", required=True, help="Path to experiment_config.yaml")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    cfg = load_config(Path(args.config))
    exp = cfg["experiment"]
    split_cfg = cfg["data"]["split"]

    all_rows = collect_samples(cfg, repo_root)
    if not all_rows:
        print("[ERROR] No samples found. Check raw dataset paths and class folder names.")
        return 1

    train_rows, val_rows, test_rows = stratified_split(
        rows=all_rows,
        seed=int(exp["seed"]),
        train_ratio=float(split_cfg["train"]),
        val_ratio=float(split_cfg["val"]),
    )

    manifests_dir = repo_root / cfg["paths"]["manifests_dir"]
    write_csv(manifests_dir / "all_samples.csv", all_rows)
    write_csv(manifests_dir / "train.csv", train_rows)
    write_csv(manifests_dir / "val.csv", val_rows)
    write_csv(manifests_dir / "test.csv", test_rows)

    print(f"[OK] Total samples: {len(all_rows)}")
    print(f"[OK] Train/Val/Test: {len(train_rows)}/{len(val_rows)}/{len(test_rows)}")
    print(f"[OK] Manifests written to: {manifests_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
