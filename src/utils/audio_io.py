"""
Audio input/output utilities
"""

import librosa
import soundfile as sf
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Any
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from config.settings import SAMPLE_RATE


def load_audio(audio_path: str, sr: int = SAMPLE_RATE) -> Tuple[np.ndarray, int]:
    """
    Load audio file
    
    Args:
        audio_path: Path to audio file
        sr: Target sample rate
        
    Returns:
        (audio_data, sample_rate)
    """
    y, sr = librosa.load(audio_path, sr=sr)
    return y, sr


def save_audio(audio_path: str, y: np.ndarray, sr: int = SAMPLE_RATE):
    """
    Save audio to file
    
    Args:
        audio_path: Output path
        y: Audio data
        sr: Sample rate
    """
    sf.write(audio_path, y, sr)


def get_audio_info(audio_path: str) -> Dict[str, Any]:
    """
    Get audio file information.
    Tries soundfile first; falls back to loading with librosa if the format
    is not recognised (e.g. some WAV encodings unsupported by libsndfile).
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Dictionary with audio metadata (duration, sample_rate, channels, format, subtype)
    """
    try:
        info = sf.info(audio_path)
        return {
            'duration': info.duration,
            'sample_rate': info.samplerate,
            'channels': info.channels,
            'format': info.format,
            'subtype': info.subtype,
        }
    except Exception as sf_err:
        # Fallback: load with librosa (uses audioread when needed) to get duration/sr
        try:
            y, sr = librosa.load(audio_path, sr=None)
            duration = len(y) / sr
            return {
                'duration': duration,
                'sample_rate': sr,
                'channels': 1,
                'format': 'UNKNOWN',
                'subtype': 'PCM_16',
            }
        except Exception as lr_err:
            raise OSError(
                f"Could not read audio file. soundfile: {sf_err}. librosa: {lr_err}. "
                "Try re-exporting as standard PCM WAV or use .flac / .ogg."
            ) from lr_err