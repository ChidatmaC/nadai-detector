"""
Text report generation
"""

from typing import Dict, Any


def generate_report(result: Dict[str, Any], output_path: str):
    """Generate detailed text report"""
    report = generate_summary(result)
    
    with open(output_path, 'w') as f:
        f.write(report)
    
    print(f"Saved report to {output_path}")


def generate_summary(result: Dict[str, Any]) -> str:
    """Generate summary text"""
    summary = f"""
{'='*70}
                    NADAI DETECTION REPORT
{'='*70}

RESULT
------
Nadai Type:              {result['nadai_type'].upper()}
Nadai Value:             {result['nadai_value']} subdivisions per beat

TIMING STRUCTURE
----------------
Phrase Period:           {result['phrase_period']:.3f} seconds
Beat Duration:           {result['beat_duration']:.3f} seconds
Beats per Phrase:        {result['num_beats']}

TEMPO
-----
BPM (per beat):          {60/result['beat_duration']:.1f}
BPM (per phrase):        {60/result['phrase_period']:.1f}

ANALYSIS STATISTICS
-------------------
Repetitions Found:       {result['num_repetitions']}
Subdivisions per Beat:   {result['subdivisions_per_beat']:.2f}

AUDIO FILE
----------
File: {result['audio_file']}

{'='*70}

INTERPRETATION
--------------
This recording contains a rhythmic pattern in {result['nadai_type']} nadai,
with {result['nadai_value']} subdivisions per beat. The phrase repeats every
{result['phrase_period']:.3f} seconds, containing {result['num_beats']} beats.

{'='*70}
"""
    
    return summary