"""
Pattern matching for transcendental cryptography.

This module provides utilities for finding and verifying patterns
within synthetic streams generated from transcendental numbers.
"""
import numpy as np
import hashlib
from typing import List, Tuple, Dict, Optional, Union
from concurrent.futures import ThreadPoolExecutor
import logging

# Configure logging
logger = logging.getLogger(__name__)

class Pattern:
    """Represents a pattern to search for in a synthetic stream."""
    
    def __init__(
        self,
        digits: List[int],
        spacing: Optional[List[int]] = None
    ):
        """
        Initialize a pattern.
        
        Args:
            digits: List of digits in the pattern
            spacing: List of spaces between consecutive digits (optional)
                     If None, pattern must be contiguous
        """
        self.digits = digits
        self.spacing = spacing
        
        # Validate
        if spacing is not None and len(spacing) != len(digits) - 1:
            raise ValueError("Spacing list must be one element shorter than digit list")
    
    @property
    def length(self) -> int:
        """Get the number of digits in the pattern."""
        return len(self.digits)
    
    @property
    def total_span(self) -> int:
        """
        Get the total span of the pattern including spacing.
        
        For contiguous patterns, this equals length.
        For patterns with spacing, it's the sum of all spacings + length.
        """
        if self.spacing is None:
            return self.length
        
        return self.length + sum(self.spacing)
    
    def is_contiguous(self) -> bool:
        """Check if the pattern is contiguous (no spacing)."""
        return self.spacing is None or all(s == 0 for s in self.spacing)
    
    def match_at_position(self, stream: np.ndarray, start_pos: int) -> Tuple[bool, int]:
        """
        Check if the pattern matches at a specific position in the stream.
        
        Args:
            stream: The synthetic stream to check
            start_pos: Starting position to check
        
        Returns:
            Tuple of (match_found, end_position):
            - match_found: True if pattern matches, False otherwise
            - end_position: Position immediately after the last digit of the pattern
                           (or -1 if no match)
        """
        if start_pos < 0 or start_pos >= len(stream):
            return False, -1
        
        # Handle contiguous pattern
        if self.is_contiguous():
            if start_pos + self.length > len(stream):
                return False, -1
            
            for i, digit in enumerate(self.digits):
                if stream[start_pos + i] != digit:
                    return False, -1
            
            return True, start_pos + self.length
        
        # Handle pattern with spacing
        current_pos = start_pos
        
        for i, digit in enumerate(self.digits):
            # Check if we're still within stream bounds
            if current_pos >= len(stream):
                return False, -1
            
            # Check digit match
            if stream[current_pos] != digit:
                return False, -1
            
            # Move to next position (if not the last digit)
            if i < len(self.digits) - 1:
                current_pos += 1 + self.spacing[i]
        
        # Return the position immediately after the last digit
        return True, current_pos + 1
    
    def to_dict(self) -> Dict:
        """
        Convert pattern to dictionary representation.
        
        Returns:
            Dictionary containing pattern information
        """
        return {
            "digits": self.digits,
            "spacing": self.spacing
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Pattern':
        """
        Create a pattern from dictionary representation.
        
        Args:
            data: Dictionary containing pattern information
        
        Returns:
            Pattern instance
        """
        return cls(
            digits=data["digits"],
            spacing=data.get("spacing")
        )
    
    def __str__(self) -> str:
        """String representation of the pattern."""
        if self.is_contiguous():
            return "".join(str(d) for d in self.digits)
        
        parts = []
        for i, digit in enumerate(self.digits):
            parts.append(str(digit))
            if i < len(self.spacing):
                parts.append(f"[{self.spacing[i]}]")
        
        return "".join(parts)


class PatternMatcher:
    """Finds and verifies patterns in synthetic streams."""
    
    def __init__(self, threads: int = None, follow_digits: int = 25):
        """
        Initialize the pattern matcher.
        
        Args:
            threads: Number of threads to use for parallel matching
            follow_digits: Number of digits to extract after the pattern match
        """
        self.threads = threads
        self.follow_digits = follow_digits
    
    def find_pattern(
        self,
        pattern: Pattern,
        stream: np.ndarray,
        max_positions: int = 5,
        start_from: int = 0
    ) -> List[Tuple[int, np.ndarray]]:
        """
        Find all occurrences of a pattern in a stream.
        
        Args:
            pattern: Pattern to search for
            stream: Synthetic stream to search in
            max_positions: Maximum number of positions to return
            start_from: Position to start searching from
        
        Returns:
            List of tuples (position, follow_sequence) where:
            - position: Starting position where the pattern was found
            - follow_sequence: Array of digits that follow the pattern
        """
        results = []
        
        # Use multi-threading for large streams
        if len(stream) > 10000 and self.threads not in (0, 1):
            results = self._find_pattern_parallel(
                pattern, stream, max_positions, start_from
            )
        else:
            # Sequential search
            results = self._find_pattern_sequential(
                pattern, stream, max_positions, start_from
            )
        
        # Sort results by position
        results.sort(key=lambda x: x[0])
        
        return results
    
    def _find_pattern_sequential(
        self,
        pattern: Pattern,
        stream: np.ndarray,
        max_positions: int,
        start_from: int
    ) -> List[Tuple[int, np.ndarray]]:
        """
        Find pattern occurrences sequentially.
        
        Args:
            pattern: Pattern to search for
            stream: Stream to search in
            max_positions: Maximum positions to find
            start_from: Starting position
        
        Returns:
            List of tuples (position, follow_sequence)
        """
        results = []
        
        for pos in range(start_from, len(stream) - pattern.length + 1):
            match_found, end_pos = pattern.match_at_position(stream, pos)
            
            if match_found:
                # Extract follow digits
                follow_seq = self._extract_follow_digits(stream, end_pos)
                
                # Add to results
                results.append((pos, follow_seq))
                
                if len(results) >= max_positions:
                    break
        
        return results
    
    def _find_pattern_parallel(
        self,
        pattern: Pattern,
        stream: np.ndarray,
        max_positions: int,
        start_from: int
    ) -> List[Tuple[int, np.ndarray]]:
        """
        Find pattern occurrences in parallel.
        
        Args:
            pattern: Pattern to search for
            stream: Stream to search in
            max_positions: Maximum positions to find
            start_from: Starting position
        
        Returns:
            List of tuples (position, follow_sequence)
        """
        # Determine thread count
        import multiprocessing
        threads = self.threads or max(1, multiprocessing.cpu_count() - 1)
        
        # Calculate chunk size for parallel processing
        stream_length = len(stream) - pattern.length + 1
        chunk_size = max(1000, stream_length // threads)
        
        chunks = [
            (max(start_from, i), min(i + chunk_size, stream_length))
            for i in range(start_from, stream_length, chunk_size)
        ]
        
        results = []
        
        with ThreadPoolExecutor(max_workers=threads) as executor:
            # Submit search tasks
            futures = [
                executor.submit(
                    self._search_chunk, pattern, stream, start, end, max_positions
                )
                for start, end in chunks
            ]
            
            # Process results as they complete
            for future in futures:
                chunk_results = future.result()
                results.extend(chunk_results)
                
                # Break early if we have enough positions
                if len(results) >= max_positions:
                    break
        
        # Sort and limit results
        results.sort(key=lambda x: x[0])
        return results[:max_positions]
    
    def _search_chunk(
        self,
        pattern: Pattern,
        stream: np.ndarray,
        start: int,
        end: int,
        max_positions: int
    ) -> List[Tuple[int, np.ndarray]]:
        """
        Search for pattern in a stream chunk.
        
        Args:
            pattern: Pattern to search for
            stream: Stream to search in
            start: Start position of chunk
            end: End position of chunk
            max_positions: Maximum positions to find
        
        Returns:
            List of tuples (position, follow_sequence)
        """
        results = []
        
        for pos in range(start, end):
            match_found, end_pos = pattern.match_at_position(stream, pos)
            
            if match_found:
                # Extract follow digits
                follow_seq = self._extract_follow_digits(stream, end_pos)
                
                # Add to results
                results.append((pos, follow_seq))
                
                if len(results) >= max_positions:
                    break
        
        return results
    
    def _extract_follow_digits(
        self,
        stream: np.ndarray,
        end_pos: int
    ) -> np.ndarray:
        """
        Extract digits following the pattern match.
        
        Args:
            stream: Stream to extract from
            end_pos: Position immediately after the pattern match
        
        Returns:
            Array of follow digits (may be shorter than follow_digits if at stream end)
        """
        # Calculate how many digits we can extract
        available = min(self.follow_digits, len(stream) - end_pos)
        
        if available <= 0:
            # Handle edge case where pattern ends at stream end
            return np.array([], dtype=np.uint8)
        
        # Extract digits
        follow_seq = stream[end_pos:end_pos + available]
        
        return follow_seq
    
    def verify_pattern_matches(
        self,
        pattern: Pattern,
        stream: np.ndarray,
        expected_results: List[Tuple[int, np.ndarray]]
    ) -> bool:
        """
        Verify that a pattern appears at the specified positions with the correct follow digits.
        
        Args:
            pattern: Pattern to verify
            stream: Stream to check in
            expected_results: List of expected (position, follow_sequence) tuples
        
        Returns:
            True if pattern matches at all positions with correct follow digits, False otherwise
        """
        for pos, expected_follow in expected_results:
            match_found, end_pos = pattern.match_at_position(stream, pos)
            
            if not match_found:
                return False
            
            # Extract follow digits
            actual_follow = self._extract_follow_digits(stream, end_pos)
            
            # Compare follow sequences
            if len(actual_follow) != len(expected_follow) or not np.array_equal(actual_follow, expected_follow):
                return False
        
        return True
    
    def hash_follow_sequences(self, follow_sequences: List[np.ndarray]) -> str:
        """
        Create a cryptographic hash of pattern follow sequences.
        
        Args:
            follow_sequences: List of digit sequences following pattern matches
        
        Returns:
            SHA-256 hash of follow sequences
        """
        # Convert sequences to string and concatenate
        seq_str = ""
        for seq in follow_sequences:
            seq_str += "".join(str(d) for d in seq) + "|"
        
        # Generate hash
        return hashlib.sha256(seq_str.encode()).hexdigest()
    
    def verify_follow_hash(
        self,
        follow_sequences: List[np.ndarray],
        expected_hash: str
    ) -> bool:
        """
        Verify that follow sequences match an expected hash.
        
        Args:
            follow_sequences: List of digit sequences to verify
            expected_hash: Expected SHA-256 hash
        
        Returns:
            True if hash matches, False otherwise
        """
        actual_hash = self.hash_follow_sequences(follow_sequences)
        return actual_hash == expected_hash


def generate_random_pattern(
    length: int = 3,
    max_spacing: int = 10,
    use_spacing: bool = True
) -> Pattern:
    """
    Generate a random pattern.
    
    Args:
        length: Number of digits in the pattern
        max_spacing: Maximum spacing between digits
        use_spacing: Whether to use spacing (if False, pattern is contiguous)
    
    Returns:
        Random Pattern instance
    """
    # Generate random digits
    digits = np.random.randint(0, 10, size=length).tolist()
    
    # Generate spacing if needed
    spacing = None
    if use_spacing and length > 1:
        spacing = np.random.randint(0, max_spacing + 1, size=length - 1).tolist()
    
    return Pattern(digits, spacing)


def get_pattern_matcher(threads: int = None, follow_digits: int = 25) -> PatternMatcher:
    """
    Get a pattern matcher instance.
    
    Args:
        threads: Number of threads to use
        follow_digits: Number of digits to extract after pattern match
    
    Returns:
        PatternMatcher instance
    """
    return PatternMatcher(threads, follow_digits)
