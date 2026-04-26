#!/usr/bin/env python3
"""
Create a clean 2-class SCVD view for training:
- source: SCVD/SCVD_converted_sec_split/{Train,Test}/{Normal,Violence,Weaponized}
- target: ml_module/data/raw/scvd/{normal,violence}

Weaponized is excluded by design.
"""

from __future__ import annotations

import shutil
from pathlib import Path

VIDEO_EXTS = {".avi", ".mp4", ".mov", ".mkv", ".mpeg", ".mpg", ".wmv"}


def copy_class(src_root: Path, split: str, class_name: str, dst_dir: Path) -> int:
    src_dir = src_root / split / class_name
    if not src_dir.exists():
        return 0

    copied = 0
    prefix = f"{split.lower()}_{class_name.lower()}_"
    for idx, file_path in enumerate(sorted(src_dir.iterdir())):
        if not file_path.is_file() or file_path.suffix.lower() not in VIDEO_EXTS:
            continue
        target_name = f"{prefix}{idx:05d}{file_path.suffix.lower()}"
        shutil.copy2(file_path, dst_dir / target_name)
        copied += 1
    return copied


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    src_root = repo_root / "SCVD" / "SCVD_converted_sec_split"
    dst_root = repo_root / "ml_module" / "data" / "raw" / "scvd"
    normal_dst = dst_root / "normal"
    violence_dst = dst_root / "violence"

    if not src_root.exists():
        print(f"[ERROR] Source directory not found: {src_root}")
        return 1

    normal_dst.mkdir(parents=True, exist_ok=True)
    violence_dst.mkdir(parents=True, exist_ok=True)

    # Clean previous copies for idempotent runs.
    for folder in (normal_dst, violence_dst):
        for file_path in folder.glob("*"):
            if file_path.is_file():
                file_path.unlink()

    normal_count = 0
    violence_count = 0
    for split in ("Train", "Test"):
        normal_count += copy_class(src_root, split, "Normal", normal_dst)
        violence_count += copy_class(src_root, split, "Violence", violence_dst)

    weaponized_train = len(list((src_root / "Train" / "Weaponized").glob("*.avi")))
    weaponized_test = len(list((src_root / "Test" / "Weaponized").glob("*.avi")))

    print("[OK] SCVD binary preparation complete")
    print(f"[OK] normal clips copied: {normal_count}")
    print(f"[OK] violence clips copied: {violence_count}")
    print(
        "[INFO] weaponized clips excluded: "
        f"{weaponized_train + weaponized_test} "
        f"(Train={weaponized_train}, Test={weaponized_test})"
    )
    print(f"[OK] Output directory: {dst_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
