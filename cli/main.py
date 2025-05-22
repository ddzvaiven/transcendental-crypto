#!/usr/bin/env python
"""
Command-line interface for transcendental cryptography.

This module provides a CLI for the transcendental cryptography system,
allowing users to generate keys, encrypt/decrypt data, and manage certificates.
"""
import os
import sys
import argparse
import logging
from typing import List, Optional
import json

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.transcendental.digits import download_digits, verify_digits
from src.transcendental.patterns import Pattern
from src.crypto.keys import PrivateKey, PublicKey
from src.crypto.encryption import encrypt_file, decrypt_file, encrypt_message, decrypt_message

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_command(args):
    """
    Download and verify transcendental digit files.
    
    Args:
        args: Command-line arguments
    """
    logger.info("Setting up transcendental digit files...")
    
    # Download digits
    download_digits(force=args.force, data_dir=args.data_dir)
    
    # Verify digits
    if verify_digits(data_dir=args.data_dir):
        logger.info("Digit files verified successfully.")
    else:
        logger.error("Digit file verification failed!")
        sys.exit(1)
    
    logger.info("Setup complete.")

def keygen_command(args):
    """
    Generate a key pair.
    
    Args:
        args: Command-line arguments
    """
    logger.info("Generating key pair...")
    
    # Parse pattern
    if args.pattern:
        digits = [int(d) for d in args.pattern.split(',')]
        
        spacing = None
        if args.spacing:
            spacing = [int(s) for s in args.spacing.split(',')]
            
            # Validate
            if len(spacing) != len(digits) - 1:
                logger.error("Invalid spacing: must be exactly one less than pattern length")
                sys.exit(1)
        
        pattern = Pattern(digits, spacing)
    else:
        # Generate random pattern
        pattern_length = args.pattern_length
        use_spacing = not args.no_spacing
        max_spacing = args.max_spacing
        
        # Generate random digits
        import random
        digits = [random.randint(0, 9) for _ in range(pattern_length)]
        
        # Generate spacing if needed
        spacing = None
        if use_spacing and pattern_length > 1:
            spacing = [random.randint(0, max_spacing) for _ in range(pattern_length - 1)]
        
        pattern = Pattern(digits, spacing)
    
    # Create private key
    if args.pi_seed is not None and args.e_seed is not None:
        # Use provided seeds
        private_key = PrivateKey(
            pi_seed=args.pi_seed,
            e_seed=args.e_seed,
            pattern=pattern,
            num_offsets=args.num_offsets,
            modulus=args.modulus
        )
    else:
        # Generate random seeds
        import secrets
        pi_seed = secrets.randbits(64)
        e_seed = secrets.randbits(64)
        
        private_key = PrivateKey(
            pi_seed=pi_seed,
            e_seed=e_seed,
            pattern=pattern,
            num_offsets=args.num_offsets,
            modulus=args.modulus
        )
    
    # Generate public key
    public_key = private_key.get_public_key(args.max_positions)
    
    # Save keys
    if args.private_key:
        private_key.save(args.private_key)
        logger.info(f"Private key saved to {args.private_key}")
    
    if args.public_key:
        public_key.save(args.public_key)
        logger.info(f"Public key saved to {args.public_key}")
    
    # Print key details
    if args.verbose:
        print("\nPrivate Key:")
        print(f"  Pi Seed: {private_key.pi_seed}")
        print(f"  E Seed: {private_key.e_seed}")
        print(f"  Pattern: {private_key.pattern}")
        print(f"  Num Offsets: {private_key.num_offsets}")
        print(f"  Modulus: {private_key.modulus}")
        
        print("\nPublic Key:")
        print(f"  Verification Token: {public_key.verification_token}")
        print(f"  Max Positions: {public_key.max_positions}")
        
        # Find and print positions
        positions = private_key.find_positions(public_key.max_positions)
        print(f"\nPattern Positions: {positions}")
    
    logger.info("Key pair generated successfully.")

def encrypt_command(args):
    """
    Encrypt a file or message.
    
    Args:
        args: Command-line arguments
    """
    # Load public key
    try:
        public_key = PublicKey.load(args.public_key)
    except Exception as e:
        logger.error(f"Failed to load public key: {e}")
        sys.exit(1)
    
    if args.text:
        # Encrypt message
        encrypted = encrypt_message(args.input, public_key)
        
        if args.output:
            # Save to file
            with open(args.output, 'w') as f:
                f.write(encrypted)
            logger.info(f"Encrypted message saved to {args.output}")
        else:
            # Print to console
            print(encrypted)
    else:
        # Encrypt file
        try:
            encrypt_file(args.input, args.output, public_key)
            logger.info(f"Encrypted file saved to {args.output}")
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            sys.exit(1)

