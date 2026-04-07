# Test Suite Documentation

Kapsamlı test suite'i - kamera ve ML model olmadan tüm sistemi test eder.

## Test Dosyaları

### 1. `test_comprehensive.py`
**Database gerektirmez** - Temel bileşenleri test eder:
- ✅ Shamir Secret Sharing (anahtar bölme/birleştirme)
- ✅ Video şifreleme/şifre çözme
- ✅ Modüler video kaynak sistemi (webcam, RTSP, file)
- ✅ Entegrasyon testleri

```bash
python tests/test_comprehensive.py
```

### 2. `test_with_database.py`
**Database gerektirir** - Veritabanı entegrasyonunu test eder:
- ✅ Database bağlantısı
- ✅ Master user yönetimi
- ✅ Member authentication
- ✅ Voting system workflow
- ✅ Tam oylama senaryosu

```bash
# Önce database'i başlat
cd docker
docker-compose up -d postgres

# Sonra testi çalıştır
python tests/test_with_database.py
```

### 3. `run_all_tests.py`
**Master test runner** - Tüm testleri çalıştırır ve rapor oluşturur:
- Dependency kontrolü
- Database kontrolü
- Tüm test suite'lerini çalıştırma
- JSON rapor oluşturma

```bash
python tests/run_all_tests.py
```

## Hızlı Başlangıç

### Senaryo 1: Database Yok
Sadece temel bileşenleri test et:

```bash
python tests/test_comprehensive.py
```

### Senaryo 2: Database Var
Tüm sistemi test et:

```bash
# Database başlat
cd docker
docker-compose up -d postgres

# Tüm testleri çalıştır
cd ..
python tests/run_all_tests.py
```

## Test Kapsamı

### Secret Sharing Tests
- ✅ Temel split/reconstruct
- ✅ Threshold ile reconstruct
- ✅ Tüm share'lerle reconstruct
- ✅ Yetersiz share ile başarısızlık
- ✅ Farklı kombinasyonlar
- ✅ Share encoding/decoding

### Video Crypto Tests
- ✅ Key generation
- ✅ Video encryption/decryption
- ✅ Yanlış key ile başarısızlık
- ✅ Güvenli dosya silme

### Video Source Tests
- ✅ Webcam source oluşturma
- ✅ RTSP source oluşturma
- ✅ File source oluşturma
- ✅ Factory pattern
- ✅ Credential handling

### Integration Tests
- ✅ Tam şifreleme workflow
- ✅ Video encrypt → key split → reconstruct → decrypt

### Database Tests (database gerektirir)
- ✅ Database bağlantısı
- ✅ Master user create/login
- ✅ Member registration
- ✅ Member encryption/decryption
- ✅ Voting session creation
- ✅ Tam voting workflow

## Test Çıktısı

### Başarılı Test
```
🧪 Testing: Basic secret sharing...
   ✅ Split secret into 5 shares
   ✅ Reconstructed secret with threshold shares

📊 TEST SUMMARY
Tests run: 25
✅ Passed: 25
❌ Failed: 0
💥 Errors: 0

🎉 ALL TESTS PASSED!
```

### Başarısız Test
```
❌ Failed: test_insufficient_shares
   AssertionError: Shares should not match

⚠️  SOME TESTS FAILED
```

## Gereksinimler

### Minimum (Database yok)
```bash
pip install cryptography pycryptodome
```

### Tam (Database ile)
```bash
pip install -r config/requirements.txt
```

## Sorun Giderme

### Import Errors
```bash
# Path sorunları için
export PYTHONPATH="${PYTHONPATH}:$(pwd)/app"
```

### Database Connection Error
```bash
# Database çalışıyor mu?
docker ps | grep postgres

# Database başlat
cd docker
docker-compose up -d postgres

# Database loglarını kontrol et
docker-compose logs postgres
```

### Module Not Found
```bash
# Tüm dependencies'i yükle
pip install -r config/requirements.txt
```

## CI/CD Entegrasyonu

### GitHub Actions
```yaml
- name: Run Tests
  run: |
    python tests/test_comprehensive.py
    python tests/run_all_tests.py
```

### GitLab CI
```yaml
test:
  script:
    - python tests/test_comprehensive.py
    - python tests/run_all_tests.py
```

## Test Raporu

Test sonuçları `tests/test_report.json` dosyasına kaydedilir:

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "total": 3,
  "passed": 3,
  "failed": 0,
  "results": {
    "Unit Tests": "PASS",
    "Integration Tests": "PASS",
    "System Test": "PASS"
  }
}
```

## Performans

Ortalama test süreleri:
- Unit Tests: ~5 saniye
- Integration Tests: ~30 saniye (database ile)
- Tüm Suite: ~45 saniye

## Katkıda Bulunma

Yeni test eklerken:
1. Test fonksiyonunu yaz
2. Docstring ekle
3. Print mesajları ekle (progress tracking için)
4. `run_all_tests.py`'ye ekle (gerekirse)

## Notlar

- Testler temporary directory kullanır (otomatik temizlenir)
- Database testleri transaction rollback yapar
- Mock'lar gerçek servisleri simüle eder
- Tüm testler izole çalışır (birbirini etkilemez)
