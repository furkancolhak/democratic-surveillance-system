# 🏗️ System Overview

Complete technical overview of the Secure Surveillance System architecture, components, and data flow.

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SURVEILLANCE SYSTEM                          │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Video      │      │   Violence   │      │   Incident   │
│   Source     │─────▶│   Detection  │─────▶│   Handler    │
│ (Cam/RTSP)   │      │   (ML Model) │      │              │
└──────────────┘      └──────────────┘      └──────────────┘
                                                     │
                                                     ▼
┌──────────────────────────────────────────────────────────────────┐
│                      ENCRYPTION LAYER                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │  AES-256   │  │   Shamir   │  │    RSA     │                │
│  │  Encrypt   │─▶│   Split    │─▶│  Encrypt   │                │
│  │   Video    │  │    Key     │  │   Shares   │                │
│  └────────────┘  └────────────┘  └────────────┘                │
└──────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                    DATABASE LAYER                                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │ Encrypted  │  │  Encrypted │  │   Voting   │                │
│  │   Video    │  │   Shares   │  │  Sessions  │                │
│  └────────────┘  └────────────┘  └────────────┘                │
└──────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                    NOTIFICATION LAYER                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │   Email    │  │   Voting   │  │    2FA     │                │
│  │   Alert    │─▶│    Link    │─▶│   TOTP     │                │
│  └────────────┘  └────────────┘  └────────────┘                │
└──────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                      VOTING LAYER                                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │  Member    │  │  Threshold │  │  Decrypt   │                │
│  │   Votes    │─▶│   Check    │─▶│   Video    │                │
│  └────────────┘  └────────────┘  └────────────┘                │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Core Components

### 1. Video Source Layer (`app/utils/video_source.py`)

**Purpose**: Abstract video input sources

**Supported Sources**:
- **WebcamSource**: Local USB/built-in cameras
- **RTSPSource**: IP cameras via RTSP protocol
- **FileSource**: Video files for testing

**Key Features**:
- Factory pattern for easy switching
- Automatic FPS detection
- Credential management for RTSP
- Loop support for file sources

**Configuration**: `.env` → `VIDEO_SOURCE_TYPE`

---

### 2. Violence Detection Layer (`app/ml/`)

**Components**:
- `secure_webcam_detector.py` - Main detection loop
- `model_adapter.py` - Model abstraction
- `model_manager.py` - Model registry & loading
- `models/` - ML model storage

**Supported Formats**:
- TensorFlow/Keras (.keras, .h5)
- ONNX (.onnx)
- Custom (via adapter pattern)

**Detection Flow**:
1. Read frame from video source
2. Buffer frames (sequence_length)
3. Preprocess via model adapter
4. Run inference
5. Check threshold
6. Trigger recording if violence detected

**Configuration**: `app/ml/models/model_registry.json`

---

### 3. Encryption Layer (`app/services/`)

#### Video Encryption (`video_crypto.py`)

**Algorithm**: AES-256-CBC  
**Key Generation**: Random 256-bit key per video  
**Metadata**: IV + original filename stored with encrypted data

**Process**:
```python
1. Generate random 256-bit key
2. Generate random 128-bit IV
3. Encrypt video with AES-256-CBC
4. Store: [metadata_length][metadata_json][encrypted_data]
5. Securely delete original
```

#### Secret Sharing (`secret_sharing.py`)

**Algorithm**: Shamir Secret Sharing  
**Prime**: 2^521 - 1 (Mersenne prime)  
**Threshold**: k-of-n (e.g., 3-of-5)

**Process**:
```python
1. Convert 256-bit key to integer
2. Generate polynomial: f(x) = key + a₁x + a₂x² + ... + aₖ₋₁xᵏ⁻¹
3. Evaluate at n points: (1, f(1)), (2, f(2)), ..., (n, f(n))
4. Each point is a share
5. Reconstruction: Lagrange interpolation with k shares
```

#### RSA Encryption (`secure_member_auth.py`)

**Key Size**: 2048-bit RSA  
**Padding**: OAEP with SHA-256  
**Purpose**: Encrypt shares for individual members

**Process**:
```python
1. Generate RSA key pair per member
2. Encrypt private key with master key
3. Store public key in database
4. Encrypt each share with member's public key
5. Member decrypts with their private key
```

---

