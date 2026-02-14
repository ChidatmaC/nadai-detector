"""
Configuration settings for nadai detection using SSM methodology
"""

# ==================== AUDIO PROCESSING ====================
SAMPLE_RATE = 22050
HOP_LENGTH = 512  # ~23ms at 22050 Hz

# ==================== ONSET DETECTION ====================
ONSET_DETECTION_METHODS = ['spectral_flux', 'hfc', 'complex']
ONSET_THRESHOLD = 0.05  # 50ms merge threshold for duplicate onsets
ONSET_BACKTRACK = True

# ==================== FEATURE EXTRACTION ====================
# Feature types: 'mfcc', 'chroma', 'tempogram', 'combined'
FEATURE_TYPE = 'combined'
N_MFCC = 13
N_MELS = 40
N_CHROMA = 12

# ==================== SELF-SIMILARITY MATRIX ====================
SSM_METRIC = 'cosine'  # 'cosine', 'euclidean', 'correlation'
SSM_FEATURE_TYPE = 'combined'  # 'mfcc', 'chroma', 'tempogram', 'combined'
SSM_NORMALIZE = True
SSM_ENHANCE = True
SSM_FILTER_WIDTH = 5

# ==================== REPETITION DETECTION ====================
MIN_REPETITION_DURATION = 0.5  # seconds
REPETITION_THRESHOLD = 0.7  # similarity threshold (0-1)
MIN_REPETITIONS = 3  # minimum number of repetitions to confirm pattern
PERIOD_TOLERANCE = 0.1  # tolerance for period clustering (seconds)
PERIOD_MIN = 0.5  # minimum phrase duration (seconds)
PERIOD_MAX = 10.0  # maximum phrase duration (seconds)

# ==================== SEGMENTATION ====================
SEGMENTATION_TOLERANCE = 0.1  # seconds

# ==================== INTERVAL ANALYSIS ====================
IOI_TOLERANCE_MS = 10  # milliseconds tolerance for GCD calculation
IOI_METHOD = 'hybrid'  # 'gcd', 'histogram', 'hybrid'
HISTOGRAM_BINS = 50

# ==================== BEAT DETECTION ====================
COMMON_BEAT_COUNTS = [3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16]
DEFAULT_BEAT_COUNTS = [8, 4]

# ==================== NADAI CLASSIFICATION ====================
NADAI_DEFINITIONS = {
    'tisra': {
        'base': 3,
        'multiples': [3, 6, 12, 24, 48]
    },
    'caturasra': {
        'base': 4,
        'multiples': [2, 4, 8, 16, 32, 64]
    },
    'khanda': {
        'base': 5,
        'multiples': [5, 10, 20, 40, 80]
    },
    'misra': {
        'base': 7,
        'multiples': [7, 14, 28, 56, 112]
    },
    'sankirna': {
        'base': 9,
        'multiples': [9, 18, 36, 72, 144]
    }
}

# ==================== VISUALIZATION ====================
PLOT_STYLE = 'seaborn-v0_8-darkgrid'
FIGURE_DPI = 150
MAX_PHRASES_TO_PLOT = 10
COLORMAP_SSM = 'hot'
COLORMAP_SIMILARITY = 'YlOrRd'
COLORMAP_LAG = 'viridis'

# ==================== OUTPUT ====================
OUTPUT_JSON = True
OUTPUT_PLOT = True
OUTPUT_REPORT = True
VERBOSE = True

# ==================== VALIDATION ====================
MIN_AUDIO_DURATION = 2.0  # seconds
MAX_AUDIO_DURATION = 600.0  # seconds (10 minutes)
SUPPORTED_AUDIO_FORMATS = ['.wav', '.mp3', '.flac', '.ogg', '.aiff']