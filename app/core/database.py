"""
Secure Database Layer with Encryption
PostgreSQL + SQLAlchemy + Master Key Encryption
"""

from sqlalchemy import create_engine, Column, String, Boolean, Integer, DateTime, Text, LargeBinary, ForeignKey, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from datetime import datetime, timedelta
import uuid
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

Base = declarative_base()

class MasterKeyManager:
    """Master key management - Encrypts all sensitive data"""
    
    def __init__(self, master_key_path: str = None):
        self.master_key_path = master_key_path or os.getenv('MASTER_KEY_PATH', 'secrets/master.key')
        self.fernet = self._load_or_create_master_key()
    
    def _load_or_create_master_key(self) -> Fernet:
        """Load or create master key"""
        os.makedirs(os.path.dirname(self.master_key_path), exist_ok=True)
        
        if os.path.exists(self.master_key_path):
            with open(self.master_key_path, 'rb') as f:
                key = f.read()
        else:
            # Create new master key
            key = Fernet.generate_key()
            with open(self.master_key_path, 'wb') as f:
                f.write(key)
            # Restrict file permissions (only owner can read)
            os.chmod(self.master_key_path, 0o400)
            print(f"🔑 New master key created: {self.master_key_path}")
        
        return Fernet(key)
    
    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data"""
        return self.fernet.encrypt(data)
    
    def decrypt(self, encrypted_data: bytes) -> bytes:
        """Decrypt data"""
        return self.fernet.decrypt(encrypted_data)
    
    def encrypt_string(self, text: str) -> bytes:
        """Encrypt string"""
        return self.encrypt(text.encode('utf-8'))
    
    def decrypt_string(self, encrypted_data: bytes) -> str:
        """Decrypt string"""
        return self.decrypt(encrypted_data).decode('utf-8')


class MasterUser(Base):
    """Master/Admin users"""
    __tablename__ = 'master_users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)  # Argon2
    totp_secret_encrypted = Column(LargeBinary, nullable=False)
    public_key = Column(Text, nullable=False)
    private_key_encrypted = Column(LargeBinary, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_login = Column(DateTime(timezone=True))
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    
    # Relationships
    created_members = relationship("Member", foreign_keys="Member.created_by", back_populates="creator")


class Member(Base):
    """Voting members"""
    __tablename__ = 'members'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    public_key = Column(Text, nullable=False)
    private_key_encrypted = Column(LargeBinary, nullable=False)
    totp_secret_encrypted = Column(LargeBinary, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey('master_users.id'))
    deactivated_at = Column(DateTime(timezone=True))
    deactivated_by = Column(UUID(as_uuid=True), ForeignKey('master_users.id'))
    
    # Relationships
    creator = relationship("MasterUser", foreign_keys=[created_by], back_populates="created_members")
    shares = relationship("MemberShare", back_populates="member", cascade="all, delete-orphan")
    votes = relationship("Vote", back_populates="member", cascade="all, delete-orphan")


class VotingSession(Base):
    """Voting sessions"""
    __tablename__ = 'voting_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), unique=True, nullable=False)
    encrypted_video_path = Column(Text, nullable=False)
    encryption_key_encrypted = Column(LargeBinary, nullable=False)  # Encrypted with master key
    timestamp = Column(String(50), nullable=False)
    threshold = Column(Integer, nullable=False)
    total_members = Column(Integer, nullable=False)
    status = Column(String(20), default='active')
    decrypted_video_path = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True), default=lambda: datetime.utcnow() + timedelta(hours=48))
    
    __table_args__ = (
        CheckConstraint("status IN ('active', 'approved', 'rejected', 'error', 'expired')", name='check_status'),
    )
    
    # Relationships
    shares = relationship("MemberShare", back_populates="session", cascade="all, delete-orphan")
    votes = relationship("Vote", back_populates="session", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="session")


class MemberShare(Base):
    """Shamir secret shares"""
    __tablename__ = 'member_shares'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('voting_sessions.id', ondelete='CASCADE'), nullable=False)
    member_id = Column(UUID(as_uuid=True), ForeignKey('members.id', ondelete='CASCADE'), nullable=False)
    share_index = Column(Integer, nullable=False)
    share_encrypted = Column(LargeBinary, nullable=False)  # Encrypted with member's public key
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    session = relationship("VotingSession", back_populates="shares")
    member = relationship("Member", back_populates="shares")


class Vote(Base):
    """Member votes"""
    __tablename__ = 'votes'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('voting_sessions.id', ondelete='CASCADE'), nullable=False)
    member_id = Column(UUID(as_uuid=True), ForeignKey('members.id', ondelete='CASCADE'), nullable=False)
    vote = Column(Boolean, nullable=False)
    share_value_encrypted = Column(LargeBinary)  # Only if vote=true
    signature = Column(Text, nullable=False)
    voted_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    ip_address = Column(INET)
    user_agent = Column(Text)
    
    # Relationships
    session = relationship("VotingSession", back_populates="votes")
    member = relationship("Member", back_populates="votes")


class AuditLog(Base):
    """Audit trail"""
    __tablename__ = 'audit_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50), nullable=False)
    user_id = Column(UUID(as_uuid=True))
    user_type = Column(String(20))  # 'master' or 'member'
    session_id = Column(UUID(as_uuid=True), ForeignKey('voting_sessions.id', ondelete='SET NULL'))
    action = Column(Text, nullable=False)
    details = Column(JSONB)
    ip_address = Column(INET)
    user_agent = Column(Text)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    session = relationship("VotingSession", back_populates="audit_logs")


class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost:5432/surveillance_db')
        self.engine = create_engine(
            self.database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.master_key_manager = MasterKeyManager()
    
    def create_tables(self):
        """Create database tables"""
        Base.metadata.create_all(bind=self.engine)
        print("✅ Database tables created successfully")
    
    def get_session(self):
        """Get new database session"""
        return self.SessionLocal()
    
    def log_audit(self, session, event_type: str, user_id: uuid.UUID, user_type: str, 
                  action: str, details: dict = None, session_id: uuid.UUID = None,
                  ip_address: str = None, user_agent: str = None, success: bool = True,
                  error_message: str = None):
        """Log audit event"""
        try:
            audit_log = AuditLog(
                event_type=event_type,
                user_id=user_id,
                user_type=user_type,
                action=action,
                details=details,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                error_message=error_message
            )
            session.add(audit_log)
            session.commit()
        except Exception as e:
            print(f"❌ Failed to log audit: {e}")
            session.rollback()


# Global instance
db_manager = DatabaseManager()