### 4. Database Layer (`app/core/database.py`)

**Database**: PostgreSQL 15  
**ORM**: SQLAlchemy 2.0  
**Encryption**: Fernet (symmetric) for sensitive data

#### Tables

**master_users**
- Admin users with full system access
- TOTP 2FA required
- RSA key pair for signing
- Argon2 password hashing

**members**
- Voting members
- TOTP 2FA required
- RSA key pair for share encryption
- Created by master users

**voting_sessions**
- One per incident
- Stores encrypted video path
- Threshold and member count
- Status: active, approved, rejected, error

**member_shares**
- One per member per session
- Encrypted share data
- Share index for reconstruction

**votes**
- Member votes (approve/reject)
- Cryptographic signature
- Encrypted share (if approved)
- IP address and user agent

**audit_logs**
- Immutable event log
- All system actions
- User, timestamp, details

#### Master Key

**Purpose**: Encrypt all sensitive data in database  
**Algorithm**: Fernet (AES-128-CBC + HMAC)  
**Storage**: `secrets/master.key` (file system)  
**Permissions**: 0400 (read-only by owner)

**Encrypted Data**:
- Member private keys
- TOTP secrets
- Encryption keys (backup)
- Share values

---

### 5. Authentication Layer (`app/core/`)

#### Master User (`master_user_manager.py`)

**Purpose**: System administrators  
**Authentication**: Username + Password + TOTP  
**Capabilities**:
- Create/manage members
- View audit logs
- System configuration

**Security**:
- Argon2 password hashing
- TOTP 2FA (30-second window)
- Failed login tracking
- Account lockout after 5 attempts

#### Member Auth (`secure_member_auth.py`)

**Purpose**: Voting members  
**Authentication**: Email + TOTP  
**Capabilities**:
- Vote on incidents
- View assigned sessions
- Decrypt approved videos

**Security**:
- RSA key pair per member
- TOTP 2FA (30-second window)
- Cryptographic vote signatures
- No password (email + TOTP only)

---

### 6. Voting Layer (`app/core/secure_voting_system.py`)

#### Voting Process

1. **Session Creation**
   - Encrypt video
   - Split encryption key
   - Encrypt shares for members
   - Store in database
   - Send email notifications

2. **Vote Submission**
   - Verify TOTP
   - Decrypt member's share
   - Sign vote data
   - Store encrypted share (if approved)
   - Check threshold

3. **Threshold Check**
   - Count positive votes
   - If threshold met:
     - Collect approved shares
     - Reconstruct encryption key
     - Decrypt video
     - Update session status
   - If all voted but threshold not met:
     - Mark session as rejected

4. **Audit Logging**
   - Log all actions
   - Immutable records
   - Timestamp + user + details

---

### 7. Notification Layer (`app/services/notification_service.py`)

**Protocol**: SMTP  
**Authentication**: Username + Password (app-specific)  
**Security**: TLS/STARTTLS

#### Email Types

**Incident Notification**
- Sent when violence detected
- Contains voting link with JWT token
- Token expires in 24 hours
- Unique per member

**Result Notification**
- Sent when voting completes
- Approved: Video available
- Rejected: Video remains encrypted

#### JWT Tokens

**Purpose**: Secure voting links  
**Algorithm**: HS256  
**Payload**: session_id, email, expiration  
**Verification**: On vote submission

---

### 8. Web Interface (`app/api/secure_voting_web.py`)

**Framework**: Flask 3.0  
**Port**: 3333  
**Security**: CORS enabled, JWT authentication

#### Endpoints

**Public**:
- `GET /` - Landing page
- `GET /health` - Health check
- `POST /admin/login` - Master user login

**Authenticated**:
- `GET /vote` - Voting page (JWT token)
- `POST /vote` - Submit vote
- `GET /admin/dashboard` - Admin panel
- `POST /admin/members` - Create member

---

## 🔄 Data Flow

### Incident Detection Flow

```
1. Camera → Frame
2. Frame → Detection Model
3. Model → Violence Detected
4. Start Recording (10 seconds)
5. Video → AES-256 Encryption
6. Encryption Key → Shamir Split (k-of-n)
7. Shares → RSA Encrypt (per member)
8. Store: Encrypted Video + Encrypted Shares
9. Delete: Original Video (secure wipe)
10. Send: Email Notifications
```

