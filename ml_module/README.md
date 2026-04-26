# ML Module (2-Class Violence Classification)

Bu modül, publication odaklı 2-class (Normal/Violence) deney akışı için hazırlanmıştır.

## Sabit Protokol

- Task: `normal` vs `violence`
- Seed: `49`
- Split: `70/15/15` (train/val/test)
- Split yöntemi: stratified
- SCVD `weaponized` etiketi: ana deney dışında

## Klasör Yapısı

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

## Dataset Yerleştirme Notu

Her kaynak dataset için klasör yapısı en azından şu etiketleri içermelidir:
- `normal`
- `violence`

SCVD içindeki `weaponized` örnekler ana protokol kapsamında otomatik dışlanır.

## Çalıştırma

Veriyi hazırlama:

```bash
python ml_module/prepare_data.py --config ml_module/configs/experiment_config.yaml
```

Eğitim başlatma (iskelet):

```bash
python ml_module/train.py --config ml_module/configs/experiment_config.yaml --model bilstm
```

Değerlendirme (iskelet):

```bash
python ml_module/evaluate.py --config ml_module/configs/experiment_config.yaml --split test
```
