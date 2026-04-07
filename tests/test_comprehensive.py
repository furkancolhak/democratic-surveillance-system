"""
Comprehensive System Test Suite
Tests all components without requiring camera or ML model
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app', 'core'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app', 'services'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app', 'ml'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app', 'utils'))

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil
from datetime import datetime
import uuid
import json

# Import components to test
from secret_sharing import ShamirSecretSharing
from video_crypto import VideoCrypto
from video_source import WebcamSource, RTSPSource, FileSource, create_video_source


class TestSecretSharing(unittest.TestCase):
    """Test Shamir Secret Sharing implementation"""
    
    def setUp(self):
        self.sss = ShamirSecretSharing()
        
    def test_split_and_reconstruct_basic(self):
        """Test basic split and reconstruct"""
        print("\n🧪 Testing: Basic secret sharing...")
        
        # Generate a 32-byte secret (AES-256 key)
        secret = os.urandom(32)
        
        # Split into 5 shares, threshold 3
        shares = self.sss.split_secret(secret, n=5, k=3)
        
        self.assertEqual(len(shares), 5)
        print(f"   ✅ Split secret into {len(shares)} shares")
        
        # Reconstruct with exactly threshold shares
        reconstructed = self.sss.reconstruct_secret(shares[:3], 32)
        
        self.assertEqual(secret, reconstructed)
        print(f"   ✅ Reconstructed secret with threshold shares")
        
    def test_reconstruct_with_more_shares(self):
        """Test reconstruction with more than threshold shares"""
        print("\n🧪 Testing: Reconstruction with extra shares...")
        
        secret = os.urandom(32)
        shares = self.sss.split_secret(secret, n=5, k=3)
        
        # Reconstruct with 4 shares
        reconstructed = self.sss.reconstruct_secret(shares[:4], 32)
        
        self.assertEqual(secret, reconstructed)
        print(f"   ✅ Reconstructed with 4 shares (threshold: 3)")
        
    def test_reconstruct_with_all_shares(self):
        """Test reconstruction with all shares"""
        print("\n🧪 Testing: Reconstruction with all shares...")
        
        secret = os.urandom(32)
        shares = self.sss.split_secret(secret, n=5, k=3)
        
        # Reconstruct with all 5 shares
        reconstructed = self.sss.reconstruct_secret(shares, 32)
        
        self.assertEqual(secret, reconstructed)
        print(f"   ✅ Reconstructed with all 5 shares")
        
    def test_insufficient_shares(self):
        """Test that reconstruction fails with insufficient shares"""
        print("\n🧪 Testing: Insufficient shares...")
        
        secret = os.urandom(32)
        shares = self.sss.split_secret(secret, n=5, k=3)
        
        # Try with only 2 shares (threshold is 3)
        reconstructed = self.sss.reconstruct_secret(shares[:2], 32)
        
        # Should not match original secret
        self.assertNotEqual(secret, reconstructed)
        print(f"   ✅ Correctly failed with insufficient shares")
        
    def test_different_share_combinations(self):
        """Test that different combinations of shares work"""
        print("\n🧪 Testing: Different share combinations...")
        
        secret = os.urandom(32)
        shares = self.sss.split_secret(secret, n=5, k=3)
        
        # Test different combinations
        combinations = [
            shares[0:3],  # First 3
            shares[1:4],  # Middle 3
            shares[2:5],  # Last 3
            [shares[0], shares[2], shares[4]],  # Non-consecutive
        ]
        
        for i, combo in enumerate(combinations):
            reconstructed = self.sss.reconstruct_secret(combo, 32)
            self.assertEqual(secret, reconstructed)
            print(f"   ✅ Combination {i+1} successful")
            
    def test_encode_decode_share(self):
        """Test share encoding and decoding"""
        print("\n🧪 Testing: Share encoding/decoding...")
        
        secret = os.urandom(32)
        shares = self.sss.split_secret(secret, n=3, k=2)
        
        # Encode and decode
        encoded = self.sss.encode_share(shares[0])
        decoded = self.sss.decode_share(encoded)
        
        self.assertEqual(shares[0], decoded)
        print(f"   ✅ Share encoding/decoding successful")


class TestVideoCrypto(unittest.TestCase):
    """Test video encryption and decryption"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.crypto = VideoCrypto(encrypted_dir=self.temp_dir)
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_key_generation(self):
        """Test encryption key generation"""
        print("\n🧪 Testing: Key generation...")
        
        key = self.crypto.generate_key()
        
        self.assertEqual(len(key), 32)  # 256 bits
        print(f"   ✅ Generated 256-bit key")
        
    def test_encrypt_decrypt_video(self):
        """Test video encryption and decryption"""
        print("\n🧪 Testing: Video encryption/decryption...")
        
        # Create a fake video file
        test_video_path = os.path.join(self.temp_dir, "test_video.mp4")
        test_data = b"This is fake video data" * 1000
        
        with open(test_video_path, 'wb') as f:
            f.write(test_data)
        
        # Encrypt
        encrypted_path, key = self.crypto.encrypt_video(test_video_path)
        
        self.assertTrue(os.path.exists(encrypted_path))
        print(f"   ✅ Video encrypted: {os.path.basename(encrypted_path)}")
        
        # Decrypt
        decrypted_dir = os.path.join(self.temp_dir, "decrypted")
        decrypted_path = self.crypto.decrypt_video(encrypted_path, key, decrypted_dir)
        
        self.assertTrue(os.path.exists(decrypted_path))
        print(f"   ✅ Video decrypted: {os.path.basename(decrypted_path)}")
        
        # Verify content
        with open(decrypted_path, 'rb') as f:
            decrypted_data = f.read()
        
        self.assertEqual(test_data, decrypted_data)
        print(f"   ✅ Decrypted content matches original")
        
    def test_wrong_key_fails(self):
        """Test that decryption fails with wrong key"""
        print("\n🧪 Testing: Wrong key decryption...")
        
        # Create and encrypt video
        test_video_path = os.path.join(self.temp_dir, "test_video.mp4")
        with open(test_video_path, 'wb') as f:
            f.write(b"Test data" * 100)
        
        encrypted_path, correct_key = self.crypto.encrypt_video(test_video_path)
        
        # Try to decrypt with wrong key
        wrong_key = os.urandom(32)
        
        with self.assertRaises(Exception):
            self.crypto.decrypt_video(encrypted_path, wrong_key, self.temp_dir)
        
        print(f"   ✅ Correctly failed with wrong key")
        
    def test_secure_delete(self):
        """Test secure file deletion"""
        print("\n🧪 Testing: Secure file deletion...")
        
        # Create test file
        test_file = os.path.join(self.temp_dir, "to_delete.txt")
        with open(test_file, 'wb') as f:
            f.write(b"Sensitive data")
        
        # Delete
        result = self.crypto.delete_video(test_file)
        
        self.assertTrue(result)
        self.assertFalse(os.path.exists(test_file))
        print(f"   ✅ File securely deleted")


