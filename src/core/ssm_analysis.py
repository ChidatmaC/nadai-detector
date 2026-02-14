"""
Self-similarity matrix computation and analysis
"""

import numpy as np
from scipy.spatial.distance import pdist, squareform
from scipy.ndimage import uniform_filter
from scipy import signal
from typing import List, Dict, Optional
import librosa


class SSMAnalyzer:
    """Compute and analyze self-similarity matrices"""
    
    def __init__(self, metric: str = 'cosine'):
        """
        Args:
            metric: Distance metric ('cosine', 'euclidean', 'correlation')
        """
        self.metric = metric
        
    def compute_ssm(self, features: np.ndarray, normalize: bool = True) -> np.ndarray:
        """
        Compute self-similarity matrix
        
        Args:
            features: Feature matrix (n_features x n_frames)
            normalize: Whether to normalize features
            
        Returns:
            Self-similarity matrix (n_frames x n_frames)
        """
        # Normalize features column-wise
        if normalize:
            features = librosa.util.normalize(features, axis=0)
        
        # Transpose to (n_frames x n_features)
        features = features.T
        
        # Compute pairwise distances
        distances = pdist(features, metric=self.metric)
        
        # Convert to square matrix
        distance_matrix = squareform(distances)
        
        # Convert distances to similarities
        if self.metric == 'cosine':
            similarity_matrix = 1 - distance_matrix
        elif self.metric == 'correlation':
            similarity_matrix = 1 - distance_matrix
        else:  # euclidean
            # Normalize to [0, 1] range
            max_dist = distance_matrix.max()
            if max_dist > 0:
                similarity_matrix = 1 - (distance_matrix / max_dist)
            else:
                similarity_matrix = np.ones_like(distance_matrix)
        
        return similarity_matrix
    
    def enhance_ssm(self, ssm: np.ndarray, filter_width: int = 5) -> np.ndarray:
        """
        Enhance SSM using smoothing to make diagonal structures clearer
        
        Args:
            ssm: Self-similarity matrix
            filter_width: Width of smoothing filter
            
        Returns:
            Enhanced SSM
        """
        enhanced = np.copy(ssm)
        
        # Smooth along both axes
        enhanced = uniform_filter(enhanced, size=(filter_width, 1))
        enhanced = uniform_filter(enhanced, size=(1, filter_width))
        
        return enhanced
    
    def compute_time_lag_matrix(self, ssm: np.ndarray, times: np.ndarray) -> np.ndarray:
        """
        Compute time-lag representation of SSM
        
        Args:
            ssm: Self-similarity matrix
            times: Time stamps
            
        Returns:
            Time-lag matrix where rows are lags, columns are time positions
        """
        n = len(times)
        max_lag = n
        
        lag_matrix = np.zeros((max_lag, n))
        
        for lag in range(max_lag):
            for i in range(n - lag):
                lag_matrix[lag, i] = ssm[i, i + lag]
        
        return lag_matrix
    
    def find_diagonal_lines(self, 
                           ssm: np.ndarray, 
                           times: np.ndarray,
                           min_length: float = 0.5,
                           threshold: float = 0.7) -> List[Dict]:
        """
        Find diagonal lines in SSM indicating repetitions
        
        Args:
            ssm: Self-similarity matrix
            times: Time stamps
            min_length: Minimum duration of repetition (seconds)
            threshold: Similarity threshold
            
        Returns:
            List of diagonal line segments with metadata
        """
        n = ssm.shape[0]
        dt = np.mean(np.diff(times))  # Average time step
        min_frames = int(min_length / dt)
        
        diagonal_lines = []
        
        # Search for diagonal lines at each lag
        for lag in range(1, n):
            current_line = []
            
            for i in range(n - lag):
                if ssm[i, i + lag] > threshold:
                    current_line.append(i)
                else:
                    # End of line, check if long enough
                    if len(current_line) >= min_frames:
                        diagonal_lines.append(self._create_line_dict(
                            current_line, lag, times, ssm
                        ))
                    current_line = []
            
            # Check final line
            if len(current_line) >= min_frames:
                diagonal_lines.append(self._create_line_dict(
                    current_line, lag, times, ssm
                ))
        
        return diagonal_lines
    
    def _create_line_dict(self, 
                         line_indices: List[int], 
                         lag: int, 
                         times: np.ndarray,
                         ssm: np.ndarray) -> Dict:
        """Create dictionary with line metadata"""
        start_idx = line_indices[0]
        end_idx = line_indices[-1]
        
        return {
            'start_time': times[start_idx],
            'end_time': times[end_idx],
            'duration': times[end_idx] - times[start_idx],
            'lag': lag,
            'lag_time': times[lag] - times[0],
            'strength': np.mean(ssm[line_indices, np.array(line_indices) + lag])
        }


def compute_ssm(features: np.ndarray, **kwargs) -> np.ndarray:
    """
    Convenience function for SSM computation
    
    Args:
        features: Feature matrix
        **kwargs: Additional arguments for SSMAnalyzer
        
    Returns:
        Self-similarity matrix
    """
    analyzer = SSMAnalyzer(**kwargs)
    return analyzer.compute_ssm(features)