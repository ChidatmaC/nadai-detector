"""
Feature extraction for self-similarity matrix computation
"""

import librosa
import numpy as np
from typing import Tuple, Optional
import sys
import os

# Add parent directory to path for config import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from config.settings import SAMPLE_RATE, HOP_LENGTH, N_MFCC, N_MELS


class FeatureExtractor:
    """Extract audio features for similarity analysis"""
    
    def __init__(self, sr: int = SAMPLE_RATE, hop_length: int = HOP_LENGTH):
        self.sr = sr
        self.hop_length = hop_length
        
    def extract(self, audio_path: str, feature_type: str = 'combined') -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract features from audio
        
        Args:
            audio_path: Path to audio file
            feature_type: Type of features ('mfcc', 'chroma', 'tempogram', 'combined')
            
        Returns:
            features: Feature matrix (n_features x n_frames)
            times: Time stamps for each frame
        """
        y, sr = librosa.load(audio_path, sr=self.sr)
        
        if feature_type == 'mfcc':
            features = self._extract_mfcc(y, sr)
        elif feature_type == 'chroma':
            features = self._extract_chroma(y, sr)
        elif feature_type == 'tempogram':
            features = self._extract_tempogram(y, sr)
        elif feature_type == 'combined':
            features = self._extract_combined(y, sr)
        else:
            raise ValueError(f"Unknown feature type: {feature_type}")
        
        # Get time stamps
        times = librosa.frames_to_time(
            np.arange(features.shape[1]),
            sr=sr,
            hop_length=self.hop_length
        )
        
        return features, times
    
    def _extract_mfcc(self, y: np.ndarray, sr: int) -> np.ndarray:
        """Extract MFCC features with deltas"""
        mfcc = librosa.feature.mfcc(
            y=y,
            sr=sr,
            n_mfcc=N_MFCC,
            hop_length=self.hop_length
        )
        # Delta features for temporal dynamics
        mfcc_delta = librosa.feature.delta(mfcc)
        return np.vstack([mfcc, mfcc_delta])
    
    def _extract_chroma(self, y: np.ndarray, sr: int) -> np.ndarray:
        """Extract chroma features"""
        chroma = librosa.feature.chroma_cqt(
            y=y,
            sr=sr,
            hop_length=self.hop_length
        )
        return chroma
    
    def _extract_tempogram(self, y: np.ndarray, sr: int) -> np.ndarray:
        """Extract tempogram (rhythmic features)"""
        # Onset strength
        oenv = librosa.onset.onset_strength(
            y=y,
            sr=sr,
            hop_length=self.hop_length
        )
        
        # Tempogram
        tempogram = librosa.feature.tempogram(
            onset_envelope=oenv,
            sr=sr,
            hop_length=self.hop_length
        )
        
        return tempogram
    
    def _extract_combined(self, y: np.ndarray, sr: int) -> np.ndarray:
        """Extract combined features optimized for rhythm analysis"""
        
        # Mel spectrogram for overall timbre
        mel_spec = librosa.feature.melspectrogram(
            y=y,
            sr=sr,
            hop_length=self.hop_length,
            n_mels=N_MELS
        )
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        
        # Spectral contrast for percussive character
        spectral_contrast = librosa.feature.spectral_contrast(
            y=y,
            sr=sr,
            hop_length=self.hop_length
        )
        
        # Onset strength for rhythmic timing
        oenv = librosa.onset.onset_strength(
            y=y,
            sr=sr,
            hop_length=self.hop_length
        )
        oenv = oenv.reshape(1, -1)
        
        # Combine all features
        features = np.vstack([
            mel_spec_db,
            spectral_contrast,
            oenv
        ])
        
        return features


def extract_features(
    audio_path: str,
    feature_type: str = 'combined',
    **kwargs
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Convenience function for feature extraction
    
    Args:
        audio_path: Path to audio file
        feature_type: Type of features ('mfcc', 'chroma', 'tempogram', 'combined')
        **kwargs: Additional arguments for FeatureExtractor (e.g. sr, hop_length)
        
    Returns:
        features, times
    """
    extractor = FeatureExtractor(**kwargs)
    return extractor.extract(audio_path, feature_type=feature_type)