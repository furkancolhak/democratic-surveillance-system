# 🔒 Secure Surveillance System

A privacy-focused violence detection system with democratic video access control using Shamir Secret Sharing and multi-party voting.

## 🎯 Overview

This system detects violent incidents via camera feeds, encrypts the recordings, and requires democratic approval from authorized members to decrypt and view the footage. No single person can access the videos alone.

### Key Features

- 🎥 **Modular Video Sources**: Webcam, RTSP/IP cameras, or video files
- 🤖 **AI Violence Detection**: TensorFlow/ONNX model support
- 🔐 **AES-256 Encryption**: Military-grade video encryption
- 🔑 **Shamir Secret Sharing**: Distributed key management (k-of-n threshold)
- 🗳️ **Democratic Voting**: Multi-party approval required for decryption
- 🔒 **2FA Authentication**: TOTP for all users (master & members)
- 📧 **Email Notifications**: Automated incident alerts
- 🗄️ **PostgreSQL Database**: Secure data persistence
- 📊 **Audit Logging**: Complete activity tracking
- 🐳 **Docker Ready**: Containerized deployment

---

## 📁 Project Structure

```
surveillance-system/
├── .env                          # Single configuration file (DO NOT COMMIT)
├── README.md                     # This file
│
├── app/                          # Application code
│   ├── core/                     # Core business logic
│   │   ├── database.py           # Database models & master key encryption
│   │   ├── master_user_manager.py    # Admin user management
│   │   ├── secure_member_auth.py     # Member authentication & key management
│   │   └── secure_voting_system.py   # Voting & decryption logic
│   │
│   ├── api/                      # Web API
│   │   └── secure_voting_web.py  # Flask web interface
│   │
│   ├── ml/                       # Machine Learning
│   │   ├── model_adapter.py      # Model abstraction layer
│   │   ├── model_manager.py      # Model registry & loading
│   │   ├── secure_webcam_detector.py  # Violence detection engine
│   │   └── models/               # ML models directory
│   │       ├── model_registry.json
│   │       └── [model_folders]/
│   │
│   ├── services/                 # Supporting services
│   │   ├── notification_service.py   # Email notifications
│   │   ├── secret_sharing.py         # Shamir Secret Sharing
│   │   └── video_crypto.py           # Video encryption/decryption
│   │
│   └── utils/                    # Utilities
│       └── video_source.py       # Modular video source (webcam/RTSP/file)
│
├── config/                       # Configuration templates
│   ├── .env.example              # Environment variables template
│   ├── requirements.txt          # Python dependencies
│   └── nginx.conf                # Nginx configuration
│
├── docker/                       # Docker deployment
│   ├── docker-compose.yml        # Service orchestration
│   ├── Dockerfile                # Application container
│   └── init_db.sql               # Database initialization
│
├── docs/                         # Documentation
│   ├── CHANGELOG.md              # Version history
│   ├── DEPLOYMENT_GUIDE.md       # Production deployment
│   ├── MODEL_DEPLOYMENT_GUIDE.md # ML model setup
│   ├── NGINX_EXPLAINED.md        # Nginx configuration guide
│   ├── TESTING_GUIDE.md          # Testing documentation
│   └── VIDEO_SOURCE_GUIDE.md     # Video source configuration
│
├── scripts/                      # Utility scripts
│   ├── init_database.py          # Database schema initialization
│   └── setup.sh                  # System setup script
│
├── tests/                        # Test suite
│   ├── quick_test.py             # Fast smoke tests
│   ├── test_comprehensive.py     # Unit tests (no DB required)
│   ├── test_with_database.py     # Integration tests (DB required)
│   ├── run_all_tests.py          # Master test runner
│   ├── run_tests.sh              # Bash test runner
│   ├── run_tests.bat             # Windows test runner
│   └── README.md                 # Testing documentation
│
└── [runtime directories]         # Created at runtime
    ├── secrets/                  # Master encryption key
    ├── encrypted_videos/         # Encrypted incident recordings
    ├── decrypted_videos/         # Decrypted videos (after approval)
    ├── violence_recordings/      # Raw recordings (before encryption)
    └── totp_qr_codes/            # 2FA QR codes
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Docker & Docker Compose
- PostgreSQL 15 (via Docker)
- Webcam or IP camera (optional for testing)

### 1. Clone & Setup

```bash
# Clone repository
git clone <repository-url>
cd surveillance-system

