#!/usr/bin/env python
"""
Enhanced Transcendental Cryptography Demo

This script demonstrates the enhanced version of the transcendental cryptography
system that uses follow sequences instead of just position indices.

The script shows:
1. Pattern matching with follow sequence extraction
2. Key generation using follow sequences
3. Encryption and decryption using the derived keys
4. Visual representation of how the system works
"""
import os
import sys
import numpy as np
import hashlib
from typing import List, Tuple

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.transcendental.digits import download_digits, verify_digits
from src.transcendental.streams import get_synthetic_stream
from src.transcendental.patterns import Pattern, PatternMatcher
from src.crypto.keys import PrivateKey, PublicKey
from src.crypto.encryption import encrypt_message, decrypt_message


def ensure_digit_files():
    """Download and verify digit files if needed."""
    if not verify_digits():
        print("Downloading transcendental digit files (this may take a while)...")
        download_digits()
        
        if not verify_digits():
            print("Failed to download or verify digit files!")
            sys.exit(1)
        
        print("Digit files successfully downloaded and verified.")
    else:
        print("Transcendental digit files already exist and are verified.")


def demonstrate_pattern_matching():
    """Demonstrate pattern matching with follow sequence extraction."""
    print("\n=== Pattern Matching Demonstration ===")
    
    # Create a simple pattern
    pattern = Pattern([3, 1, 4], [2, 3])
    print(f"Pattern: {pattern}")
    
    # Generate a synthetic stream
    pi_seed = 12345
    e_seed = 67890
    stream = get_synthetic_stream(pi_seed, e_seed, length=5000)
    
    # Find pattern matches
    matcher = PatternMatcher(follow_digits=25)
    matches = matcher.find_pattern(pattern, stream, max_positions=3)
    
    print(f"Found {len(matches)} pattern matches:")
    
    for i, (pos, follow_seq) in enumerate(matches, 1):
        # Convert follow sequence to string for display
        follow_str = "".join(str(d) for d in follow_seq)
        
        print(f"  Match #{i} at position {pos}:")
        print(f"    Follow sequence: {follow_str}")
    
    # Hash the follow sequences
    follow_sequences = [seq for _, seq in matches]
    hash_value = matcher.hash_follow_sequences(follow_sequences)
    
    print(f"\nHash of follow sequences:")
    print(f"  {hash_value}")
    
    return (pattern, pi_seed, e_seed, matches, hash_value)


def demonstrate_key_generation():
    """Demonstrate key generation using follow sequences."""
    print("\n=== Key Generation Demonstration ===")
    
    # Generate a private key
    private_key = PrivateKey.generate(
        pattern_length=4,
        use_spacing=True,
        max_spacing=5,
        follow_digits=25
    )
    
    print("Generated private key:")
    print(f"  π seed: {private_key.pi_seed}")
    print(f"  e seed: {private_key.e_seed}")
    print(f"  Pattern: {private_key.pattern}")
    
    # Find pattern matches
    matches = private_key.find_pattern_matches(max_positions=3)
    
    print(f"\nFound {len(matches)} pattern matches:")
    
    for i, (pos, follow_seq) in enumerate(matches, 1):
        # Convert follow sequence to string for display
        follow_str = "".join(str(d) for d in follow_seq)
        
        print(f"  Match #{i} at position {pos}:")
        print(f"    Follow sequence: {follow_str}")
    
    # Generate public key
    public_key = private_key.get_public_key(max_positions=3)
    
    print(f"\nGenerated public key:")
    print(f"  Verification token: {public_key.verification_token}")
    print(f"  Max positions: {public_key.max_positions}")
    print(f"  Follow digits: {public_key.follow_digits}")
    
    return (private_key, public_key)


def demonstrate_encryption_decryption(private_key, public_key):
    """Demonstrate encryption and decryption using derived keys."""
    print("\n=== Encryption and Decryption Demonstration ===")
    
    # Create a test message
    message = "This is a secret message encrypted using transcendental cryptography with follow sequences."
    print(f"Original message: {message}")
    
    # Encrypt the message
    encrypted = encrypt_message(message, public_key)
    print(f"Encrypted message (truncated): {encrypted[:100]}...")
    
    # Decrypt the message
    decrypted = decrypt_message(encrypted, private_key)
    print(f"Decrypted message: {decrypted}")
    
    # Verify successful decryption
    if message == decrypted:
        print("\n✅ Successful encryption and decryption!")
    else:
        print("\n❌ Decryption failed!")


def visualize_system(pattern, matches):
    """Create a visual representation of the system."""
    print("\n=== Visual Representation of Enhanced Cryptography ===")
    
    print("Pattern search in synthetic stream:")
    
    # Create a small stream for visualization
    stream_preview = np.random.randint(0, 10, size=80)
    
    # Mark pattern occurrences
    stream_str = ""
    for i, digit in enumerate(stream_preview):
        if i % 20 == 0 and i > 0:
            stream_str += "\n"
        
        # Use position 23 as an example match position
        if i == 23:
            stream_str += f"[{digit}]"  # Start of pattern
        elif i == 26:  # 23 + 1 + spacing[0] = 23 + 1 + 2 = 26
            stream_str += f"[{digit}]"  # Second digit
        elif i == 30:  # 26 + 1 + spacing[1] = 26 + 1 + 3 = 30
            stream_str += f"[{digit}]"  # Third digit
        elif 31 <= i < 31 + 25:  # Follow sequence (25 digits)
            stream_str += f"*{digit}*"  # Follow sequence
        else:
            stream_str += f" {digit} "
    
    print(stream_str)
    
    print("\nLegend:")
    print("  [x] = Pattern digit")
    print("  *x* = Follow sequence digit")
    print("   x  = Regular stream digit")
    
    print("\nEnhanced Security Process:")
    print("1. Private key contains pattern and offset information")
    print("2. Pattern is found within the synthetic stream")
    print("3. Follow sequences are extracted after each pattern occurrence")
    print("4. Follow sequences are hashed to create the verification token")
    print("5. The verification token is used to derive the encryption key")
    print("6. This approach provides stronger security than using just positions")


def run_demo():
    """Run the complete enhanced transcendental cryptography demo."""
    print("=" * 80)
    print("ENHANCED TRANSCENDENTAL CRYPTOGRAPHY DEMONSTRATION")
    print("=" * 80)
    
    # Ensure digit files are available
    ensure_digit_files()
    
    # Demonstrate pattern matching
    pattern, pi_seed, e_seed, matches, hash_value = demonstrate_pattern_matching()
    
    # Demonstrate key generation
    private_key, public_key = demonstrate_key_generation()
    
    # Demonstrate encryption and decryption
    demonstrate_encryption_decryption(private_key, public_key)
    
    # Visualize the system
    visualize_system(pattern, matches)
    
    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