### Voting Flow

```
1. Member → Click Email Link
2. JWT Token → Verify
3. Member → Enter TOTP Code
4. TOTP → Verify
5. Member → Vote (Approve/Reject)
6. Vote → Cryptographic Signature
7. If Approved:
   - Decrypt Member's Share
   - Encrypt with Master Key
   - Store in Vote Record
8. Check Threshold:
   - If Met → Reconstruct Key → Decrypt Video
   - If Not → Wait for More Votes
9. Update Session Status
10. Log to Audit Trail
```

### Decryption Flow

```
1. Threshold Met (k members approved)
2. Collect k Encrypted Shares
3. Decrypt Shares with Master Key
4. Reconstruct Encryption Key (Lagrange)
5. Decrypt Video with AES-256
6. Save to decrypted_videos/
7. Update Session Status → "approved"
8. Send Result Notifications
9. Log to Audit Trail
```

---

## 🔐 Security Model

### Threat Model

**Protected Against**:
- ✅ Single point of compromise
- ✅ Unauthorized video access
- ✅ Key theft
- ✅ Database breach
- ✅ Man-in-the-middle attacks
- ✅ Replay attacks
- ✅ Brute force attacks

**Assumptions**:
- Master key file is secure
- Email system is trusted
- Members don't collude (< threshold)
- Database server is secure
- Network is encrypted (HTTPS)

### Security Layers

1. **Physical**: Master key file permissions
2. **Network**: HTTPS/TLS encryption
3. **Application**: JWT tokens, TOTP 2FA
4. **Database**: Master key encryption
5. **Cryptographic**: AES-256, RSA-2048, Shamir
6. **Audit**: Immutable logging

---

## 📈 Performance Characteristics

### Detection Performance

- **Frame Rate**: 30 FPS (typical)
- **Latency**: < 100ms per frame
- **Model Inference**: 20-50ms (GPU), 100-200ms (CPU)
- **Recording Buffer**: 10 seconds

### Encryption Performance

- **Video Encryption**: ~1-2 seconds per 10-second video
- **Key Splitting**: < 10ms
- **Share Encryption**: < 50ms per share
- **Total Overhead**: ~2-3 seconds

### Database Performance

- **Session Creation**: < 500ms
- **Vote Submission**: < 200ms
- **Threshold Check**: < 100ms
- **Decryption**: ~1-2 seconds

### Scalability

- **Concurrent Cameras**: 10+ (depends on hardware)
- **Members**: 100+ (tested with 5-10)
- **Sessions**: Unlimited (database limited)
- **Videos**: Disk space limited

---

## 🛠️ Technology Stack

### Backend
- **Language**: Python 3.8+
- **Web Framework**: Flask 3.0
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0

### ML/AI
- **Framework**: TensorFlow 2.13+
- **Alternative**: ONNX Runtime
- **Computer Vision**: OpenCV 4.8+

### Cryptography
- **Library**: cryptography 41.0+
- **Algorithms**: AES-256, RSA-2048, Shamir
- **Hashing**: Argon2, SHA-256

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **Reverse Proxy**: Nginx
- **Process Manager**: Gunicorn

### Frontend
- **Templates**: Jinja2
- **Styling**: Bootstrap 5
- **JavaScript**: Vanilla JS

---

## 📊 System Metrics

### Storage Requirements

- **Database**: ~100MB per 1000 sessions
- **Encrypted Videos**: ~5-10MB per 10-second video
- **Decrypted Videos**: ~5-10MB per video
- **Logs**: ~1MB per 1000 events

### Resource Usage

- **CPU**: 20-40% (with detection)
- **RAM**: 2-4GB (with ML model loaded)
- **Disk I/O**: Moderate (video writes)
- **Network**: Low (email only)

---

## 🔮 Future Enhancements

### Planned Features
- [ ] Multiple camera support
- [ ] Real-time streaming
- [ ] Mobile app
- [ ] Advanced analytics
- [ ] Cloud storage integration
- [ ] Federated learning

### Under Consideration
- [ ] Blockchain audit trail
- [ ] Zero-knowledge proofs
- [ ] Homomorphic encryption
- [ ] Edge computing support

---

**Document Version**: 1.0  
**Last Updated**: 2026-04-08  
**System Version**: See [CHANGELOG.md](CHANGELOG.md)
