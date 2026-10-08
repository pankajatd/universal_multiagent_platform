import os
from typing import List, Dict, Any

# Root paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "src", "data")
MANUALS_DIR = os.path.join(DATA_DIR, "manuals")
MODELS_DIR = os.path.join(DATA_DIR, "models")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

# LLM Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

# Defect Classes
DEFECT_CLASSES = ["normal", "scratch", "crack", "corrosion", "dimensional"]

# Feature Vector Specification (21 features)
EXPECTED_FEATURES = [
    "contour_count", "total_area", "mean_area", "max_area", "mean_aspect_ratio",
    "mean_extent", "mean_solidity", "mean_eccentricity", "mean_intensity",
    "std_intensity", "intensity_range", "hu_1", "hu_2", "hu_3", "hu_4", "hu_5",
    "hu_6", "hu_7", "glcm_contrast", "glcm_dissimilarity", "glcm_homogeneity"
]

# Statistical Priors for Feature Healing (Default Fallbacks when features are missing/corrupted)
FEATURE_PRIORS = {
    "contour_count": 1.0,
    "total_area": 1200.0,
    "mean_area": 1200.0,
    "max_area": 1200.0,
    "mean_aspect_ratio": 2.5,
    "mean_extent": 0.45,
    "mean_solidity": 0.65,
    "mean_eccentricity": 0.75,
    "mean_intensity": 115.0,
    "std_intensity": 28.0,
    "intensity_range": 160.0,
    "hu_1": 0.002,
    "hu_2": 0.00001,
    "hu_3": 0.000001,
    "hu_4": 0.0000001,
    "hu_5": 0.0,
    "hu_6": 0.0,
    "hu_7": 0.0,
    "glcm_contrast": 45.0,
    "glcm_dissimilarity": 5.0,
    "glcm_homogeneity": 0.4
}

# Image Quality Thresholds
MIN_LAPLACIAN_VARIANCE = 45.0   # Below this = blurry image
MIN_CONTRAST_STD = 10.0         # Below this = washed out / flat illumination
MAX_BRIGHTNESS_MEAN = 245.0     # Above this = overexposed / glare
MIN_BRIGHTNESS_MEAN = 15.0      # Below this = pitch dark

# Severity Thresholds
SEVERITY_PASS_MAX = 0.0
SEVERITY_LOW_MAX = 4.0
SEVERITY_MEDIUM_MAX = 7.5

# RAG Relevance Threshold (TF-IDF cosine similarity range is typically 0.15 - 0.45)
MIN_RAG_RELEVANCE = 0.20
MAX_AGENT_RETRIES = 2
