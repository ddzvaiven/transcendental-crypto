"""
Complete flow test for transcendental cryptography.

This test demonstrates the complete flow of the system:
1. Generate key pair
2. Encrypt a message
3. Decrypt the message
4. Verify the result
"""
import os
import sys
import tempfile
import unittest
from typing import Tuple

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.transcendental.digits import download_digits, verify_digits
from src.transcendental.patterns import Pattern
from src.crypto.keys import PrivateKey, PublicKey, verify_key_pair
from src.crypto.encryption import encrypt_message, decrypt_message, encrypt_file, decrypt_file


class CompleteFlowTest(unittest.TestCase):
    """Test the complete flow of the transcendental cryptography system."""
    
    @classmethod
    def setUpClass(cls):
        """Set up for all tests - download digit files if needed."""
        # Check if digit files exist
        if not verify_digits():
            print("Downloading digit files...")
            download_digits()
            
            # Verify download
            if not verify_digits():
                raise RuntimeError("Failed to download or verify digit files")
    
    def test_key_generation(self):
        """Test generation of key pair."""
        # Create pattern
        pattern = Pattern([3, 1, 4], [5, 2])
        
        # Generate private key
        private_key = PrivateKey(
            pi_seed=12345,
            e_seed=67890,
            pattern=pattern,
            num_offsets=50,
            modulus=10
        )
        
        # Derive public key
        public_key = private_key.get_public_key(max_positions=3)
        
        # Verify key pair
        self.assertTrue(verify_key_pair(private_key, public_key))
        
        # Get positions
        positions = private_key.find_positions(3)
        self.assertIsNotNone(positions)
        self.assertGreater(len(positions), 0)
        
        print(f"Pattern: {pattern}")
        print(f"Positions: {positions}")
    
    def test_message_encryption(self):
        """Test encryption and decryption of a text message."""
        # Generate key pair
        private_key = PrivateKey.generate(
            pattern_length=4,
            use_spacing=True,
            max_spacing=5,
            num_offsets=50
        )
        public_key = private_key.get_public_key()
        
        # Create test message
        original_message = "This is a secret message for testing transcendental cryptography."
        
        # Encrypt message
        encrypted_message = encrypt_message(original_message, public_key)
        
        # Decrypt message
        decrypted_message = decrypt_message(encrypted_message, private_key)
        
        # Verify result
        self.assertEqual(original_message, decrypted_message)
        
        print(f"Original: {original_message}")
        print(f"Encrypted (partial): {encrypted_message[:60]}...")
        print(f"Decrypted: {decrypted_message}")
    
    def test_file_encryption(self):
        """Test encryption and decryption of a file."""
        # Generate key pair
        private_key = PrivateKey.generate(
            pattern_length=5,
            use_spacing=True,
            max_spacing=5,
            num_offsets=50
        )
        public_key = private_key.get_public_key()
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(delete=False) as original_file:
            original_path = original_file.name
            original_content = b"This is a secret file for testing transcendental cryptography."
            original_file.write(original_content)
        
        encrypted_path = original_path + ".enc"
        decrypted_path = original_path + ".dec"
        
        try:
            # Encrypt file
            encrypt_file(original_path, encrypted_path, public_key)
            
            # Decrypt file
            decrypt_file(encrypted_path, decrypted_path, private_key)
            
            # Verify result
            with open(decrypted_path, 'rb') as f:
                decrypted_content = f.read()
            
            self.assertEqual(original_content, decrypted_content)
            
            print(f"Original size: {len(original_content)} bytes")
            print(f"Encrypted size: {os.path.getsize(encrypted_path)} bytes")
            print(f"Decrypted size: {len(decrypted_content)} bytes")
        
        finally:
            # Clean up
            for path in [original_path, encrypted_path, decrypted_path]:
                if os.path.exists(path):
                    os.unlink(path)
    
    def test_complete_flow(self):
        """Test the complete flow with file storage of keys."""
        # Create temporary files for keys
        with tempfile.NamedTemporaryFile(delete=False) as private_key_file:
            private_key_path = private_key_file.name
        
        with tempfile.NamedTemporaryFile(delete=False) as public_key_file:
            public_key_path = public_key_file.name
        
        try:
            # Generate and save key pair
            original_private_key = PrivateKey.generate(
                pattern_length=3,
                use_spacing=True,
                max_spacing=10,
                num_offsets=100
            )
            original_private_key.save(private_key_path)
            
            original_public_key = original_private_key.get_public_key()
            original_public_key.save(public_key_path)
            
            # Load keys from files
            loaded_private_key = PrivateKey.load(private_key_path)
            loaded_public_key = PublicKey.load(public_key_path)
            
            # Verify loaded keys
            self.assertTrue(verify_key_pair(loaded_private_key, loaded_public_key))
            
            # Encrypt and decrypt a message
            original_message = "Testing the complete flow with file storage."
            
            encrypted_message = encrypt_message(original_message, loaded_public_key)
            decrypted_message = decrypt_message(encrypted_message, loaded_private_key)
            
            # Verify result
            self.assertEqual(original_message, decrypted_message)
            
            print("Complete flow test passed successfully!")
        
        finally:
            # Clean up
            for path in [private_key_path, public_key_path]:
                if os.path.exists(path):
                    os.unlink(path)
    
    def test_performance(self):
        """Test the performance of key operations."""
        import time
        
        # Generate key pair
        start_time = time.time()
        private_key = PrivateKey.generate(
            pattern_length=4,
            use_spacing=True,
            max_spacing=5,
            num_offsets=100
        )
        public_key = private_key.get_public_key(max_positions=5)
        keygen_time = time.time() - start_time
        
        # Find positions
        start_time = time.time()
        positions = private_key.find_positions(5)
        find_time = time.time() - start_time
        
        # Encrypt a message
        message = "A" * 1000  # 1KB message
        
        start_time = time.time()
        encrypted = encrypt_message(message, public_key)
        encrypt_time = time.time() - start_time
        
        # Decrypt the message
        start_time = time.time()
        decrypted = decrypt_message(encrypted, private_key)
        decrypt_time = time.time() - start_time
        
        # Print results
        print("\nPerformance Results:")
        print(f"Key Generation: {keygen_time:.4f} seconds")
        print(f"Pattern Finding: {find_time:.4f} seconds")
        print(f"Encryption (1KB): {encrypt_time:.4f} seconds")
        print(f"Decryption (1KB): {decrypt_time:.4f} seconds")
        
        # Verify result
        self.assertEqual(message, decrypted)


if __name__ == "__main__":
    unittest.main()
