"""
Basic usage example
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from .pipeline import NadaiDetectionPipeline


def main():
    # Your audio file
    audio_file = 'data/input/my_rhythm_track.wav'
    
    # Create pipeline
    pipeline = NadaiDetectionPipeline(verbose=True)
    
    # Detect
    result = pipeline.detect(audio_file)
    
    # Results
    print(f"\n{'='*60}")
    print("RESULTS:")
    print(f"{'='*60}")
    print(f"Nadai: {result['nadai_type'].upper()} ({result['nadai_value']})")
    print(f"Period: {result['phrase_period']:.3f}s")
    print(f"Beats: {result['num_beats']}")
    print(f"BPM: {60/result['beat_duration']:.1f}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()