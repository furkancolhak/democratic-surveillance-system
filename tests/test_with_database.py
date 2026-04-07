"""
Database Integration Tests
Requires PostgreSQL to be running
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app', 'core'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app', 'services'))

import unittest
import tempfile
import shutil
from datetime import datetime
import uuid

# Import components
try:
    from database import db_manager
    from master_user_manager import MasterUserManager
    from secure_member_auth import SecureMemberAuth
    from secure_voting_system import SecureVotingSystem
    from video_crypto import VideoCrypto
    DATABASE_AVAILABLE = True
except Exception as e:
    print(f"⚠️  Database not available: {e}")
    DATABASE_AVAILABLE = False


@unittest.skipUnless(DATABASE_AVAILABLE, "Database not available")
class TestDatabaseConnection(unittest.TestCase):
    """Test database connectivity"""
    
    def test_database_connection(self):
        """Test basic database connection"""
        print("\n🧪 Testing: Database connection...")
        
        try:
            session = db_manager.get_session()
            result = session.execute('SELECT 1').scalar()
            session.close()
            
            self.assertEqual(result, 1)
            print(f"   ✅ Database connected successfully")
        except Exception as e:
            self.fail(f"Database connection failed: {e}")


@unittest.skipUnless(DATABASE_AVAILABLE, "Database not available")
class TestMasterUserManager(unittest.TestCase):
    """Test master user management"""
    
    def setUp(self):
        self.manager = MasterUserManager()
        self.test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        
    def test_create_master_user(self):
        """Test master user creation"""
        print("\n🧪 Testing: Master user creation...")
        
        result = self.manager.register_master_user(
            email=self.test_email,
            password="TestPassword123!",
            name="Test Master"
        )
        
        self.assertIsNotNone(result)
        self.assertIn('id', result)
        self.assertIn('totp_uri', result)
        print(f"   ✅ Master user created: {result['email']}")
        
    def test_login_master_user(self):
        """Test master user login"""
        print("\n🧪 Testing: Master user login...")
        
        # Create user
        password = "TestPassword123!"
        result = self.manager.register_master_user(
            email=self.test_email,
            password=password,
            name="Test Master"
        )
        
        # Get TOTP code
        import pyotp
        totp_secret = result['totp_uri'].split('secret=')[1].split('&')[0]
        totp = pyotp.TOTP(totp_secret)
        totp_code = totp.now()
        
        # Login
        login_result = self.manager.login(self.test_email, password, totp_code)
        
        self.assertIsNotNone(login_result)
        self.assertIn('token', login_result)
        print(f"   ✅ Master user logged in successfully")


@unittest.skipUnless(DATABASE_AVAILABLE, "Database not available")
class TestMemberAuth(unittest.TestCase):
    """Test member authentication"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.master_manager = MasterUserManager()
        self.member_auth = SecureMemberAuth()
        
        # Create a master user first
        self.master_email = f"master_{uuid.uuid4().hex[:8]}@example.com"
        master_result = self.master_manager.register_master_user(
            email=self.master_email,
            password="MasterPass123!",
            name="Test Master"
        )
        self.master_id = uuid.UUID(master_result['id'])
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_register_member(self):
        """Test member registration"""
        print("\n🧪 Testing: Member registration...")
        
        member_email = f"member_{uuid.uuid4().hex[:8]}@example.com"
        
        result = self.member_auth.register_member(
            email=member_email,
            name="Test Member",
            created_by_id=self.master_id
        )
        
        self.assertIsNotNone(result)
        self.assertIn('id', result)
        self.assertIn('totp_uri', result)
        self.assertIn('qr_path', result)
        print(f"   ✅ Member registered: {result['email']}")
        
    def test_get_active_members(self):
        """Test getting active members"""
        print("\n🧪 Testing: Get active members...")
        
        # Register 3 members
        for i in range(3):
            self.member_auth.register_member(
                email=f"member{i}_{uuid.uuid4().hex[:8]}@example.com",
                name=f"Member {i}",
                created_by_id=self.master_id
            )
        
        members = self.member_auth.get_active_members()
        
        self.assertGreaterEqual(len(members), 3)
        print(f"   ✅ Retrieved {len(members)} active members")
        
    def test_member_encryption(self):
        """Test member encryption/decryption"""
        print("\n🧪 Testing: Member encryption...")
        
        # Register member
        member_email = f"member_{uuid.uuid4().hex[:8]}@example.com"
        result = self.member_auth.register_member(
            email=member_email,
            name="Test Member",
            created_by_id=self.master_id
        )
        member_id = uuid.UUID(result['id'])
        
        # Test data
        test_data = b"Secret message for member"
        
        # Encrypt
        encrypted = self.member_auth.encrypt_for_member(member_id, test_data)
        self.assertIsNotNone(encrypted)
        print(f"   ✅ Data encrypted for member")
        
        # Decrypt
        decrypted = self.member_auth.decrypt_for_member(member_id, encrypted)
        self.assertEqual(test_data, decrypted)
        print(f"   ✅ Data decrypted successfully")


