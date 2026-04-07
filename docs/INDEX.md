# 📚 Documentation Index

Complete documentation for the Secure Surveillance System.

---

## 📖 Quick Navigation

| Document | Purpose | Audience |
|----------|---------|----------|
| [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) | Complete technical architecture | Developers, Architects |
| [CHANGELOG.md](CHANGELOG.md) | Version history and release notes | All users |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Production deployment instructions | DevOps, Admins |
| [MODEL_DEPLOYMENT_GUIDE.md](MODEL_DEPLOYMENT_GUIDE.md) | ML model setup and configuration | ML Engineers, Developers |
| [NGINX_EXPLAINED.md](NGINX_EXPLAINED.md) | Nginx reverse proxy configuration | DevOps, System Admins |
| [TESTING_GUIDE.md](TESTING_GUIDE.md) | Testing procedures and guidelines | Developers, QA |
| [VIDEO_SOURCE_GUIDE.md](VIDEO_SOURCE_GUIDE.md) | Video source configuration (webcam/RTSP/file) | All users |

---

## 🎯 By Use Case

### Getting Started
1. Read [../README.md](../README.md) - Main project overview
2. Read [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) - Technical architecture
3. Follow Quick Start guide
4. Configure video source: [VIDEO_SOURCE_GUIDE.md](VIDEO_SOURCE_GUIDE.md)
5. Set up ML model: [MODEL_DEPLOYMENT_GUIDE.md](MODEL_DEPLOYMENT_GUIDE.md)

### Development
1. [TESTING_GUIDE.md](TESTING_GUIDE.md) - Run tests
2. [../tests/README.md](../tests/README.md) - Test suite documentation
3. [CHANGELOG.md](CHANGELOG.md) - Track changes

