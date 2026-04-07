# 🚀 Deployment Guide - Secure Surveillance System

## Quick Start (5 Minutes)

### Prerequisites
```bash
# Check installations
docker --version          # Docker 20.10+
docker-compose --version  # Docker Compose 1.29+
openssl version          # OpenSSL 1.1+
```

### Step 1: Clone & Setup
```bash
git clone <your-repo>
cd surveillance-system
chmod +x setup.sh
./setup.sh
```

### Step 2: Configure Environment
```bash
nano .env
```

**Required changes:**
```env
# Strong database password
DB_PASSWORD=YourStrongPassword123!@#

# Generate with: openssl rand -hex 32
JWT_SECRET=your_64_character_random_string_here

# Gmail SMTP (use app-specific password)
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
FROM_EMAIL=your-email@gmail.com

# Your domain or IP
BASE_URL=https://your-domain.com
```

### Step 3: Start System
```bash
docker-compose up -d
```

### Step 4: Create Master User
```bash
docker-compose exec app python master_user_manager.py admin admin@example.com SecurePass123!
```

**Important:** Scan the QR code immediately!
```bash
# QR code location
cat totp_qr_codes/master/admin_qr.png
```

### Step 5: Access System
```
https://localhost
or
https://your-domain.com
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    Internet                         │
└────────────────────┬────────────────────────────────┘
                     │
                     ↓
         ┌───────────────────────┐
         │   Nginx (Port 443)    │  ← SSL/TLS, Rate Limiting
         │   - HTTPS             │
         │   - Rate Limiting     │
         │   - Security Headers  │
         └───────────┬───────────┘
                     │
                     ↓
         ┌───────────────────────┐
         │  Flask App (Port 3333)│  ← Application Logic
         │  - Gunicorn (4 workers)│
         │  - Master User Auth   │
         │  - Member Management  │
         │  - Voting System      │
         └───────────┬───────────┘
                     │
                     ↓
         ┌───────────────────────┐
         │ PostgreSQL (Port 5432)│  ← Encrypted Database
         │  - Master Key Encrypted│
         │  - Audit Logs         │
         │  - Voting Sessions    │
         └───────────────────────┘
```

---

## Security Features

### 1. Master Key Encryption
```
secrets/master.key (Fernet)
    ↓
    ├─> Private Keys (RSA-2048)
    ├─> TOTP Secrets (Base32)
    ├─> AES Video Keys (256-bit)
    └─> Member Shares (Shamir)
```

**Critical:** Backup `secrets/master.key` immediately!
```bash
cp secrets/master.key /secure/backup/location/
```

### 2. Authentication Layers
- **Master Users:** Username + Password (Argon2) + TOTP
- **Members:** Email + TOTP
- **API:** JWT tokens (24h expiry)
- **Voting:** JWT + TOTP + Digital Signature

### 3. Database Encryption
- Private keys: Encrypted with master key
- TOTP secrets: Encrypted with master key
- Video keys: Encrypted with master key
- Shares: Encrypted with member's public key

### 4. Network Security
- HTTPS only (HTTP redirects to HTTPS)
- Rate limiting (5 login attempts/min)
- Security headers (HSTS, X-Frame-Options, etc.)
- Non-root container user

---

## User Management

### Create Master User
```bash
docker-compose exec app python master_user_manager.py <username> <email> <password>
```

### Master User Login
```python
# API endpoint
POST /api/admin/login
{
  "username": "admin",
  "password": "SecurePass123!",
  "totp_code": "123456"
}
```

### Register Member (Master User Only)
```python
from secure_member_auth import SecureMemberAuth
import uuid

auth = SecureMemberAuth()
master_id = uuid.UUID('your-master-user-id')

result = auth.register_member(
    email='member@example.com',
    name='John Doe',
    created_by_id=master_id
)

print(f"QR Code: {result['qr_path']}")
```

---

## Monitoring & Maintenance

### View Logs
```bash
# Application logs
docker-compose logs -f app

# Database logs
docker-compose logs -f postgres

# Nginx logs
docker-compose logs -f nginx

# All logs
docker-compose logs -f
```

### Check System Status
```bash
# Container status
docker-compose ps

# Resource usage
docker stats

# Database connections
docker-compose exec postgres psql -U $DB_USER -d surveillance_db -c "SELECT count(*) FROM pg_stat_activity;"
```

### Database Backup
```bash
# Manual backup
docker-compose exec postgres pg_dump -U $DB_USER surveillance_db > backup_$(date +%Y%m%d).sql

# Restore
docker-compose exec -T postgres psql -U $DB_USER surveillance_db < backup_20250408.sql
```