# Copy environment template
cp config/.env.example .env

# Edit .env with your configuration
nano .env
```

### 2. Install Dependencies

```bash
pip install -r config/requirements.txt
```

### 3. Start Database

```bash
# Start PostgreSQL
docker-compose -f docker/docker-compose.yml --env-file .env up -d postgres

# Wait for database to be healthy (10 seconds)
sleep 10

# Initialize database schema
python scripts/init_database.py
```

### 4. Create Master User

```bash
cd app/core
python master_user_manager.py admin admin@example.com SecurePassword123
```

### 5. Run Tests

```bash
# Quick smoke test
python tests/quick_test.py

# Comprehensive tests
python tests/test_comprehensive.py

# All tests (including database)
python tests/run_all_tests.py
```

### 6. Start Application

```bash
# Development mode
cd app/api
python secure_voting_web.py

# Production mode (Docker)
docker-compose -f docker/docker-compose.yml --env-file .env up -d
```

---

## ⚙️ Configuration

### Single .env File

All configuration is managed through a single `.env` file in the project root:

```env
# Database
DB_USER=surveillance_admin
DB_PASSWORD=SecurePass123
DATABASE_URL=postgresql://surveillance_admin:SecurePass123@localhost:5432/surveillance_db

# Email (SMTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com

# Application
BASE_URL=http://localhost:3333
JWT_SECRET=your-random-64-char-secret
JWT_EXPIRE_HOURS=24

# Video Source (webcam, rtsp, or file)
VIDEO_SOURCE_TYPE=webcam
WEBCAM_INDEX=0

# RTSP Camera (if VIDEO_SOURCE_TYPE=rtsp)
RTSP_URL=rtsp://192.168.1.100:554/stream
RTSP_USERNAME=admin
RTSP_PASSWORD=camera_password

# Video File (if VIDEO_SOURCE_TYPE=file)
VIDEO_FILE_PATH=test_videos/sample.mp4
VIDEO_FILE_LOOP=true
```

See `config/.env.example` for full configuration options.

---

## 🎥 Video Source Configuration

The system supports three video source types:

### 1. Webcam (Local Testing)

```env
VIDEO_SOURCE_TYPE=webcam
WEBCAM_INDEX=0
```

### 2. RTSP/IP Camera (Production)

```env
VIDEO_SOURCE_TYPE=rtsp
RTSP_URL=rtsp://192.168.1.100:554/stream
RTSP_USERNAME=admin
RTSP_PASSWORD=camera_password
```

### 3. Video File (Testing/Demo)

```env
VIDEO_SOURCE_TYPE=file
VIDEO_FILE_PATH=test_videos/sample.mp4
VIDEO_FILE_LOOP=true
```

See [docs/VIDEO_SOURCE_GUIDE.md](docs/VIDEO_SOURCE_GUIDE.md) for detailed configuration.

---

## 🤖 ML Model Configuration

### Supported Formats

- TensorFlow/Keras (.keras, .h5)
- ONNX (.onnx)
- Custom models (via adapter pattern)

### Model Registry

Models are registered in `app/ml/models/model_registry.json`:

```json
{
  "models": [
    {
      "id": "violence_detection_v2",
      "name": "Violence Detection v2",
      "version": "2.0",
      "format": "keras",
      "active": true,
      "path": "app/ml/models/violence_detection_v2/model.keras"
    }
  ]
}
```

See [docs/MODEL_DEPLOYMENT_GUIDE.md](docs/MODEL_DEPLOYMENT_GUIDE.md) for details.

---

## 🔐 Security Architecture

### Encryption Flow

1. **Violence Detected** → Video recorded (10 seconds)
2. **AES-256 Encryption** → Video encrypted with random key
3. **Shamir Secret Sharing** → Key split into N shares (threshold K)
4. **RSA Encryption** → Each share encrypted with member's public key
5. **Database Storage** → Encrypted shares stored separately
6. **Secure Deletion** → Original video securely wiped

### Decryption Flow

1. **Email Notification** → Members receive voting link
2. **2FA Authentication** → TOTP verification required
3. **Vote Submission** → Member approves/rejects with signature
4. **Threshold Check** → If K members approve:
   - Shares decrypted with member private keys
   - Encryption key reconstructed via Lagrange interpolation
   - Video decrypted and made available
5. **Audit Logging** → All actions logged immutably

### Key Features

- **No Single Point of Failure**: No one person can decrypt videos
- **Democratic Control**: Requires majority approval
- **Cryptographic Signatures**: All votes are signed and verified
- **Forward Secrecy**: Each video has unique encryption key
- **Audit Trail**: Complete logging of all operations

---

## 🧪 Testing

### Quick Test (5 seconds)

```bash
python tests/quick_test.py
```

Tests: Imports, Environment, Secret Sharing, Video Crypto, Video Source

### Unit Tests (No Database)

```bash
python tests/test_comprehensive.py
```

Tests: 19 unit tests covering all core components

### Integration Tests (Database Required)

```bash
python tests/test_with_database.py
```

Tests: Database, Master User, Member Auth, Voting System

### All Tests

```bash
# Python
python tests/run_all_tests.py

