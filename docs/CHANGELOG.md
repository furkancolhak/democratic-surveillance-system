# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2025-04-08

### 🎉 Major Release - Complete System Overhaul

### Added
- **PostgreSQL Database** - Replaced YAML files with encrypted database
- **Master Key Encryption** - Fernet encryption for all sensitive data
- **Nginx Reverse Proxy** - SSL/TLS, rate limiting, security headers
- **Docker Containerization** - Multi-container orchestration
- **Master User System** - Admin-only member registration
- **Complete Audit Logging** - All actions tracked in database
- **Model Adapter System** - Support for multiple model formats
- **Flexible Preprocessing** - Config-based and custom Python preprocessing
- **Model Management CLI** - Easy model deployment and switching
- **Comprehensive Documentation** - English documentation suite

### Changed
- **Authentication** - Argon2 password hashing (was plain text)
- **TOTP Storage** - Encrypted in database (was plain text in YAML)
- **Private Keys** - Encrypted with master key (was Base64 only)
- **Web Server** - Gunicorn production server (was Flask dev server)
- **Video Encryption** - Keys encrypted with master key
- **Member Registration** - Requires master user authentication

### Removed
- **YAML Files** - Replaced by PostgreSQL database
- **Plain Text Secrets** - All secrets now encrypted
- **Development Server** - Replaced by Gunicorn + Nginx
- **Hardcoded Model** - Replaced by flexible model adapter
- **Turkish Documentation** - Replaced by English docs

### Security
- ✅ SSL/TLS encryption (HTTPS)
- ✅ Rate limiting (5 login attempts/min)
- ✅ Master key encryption (Fernet)
- ✅ Argon2 password hashing
- ✅ 2FA mandatory (TOTP)
- ✅ Security headers (HSTS, X-Frame-Options, etc.)
- ✅ Non-root container user
- ✅ Audit trail for all actions

### Documentation
- `README.md` - Main documentation
- `FINAL_GUIDE.md` - Complete setup guide
- `README_SECURE.md` - Detailed system documentation
- `NGINX_EXPLAINED.md` - Why Nginx is essential
- `DEPLOYMENT_GUIDE.md` - Production deployment
- `MODEL_DEPLOYMENT_GUIDE.md` - Model management guide
- `SUMMARY.md` - Quick overview
- `SYSTEM_READY.md` - Final status report

### Files Added
- `database.py` - Database models and master key manager
- `master_user_manager.py` - Master user management
- `secure_member_auth.py` - Secure member authentication
- `secure_voting_system.py` - Database-backed voting
- `secure_voting_web.py` - Secure web interface
- `secure_webcam_detector.py` - Updated detector
- `model_adapter.py` - Universal model adapter
- `model_manager.py` - Model management CLI
- `init_database.py` - Database initialization
- `test_system.py` - System tests
- `init_db.sql` - PostgreSQL schema
- `docker-compose.yml` - Container orchestration
- `Dockerfile` - Container definition
- `nginx.conf` - Reverse proxy configuration
- `setup.sh` - Automated setup script

### Files Removed
- `member_auth.py` - Replaced by `secure_member_auth.py`
- `voting_system.py` - Replaced by `secure_voting_system.py`
- `voting_web.py` - Replaced by `secure_voting_web.py`
- `webcam_violence_detector.py` - Replaced by `secure_webcam_detector.py`
- `create_initial_members.py` - Replaced by master user system
- `register_members.py` - Replaced by master user system
- `test_setup.py` - Replaced by `test_system.py`
- `test_crypto.py` - Replaced by `test_system.py`
- `instructions.md` - Not relevant
- `SISTEM_DOKUMANTASYONU.md` - Replaced by English docs
- `member_data/` - Replaced by database
- `voting_data/` - Replaced by database

---

## [1.0.0] - 2024-01-15

### Initial Release
- Basic violence detection with TensorFlow
- YAML-based data storage
- Simple member authentication
- Video encryption with AES-256
- Shamir Secret Sharing
- Email notifications
- Basic voting system

---

## Migration Guide (1.0 → 2.0)

### Breaking Changes
1. **Data Storage** - YAML → PostgreSQL (data migration required)
2. **Authentication** - New master user system
3. **Configuration** - New `.env` format
4. **Deployment** - Docker required

### Migration Steps
1. Backup all YAML files
2. Run `./setup.sh`
3. Configure `.env`
4. Create master user
5. Re-register all members
6. Test system

### Not Backward Compatible
- Old YAML files cannot be used directly
- Member credentials must be re-registered
- QR codes must be regenerated

---

## Roadmap

### v2.1.0 (Planned)
- [ ] Web admin dashboard
- [ ] Real-time monitoring
- [ ] Advanced analytics
- [ ] Multi-camera support
- [ ] Cloud storage integration

### v2.2.0 (Planned)
- [ ] Mobile app for voting
- [ ] Push notifications
- [ ] Video streaming
- [ ] Advanced model ensemble
- [ ] Auto-scaling support

### v3.0.0 (Future)
- [ ] Kubernetes deployment
- [ ] Microservices architecture
- [ ] GraphQL API
- [ ] Machine learning pipeline
- [ ] Edge computing support

---

## Support

For questions or issues:
- Check documentation in `docs/` directory
- Run tests: `docker-compose exec app python test_system.py`
- View logs: `docker-compose logs -f`
- Open an issue on GitHub

---

**Maintained by:** Surveillance Team
**License:** [Your License]
**Status:** ✅ Production Ready