class TestVideoSource(unittest.TestCase):
    """Test modular video source system"""
    
    def test_webcam_source_creation(self):
        """Test webcam source creation"""
        print("\n🧪 Testing: Webcam source creation...")
        
        source = WebcamSource(camera_index=0)
        
        self.assertEqual(source.camera_index, 0)
        self.assertFalse(source.is_opened)
        print(f"   ✅ Webcam source created: {source}")
        
    def test_rtsp_source_creation(self):
        """Test RTSP source creation"""
        print("\n🧪 Testing: RTSP source creation...")
        
        source = RTSPSource(
            rtsp_url="rtsp://192.168.1.100:554/stream",
            username="admin",
            password="password"
        )
        
        self.assertIn("admin:password", source.rtsp_url)
        print(f"   ✅ RTSP source created")
        
    def test_rtsp_url_without_credentials(self):
        """Test RTSP URL without credentials"""
        print("\n🧪 Testing: RTSP without credentials...")
        
        source = RTSPSource(rtsp_url="rtsp://192.168.1.100:554/stream")
        
        self.assertEqual(source.rtsp_url, "rtsp://192.168.1.100:554/stream")
        print(f"   ✅ RTSP source created without credentials")
        
    def test_file_source_creation(self):
        """Test file source creation"""
        print("\n🧪 Testing: File source creation...")
        
        source = FileSource(file_path="test.mp4", loop=True)
        
        self.assertEqual(source.file_path, "test.mp4")
        self.assertTrue(source.loop)
        print(f"   ✅ File source created: {source}")
        
    def test_factory_webcam(self):
        """Test factory function for webcam"""
        print("\n🧪 Testing: Factory - webcam...")
        
        source = create_video_source('webcam', camera_index=1)
        
        self.assertIsInstance(source, WebcamSource)
        self.assertEqual(source.camera_index, 1)
        print(f"   ✅ Factory created webcam source")
        
    def test_factory_rtsp(self):
        """Test factory function for RTSP"""
        print("\n🧪 Testing: Factory - RTSP...")
        
        source = create_video_source(
            'rtsp',
            rtsp_url='rtsp://camera.local/stream',
            username='user',
            password='pass'
        )
        
        self.assertIsInstance(source, RTSPSource)
        print(f"   ✅ Factory created RTSP source")
        
    def test_factory_file(self):
        """Test factory function for file"""
        print("\n🧪 Testing: Factory - file...")
        
        source = create_video_source('file', file_path='video.mp4', loop=False)
        
        self.assertIsInstance(source, FileSource)
        self.assertFalse(source.loop)
        print(f"   ✅ Factory created file source")
        
    def test_factory_invalid_type(self):
        """Test factory with invalid type"""
        print("\n🧪 Testing: Factory - invalid type...")
        
        with self.assertRaises(ValueError):
            create_video_source('invalid_type')
        
        print(f"   ✅ Factory correctly rejected invalid type")


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple components"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_full_encryption_workflow(self):
        """Test complete encryption workflow with secret sharing"""
        print("\n🧪 Testing: Full encryption workflow...")
        
        # Create fake video
        video_path = os.path.join(self.temp_dir, "incident.mp4")
        video_data = b"Incident video data" * 1000
        with open(video_path, 'wb') as f:
            f.write(video_data)
        
        # Encrypt video
        crypto = VideoCrypto(encrypted_dir=self.temp_dir)
        encrypted_path, encryption_key = crypto.encrypt_video(video_path)
        print(f"   ✅ Video encrypted")
        
        # Split encryption key
        sss = ShamirSecretSharing()
        shares = sss.split_secret(encryption_key, n=5, k=3)
        print(f"   ✅ Key split into 5 shares (threshold: 3)")
        
        # Simulate voting: 3 members approve
        approved_shares = shares[:3]
        
        # Reconstruct key
        reconstructed_key = sss.reconstruct_secret(approved_shares, 32)
        print(f"   ✅ Key reconstructed from votes")
        
        # Decrypt video
        decrypted_dir = os.path.join(self.temp_dir, "decrypted")
        decrypted_path = crypto.decrypt_video(encrypted_path, reconstructed_key, decrypted_dir)
        print(f"   ✅ Video decrypted")
        
        # Verify
        with open(decrypted_path, 'rb') as f:
            decrypted_data = f.read()
        
        self.assertEqual(video_data, decrypted_data)
        print(f"   ✅ Full workflow successful!")


class TestDatabaseMock(unittest.TestCase):
    """Test database-dependent components with mocks"""
    
    @unittest.skip("Requires database - use test_with_database.py instead")
    def test_voting_system_mock(self):
        """Test voting system with mocked database"""
        print("\n🧪 Testing: Voting system (mocked)...")
        print(f"   ⚠️  Skipped: Requires database connection")
        
    @unittest.skip("Requires database - use test_with_database.py instead")
    def test_member_auth_mock(self):
        """Test member auth with mocked database"""
        print("\n🧪 Testing: Member auth (mocked)...")
        print(f"   ⚠️  Skipped: Requires database connection")


def run_tests():
    """Run all tests with detailed output"""
    print("=" * 70)
    print("🔬 COMPREHENSIVE SYSTEM TEST SUITE")
    print("=" * 70)
    print("\nTesting all components without camera or ML model...")
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSecretSharing))
    suite.addTests(loader.loadTestsFromTestCase(TestVideoCrypto))
    suite.addTests(loader.loadTestsFromTestCase(TestVideoSource))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseMock))
    
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
    print(f"⏭️  Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
