"""
Encryption and decryption for transcendental cryptography.

This module handles encryption and decryption of data using keys
derived from transcendental pattern matching.
"""
import os
import json
import base64
import secrets
from typing import Dict, List, Tuple, Optional, Union, BinaryIO
import logging
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
import hashlib

from .keys import PrivateKey, PublicKey
from ..transcendental.patterns import PatternMatcher

# Configure logging
logger = logging.getLogger(__name__)

class EncryptedData:
    """Container for encrypted data and associated metadata."""
    
    def __init__(
        self,
        ciphertext: bytes,
        iv: bytes,
        salt: str,
        verification_token: str
    ):
        """
        Initialize encrypted data container.
        
        Args:
            ciphertext: Encrypted data
            iv: Initialization vector
            salt: Salt used in key derivation
            verification_token: Public key verification token
        """
        self.ciphertext = ciphertext
        self.iv = iv
        self.salt = salt
        self.verification_token = verification_token
    
    def to_dict(self) -> Dict:
        """
        Convert to dictionary representation.
        
        Returns:
            Dictionary containing encrypted data
        """
        return {
            "ciphertext": base64.b64encode(self.ciphertext).decode('utf-8'),
            "iv": base64.b64encode(self.iv).decode('utf-8'),
            "salt": self.salt,
            "verification_token": self.verification_token
        }
    
    def to_json(self) -> str:
        """
        Convert to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict())
    
    def save(self, path: str) -> None:
        """
        Save encrypted data to file.
        
        Args:
            path: File path to save to
        """
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EncryptedData':
        """
        Create from dictionary representation.
        
        Args:
            data: Dictionary containing encrypted data
        
        Returns:
            EncryptedData instance
        """
        return cls(
            ciphertext=base64.b64decode(data["ciphertext"]),
            iv=base64.b64decode(data["iv"]),
            salt=data["salt"],
            verification_token=data["verification_token"]
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'EncryptedData':
        """
        Create from JSON string.
        
        Args:
            json_str: JSON string representation
        
        Returns:
            EncryptedData instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def load(cls, path: str) -> 'EncryptedData':
        """
        Load encrypted data from file.
        
        Args:
            path: File path to load from
        
        Returns:
            EncryptedData instance
        """
        with open(path, 'r') as f:
            data = json.load(f)
        
        return cls.from_dict(data)


def encrypt_data(
    data: bytes,
    public_key: PublicKey,
    salt: Optional[str] = None
) -> EncryptedData:
    """
    Encrypt data using a public key.
    
    Args:
        data: Data to encrypt
        public_key: Public key to use for encryption
        salt: Optional salt for key derivation (random if None)
    
    Returns:
        EncryptedData instance containing the encrypted data
    """
    # Generate salt if not provided
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Derive encryption key
    key = public_key.derive_encryption_key(salt)
    
    # Generate random IV
    iv = os.urandom(16)
    
    # Pad data
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()
    
    # Encrypt data
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    
    # Create encrypted data container
    return EncryptedData(
        ciphertext=ciphertext,
        iv=iv,
        salt=salt,
        verification_token=public_key.verification_token
    )


def decrypt_data(
    encrypted_data: EncryptedData,
    private_key: PrivateKey
) -> bytes:
    """
    Decrypt data using a private key.
    
    Args:
        encrypted_data: Encrypted data to decrypt
        private_key: Private key to use for decryption
    
    Returns:
        Decrypted data
    
    Raises:
        ValueError: If private key doesn't match public key
    """
    # Verify that private key corresponds to encryption public key
    public_key = PublicKey(encrypted_data.verification_token)
    positions = private_key.find_pattern_matches(public_key.max_positions)
    
    # Create verification token and compare
    matcher = PatternMatcher(follow_digits=private_key.follow_digits)
    follow_sequences = [seq for _, seq in positions]
    token = matcher.hash_follow_sequences(follow_sequences)
    
    if token != encrypted_data.verification_token:
        raise ValueError("Private key doesn't match encryption key")
    
    # Derive decryption key
    key = public_key.derive_encryption_key(encrypted_data.salt)
    
    # Decrypt data
    cipher = Cipher(algorithms.AES(key), modes.CBC(encrypted_data.iv))
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(encrypted_data.ciphertext) + decryptor.finalize()
    
    # Unpad data
    unpadder = padding.PKCS7(128).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()
    
    return data


def encrypt_file(
    input_path: str,
    output_path: str,
    public_key: PublicKey,
    chunk_size: int = 64 * 1024  # 64KB chunks
) -> None:
    """
    Encrypt a file using a public key.
    
    Args:
        input_path: Path to file to encrypt
        output_path: Path to save encrypted file
        public_key: Public key to use for encryption
        chunk_size: Size of chunks to read/write
    """
    # Generate salt
    salt = secrets.token_hex(16)
    
    # Read file
    with open(input_path, 'rb') as f:
        data = f.read()
    
    # Encrypt data
    encrypted_data = encrypt_data(data, public_key, salt)
    
    # Save encrypted data
    encrypted_data.save(output_path)


def decrypt_file(
    input_path: str,
    output_path: str,
    private_key: PrivateKey,
    chunk_size: int = 64 * 1024  # 64KB chunks
) -> None:
    """
    Decrypt a file using a private key.
    
    Args:
        input_path: Path to encrypted file
        output_path: Path to save decrypted file
        private_key: Private key to use for decryption
        chunk_size: Size of chunks to read/write
    
    Raises:
        ValueError: If private key doesn't match encryption key
    """
    # Load encrypted data
    encrypted_data = EncryptedData.load(input_path)
    
    # Decrypt data
    data = decrypt_data(encrypted_data, private_key)
    
    # Save decrypted data
    with open(output_path, 'wb') as f:
        f.write(data)


def encrypt_message(
    message: str,
    public_key: PublicKey,
    encoding: str = 'utf-8'
) -> str:
    """
    Encrypt a text message using a public key.
    
    Args:
        message: Text message to encrypt
        public_key: Public key to use for encryption
        encoding: Text encoding to use
    
    Returns:
        JSON string containing encrypted message
    """
    # Convert message to bytes
    data = message.encode(encoding)
    
    # Encrypt data
    encrypted_data = encrypt_data(data, public_key)
    
    # Convert to JSON
    return encrypted_data.to_json()


def decrypt_message(
    encrypted_message: str,
    private_key: PrivateKey,
    encoding: str = 'utf-8'
) -> str:
    """
    Decrypt a text message using a private key.
    
    Args:
        encrypted_message: JSON string containing encrypted message
        private_key: Private key to use for decryption
        encoding: Text encoding to use
    
    Returns:
        Decrypted text message
    
    Raises:
        ValueError: If private key doesn't match encryption key
    """
    # Parse encrypted data
    encrypted_data = EncryptedData.from_json(encrypted_message)
    
    # Decrypt data
    data = decrypt_data(encrypted_data, private_key)
    
    # Convert to string
    return data.decode(encoding)
