# Video Kaynak Konfigürasyon Kılavuzu

Sistem artık modüler video kaynak desteği ile geliyor. Webcam, IP kamera (RTSP), veya video dosyası kullanabilirsiniz.

## Hızlı Başlangıç

`.env` dosyasında `VIDEO_SOURCE_TYPE` değişkenini ayarlayın:

```env
VIDEO_SOURCE_TYPE=webcam    # veya rtsp, file
```

## 1. Webcam (Local Test)

Kendi bilgisayarınızın webcam'i ile test etmek için:

```env
VIDEO_SOURCE_TYPE=webcam
WEBCAM_INDEX=0
```

- `WEBCAM_INDEX=0` → İlk webcam
- `WEBCAM_INDEX=1` → İkinci webcam (varsa)

### Kullanım:
```bash
cd app/ml
python secure_webcam_detector.py
```

## 2. RTSP/IP Kamera (CCTV)

Gerçek güvenlik kamerası entegrasyonu için:

```env
VIDEO_SOURCE_TYPE=rtsp
RTSP_URL=rtsp://192.168.1.100:554/stream
RTSP_USERNAME=admin
RTSP_PASSWORD=camera123
```

### Yaygın RTSP URL Formatları:

#### Hikvision:
```
rtsp://192.168.1.100:554/Streaming/Channels/101
```

#### Dahua:
```
rtsp://192.168.1.100:554/cam/realmonitor?channel=1&subtype=0
```

#### Axis:
```
rtsp://192.168.1.100:554/axis-media/media.amp
```

#### Generic:
```
rtsp://192.168.1.100:554/stream
rtsp://192.168.1.100:554/live
rtsp://192.168.1.100:554/h264
```

### IP Kamera Bağlantı Testi:

```bash
# VLC ile test et
vlc rtsp://admin:password@192.168.1.100:554/stream

# FFmpeg ile test et
ffplay rtsp://admin:password@192.168.1.100:554/stream
```

### Kullanım:
```bash
cd app/ml
python secure_webcam_detector.py
```

## 3. Video Dosyası (Test)

Kayıtlı video ile test etmek için:

```env
VIDEO_SOURCE_TYPE=file
VIDEO_FILE_PATH=test_videos/sample.mp4
VIDEO_FILE_LOOP=true
```

- `VIDEO_FILE_LOOP=true` → Video bitince başa sar
- `VIDEO_FILE_LOOP=false` → Video bitince dur

### Kullanım:
```bash
cd app/ml
python secure_webcam_detector.py
```

## Programatik Kullanım

Python kodunda direkt kullanım:

```python
from utils.video_source import create_video_source
from secure_webcam_detector import violence_detection

# Webcam
source = create_video_source('webcam', camera_index=0)
violence_detection(video_source=source)

# RTSP
source = create_video_source('rtsp', 
                             rtsp_url='rtsp://192.168.1.100:554/stream',
                             username='admin',
                             password='password')
violence_detection(video_source=source)

# File
source = create_video_source('file', 
                             file_path='test.mp4',
                             loop=True)
violence_detection(video_source=source)
```

## Sorun Giderme

### Webcam açılmıyor:
```bash
# Windows'ta kamera kullanımda mı kontrol et
# Başka uygulama (Zoom, Teams) kapatılmalı
```

### RTSP bağlanamıyor:
```bash
# 1. Ping testi
ping 192.168.1.100

# 2. Port açık mı?
telnet 192.168.1.100 554

# 3. Kullanıcı adı/şifre doğru mu?
# 4. Kamera RTSP aktif mi? (kamera ayarlarından kontrol et)
```

### Video dosyası bulunamıyor:
```bash
# Dosya yolu mutlak veya göreceli olabilir
VIDEO_FILE_PATH=/full/path/to/video.mp4
# veya
VIDEO_FILE_PATH=test_videos/sample.mp4
```

## Performans İpuçları

### RTSP için:
- Buffer boyutunu ayarlayın (kod içinde `CAP_PROP_BUFFERSIZE`)
- Düşük latency için substream kullanın
- Ağ bant genişliğini kontrol edin

### Webcam için:
- Çözünürlüğü düşürün (gerekirse)
- FPS'i sınırlayın
- Işık koşullarını optimize edin

### File için:
- Video codec'i H.264 olmalı
- FPS model ile uyumlu olmalı
- Dosya boyutu makul olmalı

## Güvenlik Notları

1. RTSP şifrelerini `.env` dosyasında saklayın
2. `.env` dosyasını `.gitignore`'a ekleyin
3. Production'da güçlü şifreler kullanın
4. Kamera ağını izole edin (VLAN)
5. HTTPS/TLS kullanın (mümkünse RTSPS)

## Çoklu Kamera Desteği

Gelecek versiyonlarda çoklu kamera desteği eklenecek. Şu an tek kamera destekleniyor.

## Örnek Senaryolar

### Senaryo 1: Ofis Testi
```env
VIDEO_SOURCE_TYPE=webcam
WEBCAM_INDEX=0
```

### Senaryo 2: Gerçek Deployment
```env
VIDEO_SOURCE_TYPE=rtsp
RTSP_URL=rtsp://192.168.10.50:554/Streaming/Channels/101
RTSP_USERNAME=surveillance_user
RTSP_PASSWORD=SecurePass123!
```

### Senaryo 3: Demo/Sunum
```env
VIDEO_SOURCE_TYPE=file
VIDEO_FILE_PATH=demo_videos/violence_sample.mp4
VIDEO_FILE_LOOP=true
```
