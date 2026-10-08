import cv2
import numpy as np
from typing import Dict, Any, Tuple
from skimage.feature import graycomatrix, graycoprops
from src.config import EXPECTED_FEATURES, FEATURE_PRIORS

def extract_features(preprocessed_bgr: np.ndarray, mask: np.ndarray) -> Dict[str, float]:
    """
    Extracts 21-dimensional geometric, intensity, Hu moment, and texture features.
    """
    features: Dict[str, float] = {}
    gray = cv2.cvtColor(preprocessed_bgr, cv2.COLOR_BGR2GRAY)

    # 1. Contour Geometry Features
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    valid_contours = [c for c in contours if cv2.contourArea(c) > 10]
    contour_count = len(valid_contours)
    features["contour_count"] = float(contour_count)

    if contour_count > 0:
        areas = [cv2.contourArea(c) for c in valid_contours]
        features["total_area"] = float(sum(areas))
        features["mean_area"] = float(np.mean(areas))
        features["max_area"] = float(max(areas))

        aspect_ratios = []
        extents = []
        solidities = []
        eccentricities = []

        for c in valid_contours:
            _, _, w, h = cv2.boundingRect(c)
            aspect_ratios.append(float(w) / (h + 1e-5))

            rect_area = (w * h) + 1e-5
            extents.append(cv2.contourArea(c) / rect_area)

            hull = cv2.convexHull(c)
            hull_area = cv2.contourArea(hull) + 1e-5
            solidities.append(cv2.contourArea(c) / hull_area)

            if len(c) >= 5:
                (x, y), (MA, ma), angle = cv2.fitEllipse(c)
                a = max(MA, ma) / 2.0
                b = min(MA, ma) / 2.0
                ecc = np.sqrt(max(0.0, 1.0 - (b ** 2) / (a ** 2 + 1e-5)))
                eccentricities.append(float(ecc))
            else:
                eccentricities.append(0.5)

        features["mean_aspect_ratio"] = float(np.mean(aspect_ratios))
        features["mean_extent"] = float(np.mean(extents))
        features["mean_solidity"] = float(np.mean(solidities))
        features["mean_eccentricity"] = float(np.mean(eccentricities))
    else:
        features["total_area"] = 0.0
        features["mean_area"] = 0.0
        features["max_area"] = 0.0
        features["mean_aspect_ratio"] = 1.0
        features["mean_extent"] = 0.0
        features["mean_solidity"] = 0.0
        features["mean_eccentricity"] = 0.0

    # 2. Intensity Statistics
    masked_pixels = gray[mask > 0]
    if len(masked_pixels) > 0:
        features["mean_intensity"] = float(np.mean(masked_pixels))
        features["std_intensity"] = float(np.std(masked_pixels))
        features["intensity_range"] = float(np.ptp(masked_pixels))
    else:
        features["mean_intensity"] = float(np.mean(gray))
        features["std_intensity"] = float(np.std(gray))
        features["intensity_range"] = float(np.ptp(gray))

    # 3. Hu Moments (Scale & Invariant Shape Descriptors)
    moments = cv2.moments(mask)
    hu_moments = cv2.HuMoments(moments).flatten()
    for i, hu in enumerate(hu_moments):
        features[f"hu_{i+1}"] = float(hu)

    # 4. GLCM Texture Descriptors
    # Downsample for GLCM efficiency
    small_gray = cv2.resize(gray, (128, 128))
    glcm = graycomatrix(small_gray, distances=[1], angles=[0], levels=256, symmetric=True, normed=True)
    features["glcm_contrast"] = float(graycoprops(glcm, 'contrast')[0, 0])
    features["glcm_dissimilarity"] = float(graycoprops(glcm, 'dissimilarity')[0, 0])
    features["glcm_homogeneity"] = float(graycoprops(glcm, 'homogeneity')[0, 0])

    return features


def validate_and_sanitize_features(features: Dict[str, float]) -> Tuple[Dict[str, float], bool, list]:
    """
    Validates feature dictionary against schema and checks for NaN, Inf, and missing keys.
    Returns: (sanitized_features, is_valid, list_of_flaws)
    """
    flaws = []
    sanitized = {}

    for col in EXPECTED_FEATURES:
        if col not in features:
            flaws.append(f"Missing key: {col}")
            sanitized[col] = FEATURE_PRIORS.get(col, 0.0)
        else:
            val = features[col]
            if val is None or np.isnan(val) or np.isinf(val):
                flaws.append(f"Invalid numeric value ({val}) for {col}")
                sanitized[col] = FEATURE_PRIORS.get(col, 0.0)
            else:
                sanitized[col] = float(val)

    is_valid = len(flaws) == 0
    return sanitized, is_valid, flaws
