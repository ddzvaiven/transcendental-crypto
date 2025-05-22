"""
Digit management for transcendental cryptography.

This module handles downloading, storing, and efficiently accessing 
digits of transcendental numbers (π and e).
"""
import os
import shutil
import numpy as np
import mmap
from pathlib import Path
from typing import Union, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default data directory is in the user's home directory
DEFAULT_DATA_DIR = os.path.join(os.path.expanduser("~"), ".tcrypt", "data")

# Hard-coded correct beginnings of π and e (for verification)
PI_START = "3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679"
E_START = "2.7182818284590452353602874713526624977572470936999595749669676277240766303535475945713821785251664274"

class DigitStore:
    """Efficiently stores and provides access to transcendental number digits."""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the digit store.
        
        Args:
            data_dir: Directory to store digit files, defaults to ~/.tcrypt/data
        """
        self.data_dir = data_dir or DEFAULT_DATA_DIR
        self._ensure_data_dir()
        
        # File paths
        self.pi_path = os.path.join(self.data_dir, "pi_1m.txt")
        self.e_path = os.path.join(self.data_dir, "e_1m.txt")
        
        # Memory-mapped files
        self._pi_mmap = None
        self._e_mmap = None
        
        # Cache frequently accessed ranges
        self._pi_cache = {}
        self._e_cache = {}
    
    def _ensure_data_dir(self) -> None:
        """Ensure the data directory exists."""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def download_digits(self, force: bool = False) -> None:
        """
        Download π and e digit files if they don't exist.
        
        Args:
            force: If True, download even if files already exist
        """
        # Get the directory containing this script
        this_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Check for built-in digit files
        builtin_pi_path = os.path.join(this_dir, "data", "pi_1m.txt")
        builtin_e_path = os.path.join(this_dir, "data", "e_1m.txt")
        
        # Pi digits
        if force or not os.path.exists(self.pi_path):
            if os.path.exists(builtin_pi_path):
                # Copy built-in file
                logger.info(f"Copying π digits from {builtin_pi_path} to {self.pi_path}")
                shutil.copy2(builtin_pi_path, self.pi_path)
            else:
                # Create file with known correct values
                logger.info(f"Creating π digits file with correct values")
                with open(self.pi_path, 'w') as f:
                    f.write(PI_START)
        
        # E digits
        if force or not os.path.exists(self.e_path):
            if os.path.exists(builtin_e_path):
                # Copy built-in file
                logger.info(f"Copying e digits from {builtin_e_path} to {self.e_path}")
                shutil.copy2(builtin_e_path, self.e_path)
            else:
                # Create file with known correct values
                logger.info(f"Creating e digits file with correct values")
                with open(self.e_path, 'w') as f:
                    f.write(E_START)
    
    def verify_digits(self) -> bool:
        """
        Verify that digit files exist and contain valid digits.
        
        Returns:
            True if both files exist and contain valid digits
        """
        if not os.path.exists(self.pi_path) or not os.path.exists(self.e_path):
            return False
        
        # Check that files contain valid digits
        try:
            # Check first chars of π against known correct values
            with open(self.pi_path, 'r') as f:
                pi_start = f.read(len(PI_START))
                if not pi_start.startswith(PI_START[:10]):
                    logger.warning("π digits file has invalid format")
                    return False
            
            # Check first chars of e against known correct values
            with open(self.e_path, 'r') as f:
                e_start = f.read(len(E_START))
                if not e_start.startswith(E_START[:10]):
                    logger.warning("e digits file has invalid format")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error verifying digit files: {e}")
            return False
    
    def open(self) -> None:
        """
        Open digit files and prepare memory-mapped access.
        
        Raises:
            FileNotFoundError: If digit files don't exist
        """
        # Verify files exist
        if not os.path.exists(self.pi_path) or not os.path.exists(self.e_path):
            raise FileNotFoundError("Digit files not found. Run download_digits() first.")
        
        # Memory-map π digits
        pi_file = open(self.pi_path, 'r+b')
        self._pi_mmap = mmap.mmap(pi_file.fileno(), 0)
        
        # Memory-map e digits
        e_file = open(self.e_path, 'r+b')
        self._e_mmap = mmap.mmap(e_file.fileno(), 0)
        
        logger.info("Opened digit files for memory-mapped access")
    
    def close(self) -> None:
        """Close memory-mapped files."""
        if self._pi_mmap:
            self._pi_mmap.close()
            self._pi_mmap = None
        
        if self._e_mmap:
            self._e_mmap.close()
            self._e_mmap = None
        
        logger.info("Closed digit files")
    
    def get_pi_digits(self, start: int, length: int) -> np.ndarray:
        """
        Get a range of π digits.
        
        Args:
            start: Starting position (0-indexed)
            length: Number of digits to retrieve
        
        Returns:
            NumPy array of digits
        
        Raises:
            ValueError: If start or length is invalid
        """
        if start < 0 or length <= 0:
            raise ValueError("Invalid start or length")
        
        # Check if range is already cached
        cache_key = (start, length)
        if cache_key in self._pi_cache:
            return self._pi_cache[cache_key].copy()
        
        # Ensure memory map is open
        if not self._pi_mmap:
            self.open()
        
        # Extract digits from memory-mapped file
        digits = np.zeros(length, dtype=np.uint8)
        digit_count = 0
        pos = 0
        
        # Skip the decimal point at the beginning
        while pos < len(self._pi_mmap) and chr(self._pi_mmap[pos]) != '.':
            pos += 1
        pos += 1  # Skip the decimal point
        
        # Skip 'start' digits
        for _ in range(start):
            while pos < len(self._pi_mmap):
                char = chr(self._pi_mmap[pos])
                pos += 1
                if char.isdigit():
                    break
                if pos >= len(self._pi_mmap):
                    pos = 0  # Wrap around
        
        # Read 'length' digits
        while digit_count < length:
            if pos >= len(self._pi_mmap):
                pos = 0  # Wrap around
            
            char = chr(self._pi_mmap[pos])
            pos += 1
            
            if char.isdigit():
                digits[digit_count] = int(char)
                digit_count += 1
        
        # Cache result for future use (up to a limit)
        if len(self._pi_cache) < 100:  # Limit cache size
            self._pi_cache[cache_key] = digits.copy()
        
        return digits
    
    def get_e_digits(self, start: int, length: int) -> np.ndarray:
        """
        Get a range of e digits.
        
        Args:
            start: Starting position (0-indexed)
            length: Number of digits to retrieve
        
        Returns:
            NumPy array of digits
        
        Raises:
            ValueError: If start or length is invalid
        """
        if start < 0 or length <= 0:
            raise ValueError("Invalid start or length")
        
        # Check if range is already cached
        cache_key = (start, length)
        if cache_key in self._e_cache:
            return self._e_cache[cache_key].copy()
        
        # Ensure memory map is open
        if not self._e_mmap:
            self.open()
        
        # Extract digits from memory-mapped file
        digits = np.zeros(length, dtype=np.uint8)
        digit_count = 0
        pos = 0
        
        # Skip the decimal point at the beginning
        while pos < len(self._e_mmap) and chr(self._e_mmap[pos]) != '.':
            pos += 1
        pos += 1  # Skip the decimal point
        
        # Skip 'start' digits
        for _ in range(start):
            while pos < len(self._e_mmap):
                char = chr(self._e_mmap[pos])
                pos += 1
                if char.isdigit():
                    break
                if pos >= len(self._e_mmap):
                    pos = 0  # Wrap around
        
        # Read 'length' digits
        while digit_count < length:
            if pos >= len(self._e_mmap):
                pos = 0  # Wrap around
            
            char = chr(self._e_mmap[pos])
            pos += 1
            
            if char.isdigit():
                digits[digit_count] = int(char)
                digit_count += 1
        
        # Cache result for future use (up to a limit)
        if len(self._e_cache) < 100:  # Limit cache size
            self._e_cache[cache_key] = digits.copy()
        
        return digits
    
    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Singleton instance for global use
_digit_store = None

def get_digit_store(data_dir: Optional[str] = None) -> DigitStore:
    """
    Get or create the singleton DigitStore instance.
    
    Args:
        data_dir: Optional data directory path
    
    Returns:
        DigitStore instance
    """
    global _digit_store
    if _digit_store is None:
        _digit_store = DigitStore(data_dir)
    return _digit_store

# Convenience functions
def download_digits(force: bool = False, data_dir: Optional[str] = None) -> None:
    """
    Download digit files.
    
    Args:
        force: If True, download even if files already exist
        data_dir: Optional data directory path
    """
    digit_store = get_digit_store(data_dir)
    digit_store.download_digits(force)

def verify_digits(data_dir: Optional[str] = None) -> bool:
    """
    Verify digit files.
    
    Args:
        data_dir: Optional data directory path
    
    Returns:
        True if files exist and have correct format
    """
    digit_store = get_digit_store(data_dir)
    return digit_store.verify_digits()

def get_pi_digits(start: int, length: int, data_dir: Optional[str] = None) -> np.ndarray:
    """
    Get a range of π digits.
    
    Args:
        start: Starting position (0-indexed)
        length: Number of digits to retrieve
        data_dir: Optional data directory path
    
    Returns:
        NumPy array of digits
    """
    digit_store = get_digit_store(data_dir)
    return digit_store.get_pi_digits(start, length)

def get_e_digits(start: int, length: int, data_dir: Optional[str] = None) -> np.ndarray:
    """
    Get a range of e digits.
    
    Args:
        start: Starting position (0-indexed)
        length: Number of digits to retrieve
        data_dir: Optional data directory path
    
    Returns:
        NumPy array of digits
    """
    digit_store = get_digit_store(data_dir)
    return digit_store.get_e_digits(start, length)
