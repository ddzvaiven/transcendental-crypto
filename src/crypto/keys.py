"""
Key management for transcendental cryptography.

This module handles the generation, storage, and validation of
cryptographic keys based on transcendental number patterns.
"""
import os
import json
import hashlib
import secrets
import base64
from typing import Dict, List, Tuple, Optional, Union
import logging

import numpy as np

from ..transcendental.streams import generate_streams_from_seeds, get_synthetic_stream
from ..transcendental.patterns import Pattern, PatternMatcher

# Configure logging
logger = logging.getLogger(__name__)

class PrivateKey:
    """Private key for transcendental cryptography."""
    
    def __init__(
        self,
        pi_seed: int,
        e_seed: int,
        pattern: Pattern,
        num_offsets: int = 100,
        modulus: int = 10,
        follow_digits: int = 25
    ):
        """
        Initialize a private key.
        
        Args:
            pi_seed: Seed for π offsets
            e_seed: Seed for e offsets
            pattern: Pattern to search for
            num_offsets: Number of offsets to generate
            modulus: Modulus for combining digits
            follow_digits: Number of digits to extract after pattern match
        """
        self.pi_seed = pi_seed
        self.e_seed = e_seed
        self.pattern = pattern
        self.num_offsets = num_offsets
        self.modulus = modulus
        self.follow_digits = follow_digits
        
        # Cache for pattern matches
        self._matches = None
    
    def generate_stream(self, length: int = 10000) -> np.ndarray:
        """
        Generate the synthetic stream for this key.
        
        Args:
            length: Length of stream to generate
        
        Returns:
            NumPy array containing the synthetic stream
        """
        return get_synthetic_stream(
            self.pi_seed,
            self.e_seed,
            length,
            self.num_offsets,
            self.modulus
        )
    
    def find_pattern_matches(self, max_positions: int = 5) -> List[Tuple[int, np.ndarray]]:
        """
        Find pattern matches in the synthetic stream.
        
        Args:
            max_positions: Maximum number of matches to find
        
        Returns:
            List of tuples (position, follow_sequence)
        """
        if self._matches is not None:
            return self._matches[:max_positions]
        
        # Generate stream
        stream = self.generate_stream()
        
        # Find pattern
        matcher = PatternMatcher(follow_digits=self.follow_digits)
        matches = matcher.find_pattern(
            self.pattern,
            stream,
            max_positions
        )
        
        # Cache result
        self._matches = matches
        
        return matches
    
    def get_follow_sequences(self, max_positions: int = 5) -> List[np.ndarray]:
        """
        Get follow sequences from pattern matches.
        
        Args:
            max_positions: Maximum number of sequences to return
        
        Returns:
            List of follow sequences
        """
        matches = self.find_pattern_matches(max_positions)
        return [seq for _, seq in matches]
    
    def to_dict(self) -> Dict:
        """
        Convert private key to dictionary representation.
        
        Returns:
            Dictionary containing key information
        """
        return {
            "pi_seed": self.pi_seed,
            "e_seed": self.e_seed,
            "pattern": self.pattern.to_dict(),
            "num_offsets": self.num_offsets,
            "modulus": self.modulus,
            "follow_digits": self.follow_digits
        }
    
    def to_json(self) -> str:
        """
        Convert private key to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict())
    
    def save(self, path: str) -> None:
        """
        Save private key to file.
        
        Args:
            path: File path to save to
        """
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def get_public_key(self, max_positions: int = 5) -> 'PublicKey':
        """
        Derive a public key from this private key.
        
        Args:
            max_positions: Maximum number of positions to use
        
        Returns:
            PublicKey instance
        """
        # Find pattern matches and extract follow sequences
        follow_sequences = self.get_follow_sequences(max_positions)
        
        # Create verification token (hash of follow sequences)
        matcher = PatternMatcher(follow_digits=self.follow_digits)
        token = matcher.hash_follow_sequences(follow_sequences)
        
        return PublicKey(token, max_positions, self.follow_digits)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PrivateKey':
        """
        Create a private key from dictionary representation.
        
        Args:
            data: Dictionary containing key information
        
        Returns:
            PrivateKey instance
        """
        pattern = Pattern.from_dict(data["pattern"])
        
        return cls(
            pi_seed=data["pi_seed"],
            e_seed=data["e_seed"],
            pattern=pattern,
            num_offsets=data.get("num_offsets", 100),
            modulus=data.get("modulus", 10),
            follow_digits=data.get("follow_digits", 25)
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'PrivateKey':
        """
        Create a private key from JSON string.
        
        Args:
            json_str: JSON string representation
        
        Returns:
            PrivateKey instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def load(cls, path: str) -> 'PrivateKey':
        """
        Load private key from file.
        
        Args:
            path: File path to load from
        
        Returns:
            PrivateKey instance
        """
        with open(path, 'r') as f:
            data = json.load(f)
        
        return cls.from_dict(data)
    
    @classmethod
    def generate(
        cls,
        pattern_length: int = 3,
        use_spacing: bool = True,
        max_spacing: int = 10,
        num_offsets: int = 100,
        modulus: int = 10,
        follow_digits: int = 25
    ) -> 'PrivateKey':
        """
        Generate a new random private key.
        
        Args:
            pattern_length: Length of pattern to generate
            use_spacing: Whether to use spacing in pattern
            max_spacing: Maximum spacing between digits
            num_offsets: Number of offsets to generate
            modulus: Modulus for combining digits
            follow_digits: Number of digits to extract after pattern match
        
        Returns:
            New PrivateKey instance
        """
        # Generate random seeds
        pi_seed = secrets.randbits(64)
        e_seed = secrets.randbits(64)
        
        # Generate random pattern
        digits = [secrets.randbelow(10) for _ in range(pattern_length)]
        
        spacing = None
        if use_spacing and pattern_length > 1:
            spacing = [secrets.randbelow(max_spacing + 1) for _ in range(pattern_length - 1)]
        
        pattern = Pattern(digits, spacing)
        
        return cls(
            pi_seed=pi_seed,
            e_seed=e_seed,
            pattern=pattern,
            num_offsets=num_offsets,
            modulus=modulus,
            follow_digits=follow_digits
        )


