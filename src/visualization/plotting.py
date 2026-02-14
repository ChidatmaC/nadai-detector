"""
Visualization for SSM-based nadai detection
"""

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from config.settings import (
    PLOT_STYLE,
    FIGURE_DPI,
    COLORMAP_SSM,
    COLORMAP_LAG
)

try:
    plt.style.use(PLOT_STYLE)
except Exception:
    pass

# Cyan-like colormap for diagonal lines (plt.cm.cyan was removed in recent matplotlib)
_CMAP_CYAN = mcolors.LinearSegmentedColormap.from_list(
    'cyan', [(1, 1, 1, 0.4), (0, 1, 1, 1)], N=256
)


def visualize_complete_analysis(result: Dict[str, Any],
                                audio_path: str,
                                save_path: Optional[str] = None):
    """
    Create comprehensive visualization
    
    Args:
        result: Detection results from pipeline
        audio_path: Path to audio file
        save_path: Optional path to save figure
    """
    fig = plt.figure(figsize=(18, 10))
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
    
    # Plot 1: Self-Similarity Matrix
    ax1 = fig.add_subplot(gs[0, :2])
    plot_ssm(ax1, result)
    
    # Plot 2: Time-Lag Matrix
    ax2 = fig.add_subplot(gs[0, 2])
    plot_time_lag(ax2, result)
    
    # Plot 3: Sub-patterns
    ax3 = fig.add_subplot(gs[1, 0])
    plot_sub_patterns(ax3, result)
    
    # Plot 4: Diagonal Strength
    ax4 = fig.add_subplot(gs[1, 1])
    plot_diagonal_strength(ax4, result)
    
    # Plot 5: Summary
    ax5 = fig.add_subplot(gs[1, 2])
    plot_summary(ax5, result)
    
    # Title
    fig.suptitle(
        f"{result['nadai_type'].upper()} Nadai Detection - {Path(audio_path).name}",
        fontsize=16,
        fontweight='bold'
    )
    
    if save_path:
        plt.savefig(save_path, dpi=FIGURE_DPI, bbox_inches='tight')
        print(f"Saved visualization to {save_path}")
    else:
        plt.show()
    
    plt.close()


def plot_ssm(ax, result):
    """Plot SSM with diagonal lines"""
    ssm = result['ssm']
    times = result['times']
    diagonal_lines = result['diagonal_lines']
    
    im = ax.imshow(
        ssm,
        cmap=COLORMAP_SSM,
        origin='lower',
        extent=[times[0], times[-1], times[0], times[-1]],
        aspect='auto'
    )
    
    # Draw diagonal lines
    for line in diagonal_lines:
        start = line['start_time']
        end = line['end_time']
        lag = line['lag_time']
        strength = line['strength']
        
        color = _CMAP_CYAN(strength)
        ax.plot(
            [start, end],
            [start + lag, end + lag],
            color=color,
            linewidth=2,
            alpha=0.8
        )
    
    # Mark period
    period = result['phrase_period']
    for i in range(1, int(times[-1] / period) + 1):
        ax.axhline(y=i * period, color='yellow', linestyle='--', alpha=0.3)
        ax.axvline(x=i * period, color='yellow', linestyle='--', alpha=0.3)
    
    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('Time (s)', fontsize=12)
    ax.set_title('Self-Similarity Matrix', fontsize=14)
    
    plt.colorbar(im, ax=ax, label='Similarity')


def plot_time_lag(ax, result):
    """Plot time-lag matrix"""
    ssm = result['ssm']
    times = result['times']
    period = result['phrase_period']
    
    n = len(times)
    max_lag = min(300, n)
    
    lag_matrix = np.zeros((max_lag, n))
    for lag in range(max_lag):
        for i in range(n - lag):
            if i + lag < n:
                lag_matrix[lag, i] = ssm[i, i + lag]
    
    im = ax.imshow(
        lag_matrix,
        cmap=COLORMAP_LAG,
        origin='lower',
        extent=[times[0], times[-1], 0, times[min(max_lag-1, n-1)]],
        aspect='auto'
    )
    
    ax.axhline(y=period, color='cyan', linestyle='--', linewidth=2,
              label=f'Period = {period:.3f}s')
    
    ax.set_xlabel('Time (s)', fontsize=10)
    ax.set_ylabel('Lag (s)', fontsize=10)
    ax.set_title('Time-Lag Matrix', fontsize=12)
    ax.legend(fontsize=9)
    
    plt.colorbar(im, ax=ax, label='Similarity')


def plot_sub_patterns(ax, result):
    """Plot detected sub-patterns"""
    sub_patterns = result.get('sub_patterns', [])
    
    if not sub_patterns:
        ax.text(0.5, 0.5, 'No sub-patterns detected', 
               ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Sub-patterns')
        return
    
    periods = [sp['period'] for sp in sub_patterns]
    divisions = [sp['divisions'] for sp in sub_patterns]
    strengths = [sp['strength'] for sp in sub_patterns]
    
    scatter = ax.scatter(periods, divisions, s=np.array(strengths)*500, 
                        c=strengths, cmap='viridis', alpha=0.7, edgecolors='black')
    
    ax.set_xlabel('Period (s)', fontsize=10)
    ax.set_ylabel('Divisions', fontsize=10)
    ax.set_title('Sub-patterns', fontsize=12)
    ax.grid(alpha=0.3)
    
    plt.colorbar(scatter, ax=ax, label='Strength')


def plot_diagonal_strength(ax, result):
    """Plot diagonal line strengths"""
    diagonal_lines = result['diagonal_lines']
    
    if not diagonal_lines:
        ax.text(0.5, 0.5, 'No diagonals', ha='center', va='center')
        return
    
    lags = [line['lag_time'] for line in diagonal_lines]
    strengths = [line['strength'] for line in diagonal_lines]
    
    ax.scatter(lags, strengths, alpha=0.6)
    
    # Mark main period
    period = result['phrase_period']
    ax.axvline(x=period, color='red', linestyle='--', label=f'Period = {period:.3f}s')
    
    ax.set_xlabel('Lag Time (s)', fontsize=10)
    ax.set_ylabel('Strength', fontsize=10)
    ax.set_title('Diagonal Line Strength', fontsize=12)
    ax.legend()
    ax.grid(alpha=0.3)


def plot_summary(ax, result):
    """Plot summary statistics"""
    ax.axis('off')
    
    summary_text = f"""
ANALYSIS SUMMARY
{'='*30}

Nadai Type: {result['nadai_type'].upper()}
Nadai Value: {result['nadai_value']}

Phrase Period: {result['phrase_period']:.3f} s
Beat Duration: {result['beat_duration']:.3f} s
Beats per Phrase: {result['num_beats']}

Subdivisions/Beat: {result['subdivisions_per_beat']:.2f}
Repetitions Found: {result['num_repetitions']}

Tempo (BPM): {60/result['beat_duration']:.1f}
    """
    
    ax.text(
        0.1, 0.9,
        summary_text,
        transform=ax.transAxes,
        fontsize=11,
        verticalalignment='top',
        fontfamily='monospace',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )