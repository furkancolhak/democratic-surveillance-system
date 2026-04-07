"""
Secure Voting System with Database Backend
Replaces YAML-based voting_system.py
"""

from database import db_manager, VotingSession, MemberShare, Vote, Member
from secure_member_auth import SecureMemberAuth
from video_crypto import VideoCrypto
from secret_sharing import ShamirSecretSharing
from typing import Dict, List, Optional
import uuid
from datetime import datetime
import json


class SecureVotingSystem:
    """Database-backed voting system with encryption"""
    
    def __init__(self):
        self.db = db_manager
        self.member_auth = SecureMemberAuth()
        self.video_crypto = VideoCrypto()
        self.secret_sharing = ShamirSecretSharing()
        self.master_key = db_manager.master_key_manager
    
    def create_voting_session(self, video_path: str, timestamp: str) -> str:
        """
        Create new voting session for detected incident
        
        Args:
            video_path: Path to recorded video
            timestamp: Timestamp string (YYYYMMDD_HHMMSS)
            
        Returns:
            session_id: UUID of created session
        """
        session = self.db.get_session()
        
        try:
            # Get active members
            active_members = session.query(Member).filter(Member.is_active == True).all()
            total_members = len(active_members)
            
            if total_members < 2:
                raise ValueError("Not enough active members (minimum 2 required)")
            
            # Calculate threshold (majority)
            threshold = (total_members // 2) + 1
            
            # Encrypt video
            encrypted_path, encryption_key = self.video_crypto.encrypt_video(video_path)
            print(f"✅ Video encrypted: {encrypted_path}")
            
            # Securely delete original video
            if not self.video_crypto.delete_video(video_path):
                raise Exception("Failed to securely delete original video")
            print(f"✅ Original video deleted: {video_path}")
            
            # Encrypt the encryption key with master key
            encryption_key_encrypted = self.master_key.encrypt(encryption_key)
            
            # Split encryption key using Shamir Secret Sharing
            key_shares = self.secret_sharing.split_secret(
                encryption_key,
                n=total_members,
                k=threshold
            )
            print(f"✅ Key split into {total_members} shares (threshold: {threshold})")
            
            # Create voting session
            session_id_str = f"session_{timestamp}"
            voting_session = VotingSession(
                session_id=session_id_str,
                encrypted_video_path=encrypted_path,
                encryption_key_encrypted=encryption_key_encrypted,
                timestamp=timestamp,
                threshold=threshold,
                total_members=total_members,
                status='active'
            )
            
            session.add(voting_session)
            session.flush()  # Get the ID
            
            # Create member shares
            for (share_index, share_bytes), member in zip(key_shares, active_members):
                # Encrypt share with member's public key
                share_encrypted = self.member_auth.encrypt_for_member(
                    member.id,
                    share_bytes
                )
                
                if not share_encrypted:
                    raise Exception(f"Failed to encrypt share for member {member.email}")
                
                member_share = MemberShare(
                    session_id=voting_session.id,
                    member_id=member.id,
                    share_index=share_index,
                    share_encrypted=share_encrypted
                )
                session.add(member_share)
                print(f"✅ Share {share_index} created for {member.email}")
            
            session.commit()
            
            # Audit log
            self.db.log_audit(
                session=session,
                event_type='voting_session_created',
                user_id=None,
                user_type='system',
                action=f'Voting session created: {session_id_str}',
                details={
                    'timestamp': timestamp,
                    'total_members': total_members,
                    'threshold': threshold
                },
                session_id=voting_session.id
            )
            
            print(f"✅ Voting session created: {session_id_str}")
            return str(voting_session.id)
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error creating voting session: {e}")
            raise
        finally:
            session.close()
    
    def get_session_by_id(self, session_uuid: uuid.UUID) -> Optional[Dict]:
        """Get session by UUID"""
        session = self.db.get_session()
        
        try:
            voting_session = session.query(VotingSession).filter(
                VotingSession.id == session_uuid
            ).first()
            
            if not voting_session:
                return None
            
            return self._session_to_dict(voting_session)
            
        finally:
            session.close()
    
    def get_session_by_session_id(self, session_id: str) -> Optional[Dict]:
        """Get session by session_id string"""
        session = self.db.get_session()
        
        try:
            voting_session = session.query(VotingSession).filter(
                VotingSession.session_id == session_id
            ).first()
            
            if not voting_session:
                return None
            
            return self._session_to_dict(voting_session)
            
        finally:
            session.close()
    
    def _session_to_dict(self, voting_session: VotingSession) -> Dict:
        """Convert VotingSession to dict"""
        return {
            'id': str(voting_session.id),
            'session_id': voting_session.session_id,
            'encrypted_video_path': voting_session.encrypted_video_path,
            'timestamp': voting_session.timestamp,
            'threshold': voting_session.threshold,
            'total_members': voting_session.total_members,
            'status': voting_session.status,
            'decrypted_video_path': voting_session.decrypted_video_path,
            'created_at': voting_session.created_at.isoformat(),
            'expires_at': voting_session.expires_at.isoformat()
        }
    
    def submit_vote(self, session_uuid: uuid.UUID, member_id: uuid.UUID,
                   vote: bool, totp_code: str, ip_address: str = None,
                   user_agent: str = None) -> bool:
        """
        Submit member vote
        
        Args:
            session_uuid: Voting session UUID
            member_id: Member UUID
            vote: True to approve, False to reject
            totp_code: TOTP authentication code
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            True if vote submitted successfully
        """
        session = self.db.get_session()
        
        try:
            # Get voting session
            voting_session = session.query(VotingSession).filter(
                VotingSession.id == session_uuid,
                VotingSession.status == 'active'
            ).first()
            
            if not voting_session:
                print(f"❌ Session not found or not active: {session_uuid}")
                return False
            
            # Check if already voted
            existing_vote = session.query(Vote).filter(
                Vote.session_id == session_uuid,
                Vote.member_id == member_id
            ).first()
            
            if existing_vote:
                print(f"❌ Member already voted: {member_id}")
                return False
            
            # Verify TOTP
            if not self.member_auth.verify_totp(member_id, totp_code):
                print(f"❌ Invalid TOTP code for member: {member_id}")
                
                self.db.log_audit(
                    session=session,
                    event_type='vote_failed',
                    user_id=member_id,
                    user_type='member',
                    action='Vote failed: Invalid TOTP',
                    session_id=session_uuid,
                    ip_address=ip_address,
                    success=False,
                    error_message='Invalid TOTP code'
                )
                return False
            
            print(f"✅ TOTP verified for member: {member_id}")
            
            # Get member's encrypted share
            member_share = session.query(MemberShare).filter(
                MemberShare.session_id == session_uuid,
                MemberShare.member_id == member_id
            ).first()
            
            if not member_share:
                print(f"❌ Member share not found: {member_id}")
                return False
            
            # Decrypt share with member's private key
            share_bytes = self.member_auth.decrypt_for_member(
                member_id,
                member_share.share_encrypted
            )
            
            if not share_bytes:
                print(f"❌ Failed to decrypt share for member: {member_id}")
                return False
            
            # Create vote data for signing
            vote_data = {
                'session_id': str(session_uuid),
                'member_id': str(member_id),
                'vote': vote,
                'timestamp': datetime.utcnow().isoformat()
            }
            vote_json = json.dumps(vote_data, sort_keys=True)
            
            # Sign vote
            signature = self.member_auth.sign_data(member_id, vote_json.encode('utf-8'))
            
            if not signature:
                print(f"❌ Failed to sign vote for member: {member_id}")
                return False
            
            # Store encrypted share only if vote is positive
            share_value_encrypted = None
            if vote:
                # Encrypt share with master key for storage
                share_value_encrypted = self.master_key.encrypt(share_bytes)
            
            # Create vote record
            vote_record = Vote(
                session_id=session_uuid,
                member_id=member_id,
                vote=vote,
                share_value_encrypted=share_value_encrypted,
                signature=signature.hex(),
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            session.add(vote_record)
            session.commit()
            
            print(f"✅ Vote submitted: {member_id} -> {vote}")
            
            # Check threshold
            self._check_threshold(session_uuid)
            
            return True
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error submitting vote: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            session.close()
    
    def _check_threshold(self, session_uuid: uuid.UUID):
        """Check if voting threshold is met and decrypt video if approved"""
        session = self.db.get_session()
        
        try:
            voting_session = session.query(VotingSession).filter(
                VotingSession.id == session_uuid
            ).first()
            
            if not voting_session or voting_session.status != 'active':
                return
            
            # Count votes
            votes = session.query(Vote).filter(Vote.session_id == session_uuid).all()
            total_votes = len(votes)
            positive_votes = sum(1 for v in votes if v.vote)
            
            print(f"\n📊 Threshold check:")
            print(f"   Total votes: {total_votes}")
            print(f"   Positive votes: {positive_votes}")
            print(f"   Threshold: {voting_session.threshold}")
            
            if positive_votes >= voting_session.threshold:
                print("✅ Threshold met! Decrypting video...")
                
                # Collect shares from positive votes
                shares = []
                for vote in votes:
                    if vote.vote and vote.share_value_encrypted:
                        # Decrypt share from storage
                        share_bytes = self.master_key.decrypt(vote.share_value_encrypted)
                        
                        # Get share index
                        member_share = session.query(MemberShare).filter(
                            MemberShare.session_id == session_uuid,
                            MemberShare.member_id == vote.member_id
                        ).first()
                        
                        if member_share:
                            shares.append((member_share.share_index, share_bytes))
                            print(f"   ✅ Share {member_share.share_index} collected")
                
                if len(shares) < voting_session.threshold:
                    print(f"❌ Not enough shares: {len(shares)} < {voting_session.threshold}")
                    voting_session.status = 'error'
                    session.commit()
                    return
                
                # Reconstruct encryption key
                encryption_key = self.secret_sharing.reconstruct_secret(
                    shares,
                    32  # AES-256 key size
                )
                
                if not encryption_key:
                    print("❌ Failed to reconstruct encryption key")
                    voting_session.status = 'error'
                    session.commit()
                    return
                
                print(f"✅ Encryption key reconstructed: {len(encryption_key)} bytes")
                
                # Decrypt video
                try:
                    decrypted_path = self.video_crypto.decrypt_video(
                        voting_session.encrypted_video_path,
                        encryption_key,
                        "decrypted_videos"
                    )
                    
                    voting_session.decrypted_video_path = decrypted_path
                    voting_session.status = 'approved'
                    voting_session.completed_at = datetime.utcnow()
                    
                    session.commit()
                    
                    print(f"✅ Video decrypted: {decrypted_path}")
                    
                    # Audit log
                    self.db.log_audit(
                        session=session,
                        event_type='video_decrypted',
                        user_id=None,
                        user_type='system',
                        action=f'Video decrypted after threshold met',
                        details={
                            'decrypted_path': decrypted_path,
                            'positive_votes': positive_votes,
                            'threshold': voting_session.threshold
                        },
                        session_id=session_uuid
                    )
                    
                except Exception as e:
                    print(f"❌ Error decrypting video: {e}")
                    voting_session.status = 'error'
                    session.commit()
                    
            elif total_votes == voting_session.total_members:
                # All members voted but threshold not met
                print("❌ All members voted, threshold not met")
                voting_session.status = 'rejected'
                voting_session.completed_at = datetime.utcnow()
                session.commit()
                
                # Audit log
                self.db.log_audit(
                    session=session,
                    event_type='session_rejected',
                    user_id=None,
                    user_type='system',
                    action='Voting session rejected',
                    details={
                        'positive_votes': positive_votes,
                        'threshold': voting_session.threshold
                    },
                    session_id=session_uuid
                )
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error checking threshold: {e}")
            import traceback
            traceback.print_exc()
        finally:
            session.close()
    
    def get_session_status(self, session_uuid: uuid.UUID) -> Optional[Dict]:
        """Get current status of voting session"""
        session = self.db.get_session()
        
        try:
            voting_session = session.query(VotingSession).filter(
                VotingSession.id == session_uuid
            ).first()
            
            if not voting_session:
                return None
            
            votes = session.query(Vote).filter(Vote.session_id == session_uuid).all()
            
            return {
                'status': voting_session.status,
                'total_votes': len(votes),
                'positive_votes': sum(1 for v in votes if v.vote),
                'threshold': voting_session.threshold,
                'total_members': voting_session.total_members,
                'decrypted_video_path': voting_session.decrypted_video_path
            }
            
        finally:
            session.close()