def decrypt_command(args):
    """
    Decrypt a file or message.
    
    Args:
        args: Command-line arguments
    """
    # Load private key
    try:
        private_key = PrivateKey.load(args.private_key)
    except Exception as e:
        logger.error(f"Failed to load private key: {e}")
        sys.exit(1)
    
    if args.text:
        # Read encrypted message
        if os.path.exists(args.input):
            with open(args.input, 'r') as f:
                encrypted = f.read()
        else:
            encrypted = args.input
        
        # Decrypt message
        try:
            decrypted = decrypt_message(encrypted, private_key)
            
            if args.output:
                # Save to file
                with open(args.output, 'w') as f:
                    f.write(decrypted)
                logger.info(f"Decrypted message saved to {args.output}")
            else:
                # Print to console
                print(decrypted)
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            sys.exit(1)
    else:
        # Decrypt file
        try:
            decrypt_file(args.input, args.output, private_key)
            logger.info(f"Decrypted file saved to {args.output}")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            sys.exit(1)

def verify_command(args):
    """
    Verify a key pair.
    
    Args:
        args: Command-line arguments
    """
    # Load keys
    try:
        private_key = PrivateKey.load(args.private_key)
        public_key = PublicKey.load(args.public_key)
    except Exception as e:
        logger.error(f"Failed to load keys: {e}")
        sys.exit(1)
    
    # Verify keys
    from src.crypto.keys import verify_key_pair
    if verify_key_pair(private_key, public_key):
        logger.info("Key pair verified successfully.")
        
        if args.verbose:
            # Find and print positions
            positions = private_key.find_positions(public_key.max_positions)
            print(f"Pattern Positions: {positions}")
    else:
        logger.error("Key pair verification failed!")
        sys.exit(1)

def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(description="Transcendental Cryptography CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Download and verify transcendental digit files")
    setup_parser.add_argument("--force", action="store_true", help="Force download even if files exist")
    setup_parser.add_argument("--data-dir", help="Directory to store digit files")
    
    # Key generation command
    keygen_parser = subparsers.add_parser("keygen", help="Generate a key pair")
    keygen_parser.add_argument("--pattern", help="Comma-separated digit pattern (e.g., '3,1,4')")
    keygen_parser.add_argument("--spacing", help="Comma-separated spacing between digits (e.g., '5,10')")
    keygen_parser.add_argument("--pattern-length", type=int, default=3, help="Length of random pattern to generate")
    keygen_parser.add_argument("--no-spacing", action="store_true", help="Don't use spacing in random pattern")
    keygen_parser.add_argument("--max-spacing", type=int, default=10, help="Maximum spacing for random pattern")
    keygen_parser.add_argument("--pi-seed", type=int, help="Seed for π offsets")
    keygen_parser.add_argument("--e-seed", type=int, help="Seed for e offsets")
    keygen_parser.add_argument("--num-offsets", type=int, default=100, help="Number of offsets to generate")
    keygen_parser.add_argument("--modulus", type=int, default=10, help="Modulus for combining digits")
    keygen_parser.add_argument("--max-positions", type=int, default=5, help="Maximum positions to use")
    keygen_parser.add_argument("--private-key", help="File to save private key to")
    keygen_parser.add_argument("--public-key", help="File to save public key to")
    keygen_parser.add_argument("--verbose", "-v", action="store_true", help="Print detailed key information")
    
    # Encryption command
    encrypt_parser = subparsers.add_parser("encrypt", help="Encrypt a file or message")
    encrypt_parser.add_argument("input", help="File to encrypt or message text")
    encrypt_parser.add_argument("output", help="File to save encrypted data to")
    encrypt_parser.add_argument("--public-key", required=True, help="Public key file to use")
    encrypt_parser.add_argument("--text", "-t", action="store_true", help="Encrypt text message instead of file")
    
    # Decryption command
    decrypt_parser = subparsers.add_parser("decrypt", help="Decrypt a file or message")
    decrypt_parser.add_argument("input", help="File to decrypt or encrypted message")
    decrypt_parser.add_argument("output", help="File to save decrypted data to")
    decrypt_parser.add_argument("--private-key", required=True, help="Private key file to use")
    decrypt_parser.add_argument("--text", "-t", action="store_true", help="Decrypt text message instead of file")
    
    # Verification command
    verify_parser = subparsers.add_parser("verify", help="Verify a key pair")
    verify_parser.add_argument("--private-key", required=True, help="Private key file to verify")
    verify_parser.add_argument("--public-key", required=True, help="Public key file to verify")
    verify_parser.add_argument("--verbose", "-v", action="store_true", help="Print detailed verification information")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    if args.command == "setup":
        setup_command(args)
    elif args.command == "keygen":
        keygen_command(args)
    elif args.command == "encrypt":
        encrypt_command(args)
    elif args.command == "decrypt":
        decrypt_command(args)
    elif args.command == "verify":
        verify_command(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
