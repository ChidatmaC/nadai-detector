"""
Nadai classification based on subdivisions per beat
"""

from typing import Tuple
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from config.settings import NADAI_DEFINITIONS


def classify_nadai(subdivisions_per_beat: float) -> Tuple[str, int]:
    """
    Classify nadai type based on number of subdivisions
    
    Args:
        subdivisions_per_beat: Number of subdivisions per beat
        
    Returns:
        (nadai_name, nadai_value)
    """
    n = round(subdivisions_per_beat)
    
    # Check exact matches
    for nadai_name, definition in NADAI_DEFINITIONS.items():
        if n in definition['multiples']:
            return nadai_name, n
    
    # Check divisibility with priority
    if n % 9 == 0:
        return 'sankirna', n
    
    if n % 7 == 0:
        return 'misra', n
    
    if n % 5 == 0:
        return 'khanda', n
    
    if n % 3 == 0 and not _is_power_of_2(n):
        return 'tisra', n
    
    if _is_power_of_2(n) or n % 4 == 0:
        return 'caturasra', n
    
    return 'unknown', n


def _is_power_of_2(n: int) -> bool:
    """Check if n is a power of 2"""
    return n > 0 and (n & (n - 1)) == 0