@unittest.skipUnless(DATABASE_AVAILABLE, "Database not available")
class TestVotingSystem(unittest.TestCase):
    """Test voting system"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.master_manager = MasterUserManager()
        self.member_auth = SecureMemberAuth()
        self.voting_system = SecureVotingSystem()
        self.crypto = VideoCrypto(encrypted_dir=self.temp_dir)
        
        # Create master user
        master_result = self.master_manager.register_master_user(
            email=f"master_{uuid.uuid4().hex[:8]}@example.com",
            password="MasterPass123!",
            name="Test Master"
        )
        self.master_id = uuid.UUID(master_result['id'])
        
        # Create 5 members
        self.members = []
        for i in range(5):
            result = self.member_auth.register_member(
                email=f"voter{i}_{uuid.uuid4().hex[:8]}@example.com",
                name=f"Voter {i}",
                created_by_id=self.master_id
            )
            self.members.append({
                'id': uuid.UUID(result['id']),
                'email': result['email'],
                'totp_secret': result['totp_uri'].split('secret=')[1].split('&')[0]
            })
        
        print(f"   ✅ Setup: Created {len(self.members)} members")
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_create_voting_session(self):
        """Test voting session creation"""
        print("\n🧪 Testing: Voting session creation...")
        
        # Create fake video
        video_path = os.path.join(self.temp_dir, "test_incident.mp4")
        with open(video_path, 'wb') as f:
            f.write(b"Test video data" * 1000)
        
        # Create session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = self.voting_system.create_voting_session(video_path, timestamp)
        
        self.assertIsNotNone(session_id)
        print(f"   ✅ Voting session created: {session_id}")
        
        # Verify session
        session_data = self.voting_system.get_session_by_id(uuid.UUID(session_id))
        self.assertIsNotNone(session_data)
        self.assertEqual(session_data['status'], 'active')
        print(f"   ✅ Session verified: {session_data['status']}")
        
    def test_voting_workflow(self):
        """Test complete voting workflow"""
        print("\n🧪 Testing: Complete voting workflow...")
        
        # Create fake video
        video_path = os.path.join(self.temp_dir, "test_incident.mp4")
        video_data = b"Test video data" * 1000
        with open(video_path, 'wb') as f:
            f.write(video_data)
        
        # Create session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_uuid = uuid.UUID(self.voting_system.create_voting_session(video_path, timestamp))
        print(f"   ✅ Session created")
        
        # Get session info
        session_data = self.voting_system.get_session_by_id(session_uuid)
        threshold = session_data['threshold']
        print(f"   ℹ️  Threshold: {threshold}/{len(self.members)}")
        
        # Members vote (threshold members approve)
        import pyotp
        for i in range(threshold):
            member = self.members[i]
            totp = pyotp.TOTP(member['totp_secret'])
            totp_code = totp.now()
            
            result = self.voting_system.submit_vote(
                session_uuid=session_uuid,
                member_id=member['id'],
                vote=True,  # Approve
                totp_code=totp_code,
                ip_address="127.0.0.1"
            )
            
            self.assertTrue(result)
            print(f"   ✅ Vote {i+1}/{threshold} submitted")
        
        # Check status
        status = self.voting_system.get_session_status(session_uuid)
        print(f"   ℹ️  Status: {status['status']}")
        print(f"   ℹ️  Votes: {status['positive_votes']}/{status['total_votes']}")
        
        # Should be approved
        self.assertEqual(status['status'], 'approved')
        self.assertIsNotNone(status['decrypted_video_path'])
        print(f"   ✅ Video decrypted: {status['decrypted_video_path']}")
        
        # Verify decrypted video
        with open(status['decrypted_video_path'], 'rb') as f:
            decrypted_data = f.read()
        
        self.assertEqual(video_data, decrypted_data)
        print(f"   ✅ Decrypted video matches original")


def run_database_tests():
    """Run database tests"""
    print("=" * 70)
    print("🔬 DATABASE INTEGRATION TESTS")
    print("=" * 70)
    
    if not DATABASE_AVAILABLE:
        print("\n❌ Database not available. Please ensure PostgreSQL is running.")
        print("   Run: docker-compose up -d postgres")
        return 1
    
    print("\n✅ Database available. Running tests...")
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseConnection))
    suite.addTests(loader.loadTestsFromTestCase(TestMasterUserManager))
    suite.addTests(loader.loadTestsFromTestCase(TestMemberAuth))
    suite.addTests(loader.loadTestsFromTestCase(TestVotingSystem))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failed: {len(result.failures)}")
    print(f"💥 Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL DATABASE TESTS PASSED!")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    exit_code = run_database_tests()
    sys.exit(exit_code)