### Deployment
1. [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Production setup
2. [NGINX_EXPLAINED.md](NGINX_EXPLAINED.md) - Configure reverse proxy
3. [MODEL_DEPLOYMENT_GUIDE.md](MODEL_DEPLOYMENT_GUIDE.md) - Deploy ML models

### Troubleshooting
1. Check [../README.md#troubleshooting](../README.md#troubleshooting)
2. Review [TESTING_GUIDE.md](TESTING_GUIDE.md) for diagnostic tests
3. Check [VIDEO_SOURCE_GUIDE.md](VIDEO_SOURCE_GUIDE.md) for camera issues

---

## 📁 File Structure Reference

### Core Application Files

```
app/
├── core/                         # Business logic
│   ├── database.py               # Database models & encryption
│   ├── master_user_manager.py    # Admin management
│   ├── secure_member_auth.py     # Member authentication
│   └── secure_voting_system.py   # Voting & decryption
│
├── api/                          # Web interface
│   └── secure_voting_web.py      # Flask API
│
├── ml/                           # Machine learning
│   ├── model_adapter.py          # Model abstraction
│   ├── model_manager.py          # Model registry
│   ├── secure_webcam_detector.py # Violence detection
│   └── models/                   # ML models
│
├── services/                     # Supporting services
│   ├── notification_service.py   # Email notifications
│   ├── secret_sharing.py         # Shamir Secret Sharing
│   └── video_crypto.py           # Video encryption
│
└── utils/                        # Utilities
    └── video_source.py           # Video source abstraction
```

### Configuration Files

```
config/
├── .env.example                  # Environment template
├── requirements.txt              # Python dependencies
└── nginx.conf                    # Nginx configuration
```

### Deployment Files

```
docker/
├── docker-compose.yml            # Service orchestration
├── Dockerfile                    # Application container
└── init_db.sql                   # Database initialization
```

### Documentation Files

```
docs/
├── INDEX.md                      # This file
├── CHANGELOG.md                  # Version history
├── DEPLOYMENT_GUIDE.md           # Production deployment
├── MODEL_DEPLOYMENT_GUIDE.md     # ML model setup
├── NGINX_EXPLAINED.md            # Nginx configuration
├── TESTING_GUIDE.md              # Testing guide
└── VIDEO_SOURCE_GUIDE.md         # Video source config
```

### Test Files

```
tests/
├── README.md                     # Testing documentation
├── quick_test.py                 # Fast smoke tests
├── test_comprehensive.py         # Unit tests
├── test_with_database.py         # Integration tests
├── run_all_tests.py              # Master test runner
├── run_tests.sh                  # Bash runner
└── run_tests.bat                 # Windows runner
```

### Runtime Directories

```
[Created at runtime]
├── secrets/                      # Master encryption key
├── encrypted_videos/             # Encrypted recordings
├── decrypted_videos/             # Decrypted videos
├── violence_recordings/          # Raw recordings
└── totp_qr_codes/                # 2FA QR codes
```

---

## 🔍 Document Details

### CHANGELOG.md
**Purpose**: Track all changes, updates, and version history  
**When to use**: Before upgrading, to see what's new  
**Maintained by**: Developers

### DEPLOYMENT_GUIDE.md
**Purpose**: Step-by-step production deployment instructions  
**When to use**: Setting up production environment  
**Covers**:
- Server requirements
- Docker deployment
- SSL/TLS configuration
- Security hardening
- Monitoring setup

### MODEL_DEPLOYMENT_GUIDE.md
**Purpose**: ML model setup and configuration  
**When to use**: Adding or updating violence detection models  
**Covers**:
- Model formats (Keras, ONNX, custom)
- Model registry configuration
- Training custom models
- Model performance tuning

### NGINX_EXPLAINED.md
**Purpose**: Nginx reverse proxy configuration  
**When to use**: Setting up HTTPS, load balancing, or custom routing  
**Covers**:
- SSL/TLS setup
- Reverse proxy configuration
- Security headers
- Rate limiting
- WebSocket support

### TESTING_GUIDE.md
**Purpose**: Comprehensive testing procedures  
**When to use**: Running tests, adding new tests, CI/CD setup  
**Covers**:
- Test suite overview
- Running tests
- Writing new tests
- CI/CD integration
- Test coverage

### VIDEO_SOURCE_GUIDE.md
**Purpose**: Video source configuration (webcam, RTSP, file)  
**When to use**: Setting up cameras or changing video input  
**Covers**:
- Webcam configuration
- RTSP/IP camera setup
- Video file testing
- Troubleshooting camera issues
- Multiple camera support (future)

---

## 🔗 External Resources

### Dependencies Documentation
- [PostgreSQL](https://www.postgresql.org/docs/)
- [Flask](https://flask.palletsprojects.com/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)
- [TensorFlow](https://www.tensorflow.org/api_docs)
- [OpenCV](https://docs.opencv.org/)
- [Cryptography](https://cryptography.io/en/latest/)

### Related Technologies
- [Docker](https://docs.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Nginx](https://nginx.org/en/docs/)
- [TOTP/2FA](https://tools.ietf.org/html/rfc6238)
- [Shamir Secret Sharing](https://en.wikipedia.org/wiki/Shamir%27s_Secret_Sharing)

---

## 📝 Documentation Standards

### File Naming
- Use UPPERCASE for main docs (e.g., `README.md`, `CHANGELOG.md`)
- Use descriptive names (e.g., `VIDEO_SOURCE_GUIDE.md`)
- Use underscores for multi-word names

### Content Structure
1. **Title** - Clear, descriptive
2. **Overview** - What this document covers
3. **Table of Contents** - For long documents
4. **Main Content** - Well-organized sections
5. **Examples** - Code snippets, commands
6. **Troubleshooting** - Common issues
7. **References** - Links to related docs

### Markdown Style
- Use headers hierarchically (H1 → H2 → H3)
- Include code blocks with language tags
- Add emojis for visual clarity (sparingly)
- Use tables for structured data
- Include links to related documents

---

## 🔄 Keeping Documentation Updated

### When to Update
- ✅ After adding new features
- ✅ After fixing bugs
- ✅ After changing configuration
- ✅ After updating dependencies
- ✅ After security updates

### What to Update
1. **CHANGELOG.md** - Always update for releases
2. **README.md** - For major feature changes
3. **Specific guides** - For related changes
4. **Code comments** - Keep in sync with docs

### Review Checklist
- [ ] All links work
- [ ] Code examples are tested
- [ ] Commands are correct
- [ ] Screenshots are current (if any)
- [ ] Version numbers are updated
- [ ] No sensitive information exposed

---

## 💡 Tips for Using Documentation

### For New Users
1. Start with [../README.md](../README.md)
2. Follow Quick Start guide
3. Read [VIDEO_SOURCE_GUIDE.md](VIDEO_SOURCE_GUIDE.md)
4. Run tests: [TESTING_GUIDE.md](TESTING_GUIDE.md)

### For Developers
1. Review [TESTING_GUIDE.md](TESTING_GUIDE.md)
2. Check [CHANGELOG.md](CHANGELOG.md) for recent changes
3. Read code comments in `app/` directory
4. Run `python tests/quick_test.py` frequently

### For DevOps
1. Study [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
2. Configure [NGINX_EXPLAINED.md](NGINX_EXPLAINED.md)
3. Set up monitoring and backups
4. Review security checklist in README

### For ML Engineers
1. Read [MODEL_DEPLOYMENT_GUIDE.md](MODEL_DEPLOYMENT_GUIDE.md)
2. Understand model registry format
3. Test models with `model_manager.py`
4. Monitor model performance

---

## 🆘 Getting Help

### Documentation Issues
- Missing information? Open an issue
- Found an error? Submit a PR
- Need clarification? Ask in discussions

### Technical Support
- Check [../README.md#troubleshooting](../README.md#troubleshooting)
- Review relevant guide in this index
- Search closed issues on GitHub
- Contact support team

---

**Last Updated**: 2026-04-08  
**Documentation Version**: 1.0  
**System Version**: See [CHANGELOG.md](CHANGELOG.md)