class PublicKey:
    """Public key for transcendental cryptography."""
    
    def __init__(
        self,
        verification_token: str,
        max_positions: int = 5,
        follow_digits: int = 25
    ):
        """
        Initialize a public key.
        
        Args:
            verification_token: Hash of follow sequences
            max_positions: Maximum number of positions used
            follow_digits: Number of digits extracted after each pattern match
        """
        self.verification_token = verification_token
        self.max_positions = max_positions
        self.follow_digits = follow_digits
    
    def to_dict(self) -> Dict:
        """
        Convert public key to dictionary representation.
        
        Returns:
            Dictionary containing key information
        """
        return {
            "verification_token": self.verification_token,
            "max_positions": self.max_positions,
            "follow_digits": self.follow_digits
        }
    
    def to_json(self) -> str:
        """
        Convert public key to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict())
    
    def save(self, path: str) -> None:
        """
        Save public key to file.
        
        Args:
            path: File path to save to
        """
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def derive_encryption_key(self, salt: str = "", key_bytes: int = 32) -> bytes:
        """
        Derive an encryption key from the public key.
        
        Args:
            salt: Optional salt value
            key_bytes: Length of key in bytes (default: 32 for AES-256)
        
        Returns:
            Bytes to use as encryption key
        """
        # Create key material from verification token and salt
        material = f"{self.verification_token}{salt}".encode()
        
        # Use SHA-256 to derive key
        h = hashlib.sha256(material).digest()
        
        # If we need more bytes, use HKDF-like approach
        if key_bytes > len(h):
            result = bytearray(h)
            while len(result) < key_bytes:
                h = hashlib.sha256(h + material).digest()
                result.extend(h)
            return bytes(result[:key_bytes])
        
        return h[:key_bytes]
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PublicKey':
        """
        Create a public key from dictionary representation.
        
        Args:
            data: Dictionary containing key information
        
        Returns:
            PublicKey instance
        """
        return cls(
            verification_token=data["verification_token"],
            max_positions=data.get("max_positions", 5),
            follow_digits=data.get("follow_digits", 25)
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'PublicKey':
        """
        Create a public key from JSON string.
        
        Args:
            json_str: JSON string representation
        
        Returns:
            PublicKey instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def load(cls, path: str) -> 'PublicKey':
        """
        Load public key from file.
        
        Args:
            path: File path to load from
        
        Returns:
            PublicKey instance
        """
        with open(path, 'r') as f:
            data = json.load(f)
        
        return cls.from_dict(data)


def verify_key_pair(private_key: PrivateKey, public_key: PublicKey) -> bool:
    """
    Verify that a private key corresponds to a public key.
    
    Args:
        private_key: Private key to verify
        public_key: Public key to verify against
    
    Returns:
        True if keys correspond, False otherwise
    """
    # Find pattern matches and extract follow sequences
    follow_sequences = private_key.get_follow_sequences(public_key.max_positions)
    
    # Hash follow sequences
    matcher = PatternMatcher(follow_digits=private_key.follow_digits)
    token = matcher.hash_follow_sequences(follow_sequences)
    
    # Compare with public key token
    return token == public_key.verification_token
