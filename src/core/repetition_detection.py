"""
Detect repeating patterns and calculate nadai directly from SSM
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from config.settings import MIN_REPETITIONS, PERIOD_TOLERANCE


class RepetitionDetector:
    """Detect repeating patterns and extract nadai from SSM"""

    def __init__(self, min_repetitions: int = MIN_REPETITIONS):
        self.min_repetitions = min_repetitions

    def analyze_repetition(self,
                           diagonal_lines: List[Dict],
                           ssm: np.ndarray,
                           times: np.ndarray) -> Dict:
        """
        Complete repetition analysis: find period, beats, and nadai

        Args:
            diagonal_lines: List of diagonal line segments from SSM
            ssm: Self-similarity matrix
            times: Time stamps

        Returns:
            Dictionary with period, num_beats, subdivisions_per_beat
        """
        if len(diagonal_lines) == 0:
            raise ValueError("No repetitions found in SSM")

        # Step 1: Find the phrase period from the strongest repetitions
        period = self._find_period(diagonal_lines)
        if period is None:
            raise ValueError("Could not determine phrase period")

        # Step 2: Find sub-patterns that are exact integer divisions
        # of the period, validated by SSM strength
        sub_patterns = self._find_sub_patterns(diagonal_lines, period)

        # Step 3: Determine beats and subdivisions from sub-pattern structure
        num_beats, subdivisions = self._determine_structure(period, sub_patterns)

        return {
            'period': period,
            'num_beats': num_beats,
            'subdivisions_per_beat': subdivisions,
            'sub_patterns': sub_patterns
        }

    def _find_period(self, diagonal_lines: List[Dict]) -> Optional[float]:
        """
        Find the dominant phrase period from diagonal lines

        Only uses strong repetitions and clusters their lag times
        to find the most consistent period.

        Args:
            diagonal_lines: Detected diagonal lines

        Returns:
            Period in seconds
        """
        lag_times = [
            line['lag_time'] for line in diagonal_lines
            if line['strength'] > 0.6 and line['duration'] > 0.5
        ]

        if len(lag_times) == 0:
            return None

        lag_times = np.array(lag_times)
        sorted_lags = np.sort(lag_times)

        # Cluster lag times that are within PERIOD_TOLERANCE of each other
        # This is where timing imprecision is handled - once, cleanly
        clusters = []
        current_cluster = [sorted_lags[0]]

        for lag in sorted_lags[1:]:
            if lag - current_cluster[-1] < PERIOD_TOLERANCE:
                current_cluster.append(lag)
            else:
                clusters.append(current_cluster)
                current_cluster = [lag]

        clusters.append(current_cluster)

        # The largest cluster is the most consistently detected period
        largest_cluster = max(clusters, key=len)

        return float(np.median(largest_cluster))

    def _find_sub_patterns(self,
                           diagonal_lines: List[Dict],
                           period: float) -> List[Dict]:
        """
        Find sub-patterns that are exact integer divisions of the period

        No tolerance needed here. If the period estimate is accurate
        (handled by _find_period), then valid sub-patterns will divide
        into it with negligible remainder. We use strength as the
        quality filter instead.

        Args:
            diagonal_lines: All detected diagonal lines
            period: Main phrase period

        Returns:
            List of valid sub-patterns with their division counts
        """
        # Group diagonal lines by their lag time using period tolerance
        # to handle slight timing variations in the same sub-pattern
        lag_groups = self._group_by_lag(diagonal_lines, period)

        sub_patterns = []

        for lag, lines in lag_groups.items():
            # Skip if this is the main period itself
            if abs(lag - period) < PERIOD_TOLERANCE:
                continue

            # Only consider lags shorter than the period
            if lag >= period:
                continue

            # Check if this lag is an exact integer division of the period
            divisions = period / lag

            # Valid only if very close to an integer
            # We use a tight threshold here (0.02) because the period
            # estimate is already accurate - this is just floating point cleanup
            if abs(divisions - round(divisions)) > 0.02:
                continue

            divisions = round(divisions)

            # Only meaningful musical divisions (2-16)
            if not (2 <= divisions <= 16):
                continue

            # Use average strength of all lines at this lag as quality metric
            avg_strength = np.mean([l['strength'] for l in lines])

            # Require a minimum strength - weak matches are noise
            if avg_strength < 0.5:
                continue

            sub_patterns.append({
                'period': lag,
                'divisions': divisions,
                'strength': avg_strength,
                'num_lines': len(lines)
            })

        # Sort by number of divisions (smallest first)
        sub_patterns.sort(key=lambda x: x['divisions'])

        return sub_patterns

    def _group_by_lag(self,
                      diagonal_lines: List[Dict],
                      period: float) -> Dict[float, List[Dict]]:
        """
        Group diagonal lines by similar lag times

        Uses PERIOD_TOLERANCE to cluster lines with nearly identical
        lags together, treating them as the same sub-pattern.

        Args:
            diagonal_lines: All detected diagonal lines
            period: Main phrase period (used to filter)

        Returns:
            Dictionary mapping representative lag -> list of lines
        """
        groups = {}

        for line in diagonal_lines:
            lag = line['lag_time']
            matched = False

            for existing_lag in list(groups.keys()):
                if abs(lag - existing_lag) < PERIOD_TOLERANCE:
                    groups[existing_lag].append(line)
                    matched = True
                    break

            if not matched:
                groups[lag] = [line]

        return groups

    def _determine_structure(self,
                             period: float,
                             sub_patterns: List[Dict]) -> Tuple[int, float]:
        """
        Determine number of beats and subdivisions per beat

        Tries to find the factorization of the sub-patterns that
        yields a known Carnatic nadai value.

        Args:
            period: Main phrase period
            sub_patterns: Validated sub-patterns from SSM

        Returns:
            (num_beats, subdivisions_per_beat)
        """
        common_beat_counts = [3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16]
        common_nadais = [3, 4, 5, 7, 9]

        if not sub_patterns:
            # No sub-patterns visible in SSM
            # Default: 8 beats of caturasra (most common in Carnatic music)
            return 8, 4.0

        # Strategy: The SSM gives us a hierarchy of repetitions.
        # The smallest division count is closest to the beat level.
        # The largest is closest to the phrase level.
        # We look for a pair (beat_count, nadai) where:
        #   beat_count × nadai = total_divisions

        total_divisions = sub_patterns[-1]['divisions']  # Largest division count

        # Try every combination of known beat counts and nadais
        # that multiply to total_divisions
        for nadai in common_nadais:
            if total_divisions % nadai == 0:
                beat_count = total_divisions // nadai
                if beat_count in common_beat_counts:
                    return beat_count, float(nadai)

        # Fallback: use the smallest sub-pattern as the beat
        # and infer nadai from the next level up
        if len(sub_patterns) >= 2:
            beat_divisions = sub_patterns[0]['divisions']
            sub_divisions = sub_patterns[1]['divisions']

            if sub_divisions % beat_divisions == 0:
                nadai = sub_divisions // beat_divisions
                if nadai in common_nadais:
                    return beat_divisions, float(nadai)

        # Last resort: smallest sub-pattern is the beat, assume caturasra
        return sub_patterns[0]['divisions'], 4.0