### Audit Logs
```sql
-- View recent audit logs
docker-compose exec postgres psql -U $DB_USER -d surveillance_db -c "
SELECT event_type, user_type, action, created_at 
FROM audit_logs 
ORDER BY created_at DESC 
LIMIT 20;
"

-- Failed login attempts
docker-compose exec postgres psql -U $DB_USER -d surveillance_db -c "
SELECT user_id, action, ip_address, created_at 
FROM audit_logs 
WHERE event_type = 'login_failed' 
ORDER BY created_at DESC;
"
```

---

## Troubleshooting

### Database Connection Error
```bash
# Check PostgreSQL status
docker-compose logs postgres

# Verify connection string
echo $DATABASE_URL

# Restart database
docker-compose restart postgres
```

### Master Key Not Found
```bash
# Check if file exists
ls -la secrets/master.key

# If lost, you CANNOT recover encrypted data!
# You must recreate the system
```

### TOTP Code Not Working
```bash
# Check server time (must be synced)
docker-compose exec app date

# Sync time (if needed)
sudo ntpdate pool.ntp.org
```

### SSL Certificate Error
```bash
# For production, use Let's Encrypt
certbot certonly --standalone -d your-domain.com

# Update nginx.conf with real certificates
ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
```

### Container Won't Start
```bash
# Check logs
docker-compose logs app

# Rebuild container
docker-compose build --no-cache app
docker-compose up -d
```

---

## Production Checklist

### Before Going Live

- [ ] Change all default passwords
- [ ] Generate strong JWT_SECRET (`openssl rand -hex 32`)
- [ ] Configure real SMTP credentials
- [ ] Use real SSL certificates (Let's Encrypt)
- [ ] Backup `secrets/master.key` to secure location
- [ ] Set up firewall rules (only 443, 80)
- [ ] Configure log rotation
- [ ] Set up automated database backups
- [ ] Test disaster recovery procedure
- [ ] Document master user credentials (securely)
- [ ] Test TOTP recovery process
- [ ] Configure monitoring/alerting
- [ ] Review audit logs regularly

### Firewall Configuration
```bash
# Ubuntu/Debian
sudo ufw allow 443/tcp
sudo ufw allow 80/tcp
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --reload
```

### Automated Backups
```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * docker-compose exec postgres pg_dump -U $DB_USER surveillance_db > /backups/db_$(date +\%Y\%m\%d).sql

# Weekly master key backup
0 3 * * 0 cp /path/to/secrets/master.key /secure/backup/master.key.$(date +\%Y\%m\%d)
```

---

## Performance Tuning

### Scale Gunicorn Workers
```yaml
# docker-compose.yml
app:
  command: gunicorn -w 8 -b 0.0.0.0:3333 --timeout 120 voting_web:app
  # Rule of thumb: (2 x CPU cores) + 1
```

### PostgreSQL Tuning
```sql
-- Increase connection pool
ALTER SYSTEM SET max_connections = 200;

-- Increase shared buffers (25% of RAM)
ALTER SYSTEM SET shared_buffers = '2GB';

-- Restart PostgreSQL
docker-compose restart postgres
```

### Nginx Caching
```nginx
# Add to nginx.conf
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m;

location /static/ {
    proxy_cache my_cache;
    proxy_cache_valid 200 1h;
}
```

---

## Disaster Recovery

### Scenario 1: Master Key Lost
**Result:** All encrypted data is UNRECOVERABLE
**Action:** 
1. Restore from backup
2. If no backup: Recreate system from scratch

### Scenario 2: Database Corrupted
```bash
# Restore from backup
docker-compose stop postgres
docker-compose exec -T postgres psql -U $DB_USER surveillance_db < backup_latest.sql
docker-compose start postgres
```

### Scenario 3: Master User Locked Out
```bash
# Reset failed login attempts
docker-compose exec postgres psql -U $DB_USER -d surveillance_db -c "
UPDATE master_users 
SET failed_login_attempts = 0, locked_until = NULL 
WHERE username = 'admin';
"
```

---

## Support & Contact

For issues:
1. Check logs: `docker-compose logs -f`
2. Review audit logs in database
3. Check this guide's troubleshooting section
4. Contact: [your-contact-info]

---

**⚠️ CRITICAL REMINDERS:**
- Backup `secrets/master.key` IMMEDIATELY
- Never commit `.env` to git
- Use strong passwords (20+ characters)
- Enable 2FA for all users
- Monitor audit logs regularly
- Test backups monthly
- Keep Docker images updated
