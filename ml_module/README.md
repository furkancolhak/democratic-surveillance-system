# ML Module (2-Class Violence Classification)

This module is prepared for publication-focused 2-class (Normal/Violence) experiments.

## Fixed Protocol

- Task: `normal` vs `violence`
- Seed: `49`
- Split: `70/15/15` (train/val/test)
- Split method: stratified
- SCVD `weaponized` label: excluded from the main experiment

## Directory Structure

```
ml_module/
  configs/
    experiment_config.yaml
  data/
    raw/
      scvd/
      rwf2000/
      real_life_violence/
    processed/
      manifests/
        all_samples.csv
        train.csv
        val.csv
        test.csv
  prepare_data.py
  train.py
  evaluate.py
```

## Dataset Placement Notes

Each source dataset should contain at least the following class folders:
- `normal`
- `violence`

`weaponized` samples in SCVD are automatically excluded in the main protocol.

## Usage

Prepare data:

```bash
python ml_module/prepare_data.py --config ml_module/configs/experiment_config.yaml
```

Start training (scaffold):

```bash
python ml_module/train.py --config ml_module/configs/experiment_config.yaml --model bilstm
```

Run evaluation (scaffold):

```bash
python ml_module/evaluate.py --config ml_module/configs/experiment_config.yaml --split test
```