# Bash (Linux/Mac)
bash tests/run_tests.sh

# Windows
tests\run_tests.bat
```

See [tests/README.md](tests/README.md) for detailed testing documentation.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [CHANGELOG.md](docs/CHANGELOG.md) | Version history and changes |
| [DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) | Production deployment instructions |
| [MODEL_DEPLOYMENT_GUIDE.md](docs/MODEL_DEPLOYMENT_GUIDE.md) | ML model setup and configuration |
| [NGINX_EXPLAINED.md](docs/NGINX_EXPLAINED.md) | Nginx reverse proxy configuration |
| [TESTING_GUIDE.md](docs/TESTING_GUIDE.md) | Comprehensive testing guide |
| [VIDEO_SOURCE_GUIDE.md](docs/VIDEO_SOURCE_GUIDE.md) | Video source configuration guide |

---

## 🐳 Docker Deployment

### Start All Services

```bash
docker-compose -f docker/docker-compose.yml --env-file .env up -d
```

### Services

- **postgres**: PostgreSQL database (port 5432)
- **app**: Flask application (port 3333)
- **nginx**: Reverse proxy (ports 80, 443)

### Useful Commands

```bash
# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Stop services
docker-compose -f docker/docker-compose.yml down

# Stop and remove volumes
docker-compose -f docker/docker-compose.yml down -v

# Restart specific service
docker-compose -f docker/docker-compose.yml restart app
```

---

## 🔧 Troubleshooting

### Database Connection Failed

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check database logs
docker-compose -f docker/docker-compose.yml logs postgres

# Verify .env configuration
cat .env | grep DATABASE_URL
```

### Import Errors

```bash
# Ensure all dependencies are installed
pip install -r config/requirements.txt

# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/app"
```

### Video Source Not Opening

```bash
# Test webcam
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'FAIL')"

# Test RTSP stream
ffplay rtsp://username:password@camera-ip:554/stream
```

### Tests Failing

```bash
# Run quick diagnostic
python tests/quick_test.py

# Check specific component
python -c "from app.services.secret_sharing import ShamirSecretSharing; print('OK')"
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add tests for new features
- Update documentation
- Ensure all tests pass before submitting PR

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- TensorFlow team for ML framework
- PostgreSQL team for database
- Cryptography library maintainers
- OpenCV community

---


## ⚠️ Security Notice

This system handles sensitive video data. Always:

- Use strong passwords (16+ characters)
- Enable 2FA for all users
- Keep .env file secure (never commit to git)
- Use HTTPS in production
- Regularly update dependencies
- Monitor audit logs
- Backup database regularly

---

**Built with ❤️ for privacy and security**
