"""
Synthetic stream generation for transcendental cryptography.

This module handles the generation of synthetic digit streams from
multiple offsets into transcendental numbers (π and e).
"""
import numpy as np
import multiprocessing
from typing import List, Tuple, Optional, Union, Callable
from concurrent.futures import ProcessPoolExecutor
import logging

from .digits import get_digit_store, get_pi_digits, get_e_digits

# Configure logging
logger = logging.getLogger(__name__)

def generate_synthetic_stream(
    pi_offsets: List[int],
    e_offsets: List[int],
    length: int = 1000,
    modulus: int = 10,
    threads: int = None
) -> np.ndarray:
    """
    Generate a synthetic stream by combining multiple offsets of π and e.
    
    The resulting stream is created by:
    1. Summing the digits from all π offsets
    2. Summing the digits from all e offsets
    3. Combining these sums using modular arithmetic
    
    Args:
        pi_offsets: List of starting positions in π
        e_offsets: List of starting positions in e
        length: Length of the synthetic stream to generate
        modulus: Modulus for combining digits (typically 10)
        threads: Number of threads to use (None for auto)
    
    Returns:
        NumPy array containing the synthetic stream
    """
    # Determine thread count
    if threads is None:
        threads = max(1, multiprocessing.cpu_count() - 1)
    
    # Calculate chunk size for parallel processing
    chunk_size = max(1, length // threads)
    chunks = [(i, min(i + chunk_size, length)) for i in range(0, length, chunk_size)]
    
    # Use process pool for parallel computation
    with ProcessPoolExecutor(max_workers=threads) as executor:
        futures = [
            executor.submit(
                _generate_stream_chunk,
                start,
                end,
                pi_offsets,
                e_offsets,
                modulus
            )
            for start, end in chunks
        ]
        
        # Collect results
        results = [future.result() for future in futures]
    
    # Combine chunks
    return np.concatenate(results)

def _generate_stream_chunk(
    start: int,
    end: int,
    pi_offsets: List[int],
    e_offsets: List[int],
    modulus: int
) -> np.ndarray:
    """
    Generate a chunk of the synthetic stream (for parallel processing).
    
    Args:
        start: Starting index of chunk
        end: Ending index of chunk (exclusive)
        pi_offsets: List of starting positions in π
        e_offsets: List of starting positions in e
        modulus: Modulus for combining digits
    
    Returns:
        NumPy array containing the chunk
    """
    chunk_length = end - start
    result = np.zeros(chunk_length, dtype=np.uint8)
    
    # Get digit store
    digit_store = get_digit_store()
    
    # Process π offsets
    for offset in pi_offsets:
        # Adjust offset based on chunk
        adjusted_offset = offset + start
        # Get digits for this chunk and offset
        pi_chunk = digit_store.get_pi_digits(adjusted_offset, chunk_length)
        # Add to result (modular addition)
        result = (result + pi_chunk) % modulus
    
    # Process e offsets
    for offset in e_offsets:
        # Adjust offset based on chunk
        adjusted_offset = offset + start
        # Get digits for this chunk and offset
        e_chunk = digit_store.get_e_digits(adjusted_offset, chunk_length)
        # Add to result (modular addition)
        result = (result + e_chunk) % modulus
    
    return result

def generate_streams_from_seeds(
    pi_seed: int,
    e_seed: int,
    num_offsets: int = 100,
    length: int = 1000,
    modulus: int = 10,
    threads: int = None
) -> np.ndarray:
    """
    Generate synthetic stream from seed values.
    
    This function deterministically derives multiple offsets from seed values.
    
    Args:
        pi_seed: Seed for π offsets
        e_seed: Seed for e offsets
        num_offsets: Number of offsets to generate for each transcendental
        length: Length of synthetic stream to generate
        modulus: Modulus for combining digits
        threads: Number of threads to use
    
    Returns:
        NumPy array containing the synthetic stream
    """
    # Generate deterministic offsets from seeds
    pi_offsets = _generate_offsets_from_seed(pi_seed, num_offsets)
    e_offsets = _generate_offsets_from_seed(e_seed, num_offsets)
    
    # Generate synthetic stream
    return generate_synthetic_stream(
        pi_offsets,
        e_offsets,
        length,
        modulus,
        threads
    )

def _generate_offsets_from_seed(seed: int, count: int) -> List[int]:
    """
    Generate deterministic offsets from a seed value.
    
    Args:
        seed: Integer seed value
        count: Number of offsets to generate
    
    Returns:
        List of offset positions
    """
    # Use numpy's random generator with seed for deterministic results
    rng = np.random.RandomState(seed)
    
    # Generate offsets in range [0, 1 billion)
    max_offset = 1_000_000_000
    offsets = rng.randint(0, max_offset, size=count)
    
    return offsets.tolist()

def compare_streams(stream1: np.ndarray, stream2: np.ndarray) -> float:
    """
    Compare two synthetic streams for similarity.
    
    Args:
        stream1: First stream
        stream2: Second stream
    
    Returns:
        Similarity score (0.0 to 1.0)
    """
    if len(stream1) != len(stream2):
        min_len = min(len(stream1), len(stream2))
        stream1 = stream1[:min_len]
        stream2 = stream2[:min_len]
    
    # Count matching positions
    matches = np.sum(stream1 == stream2)
    return matches / len(stream1)

class StreamGenerator:
    """Class for managing and caching synthetic streams."""
    
    def __init__(
        self, 
        pi_offsets: List[int] = None,
        e_offsets: List[int] = None,
        modulus: int = 10,
        threads: int = None
    ):
        """
        Initialize the stream generator.
        
        Args:
            pi_offsets: List of π offsets (optional)
            e_offsets: List of e offsets (optional)
            modulus: Modulus for combining digits
            threads: Number of threads to use
        """
        self.pi_offsets = pi_offsets or []
        self.e_offsets = e_offsets or []
        self.modulus = modulus
        self.threads = threads
        
        # Cache for generated streams
        self._cache = {}
    
    def set_parameters(
        self,
        pi_offsets: List[int] = None,
        e_offsets: List[int] = None,
        modulus: int = None,
        threads: int = None
    ) -> None:
        """
        Update generator parameters.
        
        Args:
            pi_offsets: List of π offsets (optional)
            e_offsets: List of e offsets (optional)
            modulus: Modulus for combining digits (optional)
            threads: Number of threads to use (optional)
        """
        if pi_offsets is not None:
            self.pi_offsets = pi_offsets
        if e_offsets is not None:
            self.e_offsets = e_offsets
        if modulus is not None:
            self.modulus = modulus
        if threads is not None:
            self.threads = threads
        
        # Clear cache when parameters change
        self._cache = {}
    
    def from_seeds(
        self,
        pi_seed: int,
        e_seed: int,
        num_offsets: int = 100
    ) -> None:
        """
        Set parameters using seed values.
        
        Args:
            pi_seed: Seed for π offsets
            e_seed: Seed for e offsets
            num_offsets: Number of offsets to generate for each transcendental
        """
        pi_offsets = _generate_offsets_from_seed(pi_seed, num_offsets)
        e_offsets = _generate_offsets_from_seed(e_seed, num_offsets)
        
        self.set_parameters(pi_offsets=pi_offsets, e_offsets=e_offsets)
    
    def generate(self, length: int = 1000) -> np.ndarray:
        """
        Generate a synthetic stream with current parameters.
        
        Args:
            length: Length of stream to generate
        
        Returns:
            NumPy array containing the synthetic stream
        
        Raises:
            ValueError: If no offsets are set
        """
        if not self.pi_offsets and not self.e_offsets:
            raise ValueError("No offsets set. Use set_parameters() or from_seeds() first.")
        
        # Check cache
        cache_key = length
        if cache_key in self._cache:
            return self._cache[cache_key].copy()
        
        # Generate stream
        stream = generate_synthetic_stream(
            self.pi_offsets,
            self.e_offsets,
            length,
            self.modulus,
            self.threads
        )
        
        # Cache result (up to a limit)
        if len(self._cache) < 10:  # Limit cache size
            self._cache[cache_key] = stream.copy()
        
        return stream
    
    def clear_cache(self) -> None:
        """Clear the stream cache."""
        self._cache = {}


# Create singleton instance for convenience
_stream_generator = None

def get_stream_generator() -> StreamGenerator:
    """
    Get the singleton StreamGenerator instance.
    
    Returns:
        StreamGenerator instance
    """
    global _stream_generator
    if _stream_generator is None:
        _stream_generator = StreamGenerator()
    return _stream_generator

# Convenience function
def get_synthetic_stream(
    pi_seed: int,
    e_seed: int,
    length: int = 1000,
    num_offsets: int = 100,
    modulus: int = 10,
    threads: int = None
) -> np.ndarray:
    """
    Generate a synthetic stream using seeds.
    
    Args:
        pi_seed: Seed for π offsets
        e_seed: Seed for e offsets
        length: Length of stream to generate
        num_offsets: Number of offsets to generate
        modulus: Modulus for combining digits
        threads: Number of threads to use
    
    Returns:
        NumPy array containing the synthetic stream
    """
    generator = get_stream_generator()
    generator.from_seeds(pi_seed, e_seed, num_offsets)
    return generator.generate(length)
