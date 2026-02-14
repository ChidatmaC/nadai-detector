"""
Simplified pipeline for SSM-based nadai detection
"""

import numpy as np
from typing import Dict, Any, Optional
from pathlib import Path
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.settings import *
from core.feature_extraction import extract_features
from core.ssm_analysis import SSMAnalyzer
from core.repetition_detection import RepetitionDetector
from core.nadai_classifier import classify_nadai
from visualization.plotting import visualize_complete_analysis
from visualization.reports import generate_report
from utils.validation import validate_audio_file


class NadaiDetectionPipeline:
    """
    SSM-based nadai detection pipeline
    """
    
    def __init__(self, verbose: bool = VERBOSE):
        self.verbose = verbose
        self.ssm_analyzer = SSMAnalyzer(metric=SSM_METRIC)
        self.rep_detector = RepetitionDetector(min_repetitions=MIN_REPETITIONS)
        
    def detect(self, audio_path: str) -> Dict[str, Any]:
        """
        Run complete detection pipeline
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with analysis results
        """
        # Validate
        validate_audio_file(audio_path)
        
        # Stage 1: Feature Extraction
        self._log("="*60)
        self._log("STAGE 1: FEATURE EXTRACTION")
        self._log("="*60)
        
        features, times = extract_features(
            audio_path,
            feature_type=FEATURE_TYPE
        )
        
        self._log(f"✓ Extracted {features.shape[0]} features")
        self._log(f"✓ {features.shape[1]} time frames")
        self._log(f"✓ Resolution: {np.mean(np.diff(times)):.4f}s per frame")
        
        # Stage 2: SSM Computation
        self._log("\n" + "="*60)
        self._log("STAGE 2: SELF-SIMILARITY MATRIX")
        self._log("="*60)
        
        ssm = self.ssm_analyzer.compute_ssm(features, normalize=SSM_NORMALIZE)
        
        self._log(f"✓ SSM shape: {ssm.shape}")
        self._log(f"✓ Metric: {SSM_METRIC}")
        
        if SSM_ENHANCE:
            ssm = self.ssm_analyzer.enhance_ssm(ssm, filter_width=SSM_FILTER_WIDTH)
            self._log(f"✓ Enhanced with filter width {SSM_FILTER_WIDTH}")
        
        # Stage 3: Find Diagonal Lines
        self._log("\n" + "="*60)
        self._log("STAGE 3: DETECTING REPETITIONS")
        self._log("="*60)
        
        diagonal_lines = self.ssm_analyzer.find_diagonal_lines(
            ssm,
            times,
            min_length=MIN_REPETITION_DURATION,
            threshold=REPETITION_THRESHOLD
        )
        
        self._log(f"✓ Found {len(diagonal_lines)} diagonal lines")
        
        if len(diagonal_lines) > 0:
            sorted_lines = sorted(
                diagonal_lines,
                key=lambda x: x['strength'],
                reverse=True
            )[:3]
            
            self._log("\nStrongest repetitions:")
            for i, line in enumerate(sorted_lines, 1):
                self._log(f"  {i}. Period: {line['lag_time']:.3f}s, "
                         f"Strength: {line['strength']:.2f}")
        
        # Stage 4: Analyze Repetition Structure
        self._log("\n" + "="*60)
        self._log("STAGE 4: ANALYZING RHYTHM STRUCTURE")
        self._log("="*60)
        
        structure = self.rep_detector.analyze_repetition(
            diagonal_lines,
            ssm,
            times
        )
        
        period = structure['period']
        num_beats = structure['num_beats']
        subdivisions_per_beat = structure['subdivisions_per_beat']
        
        self._log(f"✓ Phrase period: {period:.3f}s")
        self._log(f"✓ Beats per phrase: {num_beats}")
        self._log(f"✓ Subdivisions per beat: {subdivisions_per_beat:.2f}")
        
        if structure['sub_patterns']:
            self._log(f"\nDetected sub-patterns:")
            for sp in structure['sub_patterns'][:3]:
                self._log(f"  Period: {sp['period']:.3f}s, "
                         f"Divisions: {sp['divisions']}, "
                         f"Strength: {sp['strength']:.2f}")
        
        # Stage 5: Classify Nadai
        self._log("\n" + "="*60)
        self._log("STAGE 5: NADAI CLASSIFICATION")
        self._log("="*60)
        
        nadai_type, nadai_value = classify_nadai(subdivisions_per_beat)
        
        self._log(f"✓ Nadai type: {nadai_type.upper()}")
        self._log(f"✓ Nadai value: {nadai_value}")
        
        # Final Result
        self._log("\n" + "="*60)
        self._log("FINAL RESULT")
        self._log("="*60)
        self._log(f"🎵 {nadai_type.upper()} NADAI")
        self._log(f"   {nadai_value} subdivisions per beat")
        self._log(f"   {num_beats} beats per phrase")
        self._log(f"   {period:.3f}s phrase duration")
        self._log("="*60 + "\n")
        
        # Compile results
        beat_duration = period / num_beats
        
        return {
            'nadai_type': nadai_type,
            'nadai_value': int(nadai_value),
            'subdivisions_per_beat': float(subdivisions_per_beat),
            'beat_duration': float(beat_duration),
            'phrase_period': float(period),
            'num_beats': int(num_beats),
            'num_repetitions': len(diagonal_lines),
            'audio_file': str(audio_path),
            
            # Detailed data
            'ssm': ssm,
            'times': times,
            'features': features,
            'diagonal_lines': diagonal_lines,
            'sub_patterns': structure['sub_patterns']
        }
    
    def detect_and_save(self, 
                       audio_path: str, 
                       output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Detect nadai and save results
        
        Args:
            audio_path: Path to audio file
            output_dir: Directory to save outputs
            
        Returns:
            Detection results
        """
        result = self.detect(audio_path)
        
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            audio_name = Path(audio_path).stem
            
            # Save JSON
            if OUTPUT_JSON:
                json_path = output_path / 'json' / f'{audio_name}_result.json'
                json_path.parent.mkdir(exist_ok=True)
                
                json_result = {k: v for k, v in result.items() 
                              if k not in ['ssm', 'times', 'features', 'diagonal_lines', 'sub_patterns']}
                
                with open(json_path, 'w') as f:
                    json.dump(json_result, f, indent=2)
                self._log(f"\nSaved JSON to: {json_path}")
            
            # Save plot
            if OUTPUT_PLOT:
                plot_path = output_path / 'plots' / f'{audio_name}_analysis.png'
                plot_path.parent.mkdir(exist_ok=True)
                visualize_complete_analysis(result, str(audio_path), save_path=str(plot_path))
                self._log(f"Saved plot to: {plot_path}")
            
            # Save report
            if OUTPUT_REPORT:
                report_path = output_path / 'reports' / f'{audio_name}_report.txt'
                report_path.parent.mkdir(exist_ok=True)
                generate_report(result, str(report_path))
                self._log(f"Saved report to: {report_path}")
        
        return result
    
    def _log(self, message: str):
        """Log message if verbose"""
        if self.verbose:
            print(message)


def main():
    """Command-line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Detect nadai in Carnatic rhythm tracks using SSM'
    )
    parser.add_argument('audio_file', help='Path to audio file')
    parser.add_argument('-o', '--output', help='Output directory', default='data/output')
    parser.add_argument('-q', '--quiet', action='store_true', help='Suppress output')
    
    args = parser.parse_args()
    
    pipeline = NadaiDetectionPipeline(verbose=not args.quiet)
    
    try:
        result = pipeline.detect_and_save(args.audio_file, args.output)
        print(f"\n✓ Detection complete: {result['nadai_type'].upper()} nadai")
        return 0
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())