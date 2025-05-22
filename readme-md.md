# Transcendental Cryptography

A novel cryptographic system based on pattern matching within transcendental numbers.

## Overview

This project implements a cryptographic system that uses patterns within the digits of transcendental numbers (π and e) to create a secure cryptographic primitive. The system generates synthetic streams by combining multiple offsets into π and e, then searches for specific patterns within these streams to create cryptographic certificates and keys.

### Key Features

- **Quantum-Resistant**: Not based on traditional number theory problems that are vulnerable to quantum algorithms
- **Public-Key System**: Supports asymmetric encryption with public and private keys
- **Efficient**: Uses memory-mapped files and parallel processing for performance
- **Small Footprint**: Only requires ~2GB of storage for π and e digit files
- **Novel Approach**: Based on a new mathematical hardness assumption

## Installation

### Prerequisites

- Python 3.7+
- 2GB of free disk space (for π and e digit files)

### Installing from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/transcendental-crypto.git
cd transcendental-crypto

# Install the package
pip install -e .
```

## Quick Start

### Command-line Interface

```bash
# Download and verify transcendental digit files
tcrypt setup

# Generate a key pair
tcrypt keygen --private-key private.json --public-key public.json

# Encrypt a file
tcrypt encrypt plaintext.txt encrypted.enc --public-key public.json

# Decrypt a file
tcrypt decrypt encrypted.enc decrypted.txt --private-key private.json

# Verify a key pair
tcrypt verify --private-key private.json --public-key public.json
```

### Python API

```python
from src.transcendental.digits import download_digits
from src.crypto.keys import PrivateKey, PublicKey
from src.crypto.encryption import encrypt_message, decrypt_message

# Download digit files (first time only)
download_digits()

# Generate a key pair
private_key = PrivateKey.generate()
public_key = private_key.get_public_key()

# Encrypt a message
message = "Hello, transcendental world!"
encrypted = encrypt_message(message, public_key)

# Decrypt the message
decrypted = decrypt_message(encrypted, private_key)
```

## How It Works

The system operates on the principle that finding specific patterns within transcendental number expansions is computationally difficult without knowing where to look.

1. **Key Generation**:
   - Generate random offsets into π and e
   - Define a pattern and spacing rules
   - Find pattern occurrences in the combined digit stream
   - Hash the positions to create a verification token

2. **Encryption**:
   - Use the verification token to derive an encryption key
   - Encrypt data using standard AES with this key

3. **Decryption**:
   - Regenerate the same digit stream using private offsets
   - Find the same pattern positions
   - Derive the same encryption key
   - Decrypt the data

## Security Considerations

- The security of the system relies on the computational difficulty of finding specific patterns in transcendental number expansions without knowing the offsets.
- The system uses standard cryptographic primitives (SHA-256, AES) for actual encryption once the key is derived.
- No formal security proofs exist yet, so consider this experimental for now.

## Documentation

For more detailed documentation, see the docstrings in the source code or the example scripts in the `examples/` directory.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Citation

If you use this project in your research, please cite:

```
@software{transcendental_crypto,
  author = {Transcendental Crypto Team},
  title = {Transcendental Cryptography},
  year = {2025},
  url = {https://github.com/yourusername/transcendental-crypto}
}
```
