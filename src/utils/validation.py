"""
Input validation utilities
"""

from pathlib import Path
from typing import Dict, Any
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from config.settings import (
    MIN_AUDIO_DURATION,
    MAX_AUDIO_DURATION,
    SUPPORTED_AUDIO_FORMATS
)
from .audio_io import get_audio_info


def validate_audio_file(audio_path: str) -> bool:
    """
    Validate audio file
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If file is invalid
    """
    path = Path(audio_path)
    
    # Check file exists
    if not path.exists():
        raise ValueError(f"Audio file not found: {audio_path}")

    # Check file extension
    if path.suffix.lower() not in SUPPORTED_AUDIO_FORMATS:
        raise ValueError(
            f"Unsupported audio format: {path.suffix}. "
            f"Supported formats: {SUPPORTED_AUDIO_FORMATS}"
        )
    
    # Check duration
    try:
        info = get_audio_info(audio_path)
        duration = info['duration']
        
        if duration < MIN_AUDIO_DURATION:
            raise ValueError(
                f"Audio too short: {duration:.2f}s. "
                f"Minimum: {MIN_AUDIO_DURATION}s"
            )
        
        if duration > MAX_AUDIO_DURATION:
            raise ValueError(
                f"Audio too long: {duration:.2f}s. "
                f"Maximum: {MAX_AUDIO_DURATION}s"
            )
    except Exception as e:
        raise ValueError(f"Error reading audio file: {e}")
    
    return True


def validate_result(result: Dict[str, Any]) -> bool:
    """
    Validate detection result
    
    Args:
        result: Detection result dictionary
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If result is invalid
    """
    required_keys = [
        'nadai_type',
        'nadai_value',
        'subdivisions_per_beat',
        'beat_duration',
        'phrase_period',
        'fundamental_unit',
        'num_beats'
    ]
    
    for key in required_keys:
        if key not in result:
            raise ValueError(f"Missing required key in result: {key}")
    
    # Validate ranges
    if result['phrase_period'] <= 0:
        raise ValueError("Invalid phrase_period: must be positive")
    
    if result['beat_duration'] <= 0:
        raise ValueError("Invalid beat_duration: must be positive")
    
    if result['num_beats'] <= 0:
        raise ValueError("Invalid num_beats: must be positive")
    
    if result['nadai_value'] <= 0:
        raise ValueError("Invalid nadai_value: must be positive")
    
    return True