-- Surveillance System Database Schema
-- PostgreSQL 15+

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Master Users Table (Admin kullanıcılar)
CREATE TABLE master_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,  -- Argon2 hash
    totp_secret_encrypted BYTEA NOT NULL,  -- Şifreli TOTP secret
    public_key TEXT NOT NULL,
    private_key_encrypted BYTEA NOT NULL,  -- Şifreli private key
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE
);

-- Members Table (Oylama yapan üyeler)
CREATE TABLE members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    public_key TEXT NOT NULL,
    private_key_encrypted BYTEA NOT NULL,  -- Şifreli private key
    totp_secret_encrypted BYTEA NOT NULL,  -- Şifreli TOTP secret
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES master_users(id),
    deactivated_at TIMESTAMP WITH TIME ZONE,
    deactivated_by UUID REFERENCES master_users(id)
);

-- Voting Sessions Table
CREATE TABLE voting_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(100) UNIQUE NOT NULL,
    encrypted_video_path TEXT NOT NULL,
    encryption_key_encrypted BYTEA NOT NULL,  -- Master key ile şifreli AES key
    timestamp VARCHAR(50) NOT NULL,
    threshold INTEGER NOT NULL,
    total_members INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'approved', 'rejected', 'error', 'expired')),
    decrypted_video_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '48 hours')
);

-- Member Shares Table (Her üyenin share'i)
CREATE TABLE member_shares (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES voting_sessions(id) ON DELETE CASCADE,
    member_id UUID REFERENCES members(id) ON DELETE CASCADE,
    share_index INTEGER NOT NULL,
    share_encrypted BYTEA NOT NULL,  -- Üyenin public key ile şifreli share
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, member_id)
);

-- Votes Table
CREATE TABLE votes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES voting_sessions(id) ON DELETE CASCADE,
    member_id UUID REFERENCES members(id) ON DELETE CASCADE,
    vote BOOLEAN NOT NULL,
    share_value_encrypted BYTEA,  -- Sadece vote=true ise, şifreli share
    signature TEXT NOT NULL,
    voted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    UNIQUE(session_id, member_id)
);

-- Audit Log Table (Tüm önemli işlemler loglanır)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    user_id UUID,  -- master_user veya member
    user_type VARCHAR(20),  -- 'master' veya 'member'
    session_id UUID REFERENCES voting_sessions(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_members_email ON members(email);
CREATE INDEX idx_members_active ON members(is_active);
CREATE INDEX idx_voting_sessions_status ON voting_sessions(status);
CREATE INDEX idx_voting_sessions_expires ON voting_sessions(expires_at);
CREATE INDEX idx_votes_session ON votes(session_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, user_type);

-- Function: Auto-expire sessions
CREATE OR REPLACE FUNCTION expire_old_sessions()
RETURNS void AS $$
BEGIN
    UPDATE voting_sessions
    SET status = 'expired'
    WHERE status = 'active'
    AND expires_at < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Function: Log audit event
CREATE OR REPLACE FUNCTION log_audit_event(
    p_event_type VARCHAR,
    p_user_id UUID,
    p_user_type VARCHAR,
    p_action TEXT,
    p_details JSONB DEFAULT NULL,
    p_session_id UUID DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_log_id UUID;
BEGIN
    INSERT INTO audit_logs (event_type, user_id, user_type, action, details, session_id)
    VALUES (p_event_type, p_user_id, p_user_type, p_action, p_details, p_session_id)
    RETURNING id INTO v_log_id;
    
    RETURN v_log_id;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Log member creation
CREATE OR REPLACE FUNCTION trigger_log_member_creation()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM log_audit_event(
        'member_created',
        NEW.created_by,
        'master',
        'New member registered: ' || NEW.email,
        jsonb_build_object('member_id', NEW.id, 'member_email', NEW.email)
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER member_creation_audit
AFTER INSERT ON members
FOR EACH ROW
EXECUTE FUNCTION trigger_log_member_creation();

-- Trigger: Log vote submission
CREATE OR REPLACE FUNCTION trigger_log_vote()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM log_audit_event(
        'vote_submitted',
        NEW.member_id,
        'member',
        'Vote submitted: ' || CASE WHEN NEW.vote THEN 'APPROVE' ELSE 'REJECT' END,
        jsonb_build_object('vote', NEW.vote),
        NEW.session_id
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER vote_submission_audit
AFTER INSERT ON votes
FOR EACH ROW
EXECUTE FUNCTION trigger_log_vote();

-- Create scheduled job to expire old sessions (requires pg_cron extension)
-- SELECT cron.schedule('expire-sessions', '*/5 * * * *', 'SELECT expire_old_sessions()');

COMMENT ON TABLE master_users IS 'Admin users who can manage members and view system logs';
COMMENT ON TABLE members IS 'Voting members who participate in incident approval';
COMMENT ON TABLE voting_sessions IS 'Video encryption and voting sessions';
COMMENT ON TABLE member_shares IS 'Shamir secret shares for each member';
COMMENT ON TABLE votes IS 'Member votes with digital signatures';
COMMENT ON TABLE audit_logs IS 'Complete audit trail of all system actions';
