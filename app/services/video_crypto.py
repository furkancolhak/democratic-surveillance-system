from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import os
import json
from base64 import b64encode, b64decode
from typing import Tuple, Dict

class VideoCrypto:
    def __init__(self, encrypted_dir: str = "encrypted_videos"):
        self.encrypted_dir = encrypted_dir
        if not os.path.exists(encrypted_dir):
            os.makedirs(encrypted_dir)

    def generate_key(self) -> bytes:
        """Generate a random 256-bit key for AES encryption"""
        return get_random_bytes(32)

    def encrypt_video(self, video_path: str) -> Tuple[str, bytes]:
        """
        Encrypt a video file using AES-256-CBC
        Returns: (encrypted_video_path, encryption_key)
        """
        # Generate a random key and IV
        key = self.generate_key()
        iv = get_random_bytes(16)
        
        # Create cipher
        cipher = AES.new(key, AES.MODE_CBC, iv)
        
        # Read video file
        with open(video_path, 'rb') as f:
            video_data = f.read()
        
        # Pad and encrypt
        padded_data = pad(video_data, AES.block_size)
        encrypted_data = cipher.encrypt(padded_data)
        
        # Create metadata
        metadata = {
            'iv': b64encode(iv).decode('utf-8'),
            'original_filename': os.path.basename(video_path)
        }
        
        # Generate encrypted filename
        encrypted_filename = f"encrypted_{os.path.basename(video_path)}"
        encrypted_path = os.path.join(self.encrypted_dir, encrypted_filename)
        
        # Save encrypted video and metadata
        with open(encrypted_path, 'wb') as f:
            # Write metadata length as 4 bytes
            metadata_bytes = json.dumps(metadata).encode('utf-8')
            f.write(len(metadata_bytes).to_bytes(4, byteorder='big'))
            # Write metadata
            f.write(metadata_bytes)
            # Write encrypted data
            f.write(encrypted_data)
        
        return encrypted_path, key

    def decrypt_video(self, encrypted_path: str, key: bytes, output_dir: str = "decrypted_videos") -> str:
        """
        Decrypt a video file using the provided key
        Returns: path to decrypted video
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        with open(encrypted_path, 'rb') as f:
            # Read metadata length
            metadata_len = int.from_bytes(f.read(4), byteorder='big')
            # Read metadata
            metadata = json.loads(f.read(metadata_len).decode('utf-8'))
            # Read encrypted data
            encrypted_data = f.read()
        
        # Get IV from metadata
        iv = b64decode(metadata['iv'])
        
        # Create cipher
        cipher = AES.new(key, AES.MODE_CBC, iv)
        
        # Decrypt and unpad
        decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)
        
        # Save decrypted video
        output_path = os.path.join(output_dir, metadata['original_filename'])
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
        
        return output_path

    def delete_video(self, video_path: str) -> bool:
        """Securely delete a video file"""
        try:
            # Overwrite with random data before deleting
            file_size = os.path.getsize(video_path)
            with open(video_path, 'wb') as f:
                f.write(get_random_bytes(file_size))
            # Delete the file
            os.remove(video_path)
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
