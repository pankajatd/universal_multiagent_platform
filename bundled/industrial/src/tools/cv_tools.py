import cv2
import numpy as np
from typing import Dict, Any, Tuple
from src.config import MIN_LAPLACIAN_VARIANCE, MIN_CONTRAST_STD, MAX_BRIGHTNESS_MEAN, MIN_BRIGHTNESS_MEAN

def assess_image_quality(frame: np.ndarray) -> Dict[str, Any]:
    """Assesses incoming optical frame quality for blur, exposure, and contrast."""
    if len(frame.shape) == 3:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame.copy()

    # 1. Blur Detection using Variance of Laplacian
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    
    # 2. Exposure & Contrast
    mean_val = float(np.mean(gray))
    std_val = float(np.std(gray))
    
    issues = []
    if laplacian_var < MIN_LAPLACIAN_VARIANCE:
        issues.append("blur")
    if std_val < MIN_CONTRAST_STD:
        issues.append("low_contrast")
    if mean_val > MAX_BRIGHTNESS_MEAN:
        issues.append("overexposed")
    elif mean_val < MIN_BRIGHTNESS_MEAN:
        issues.append("underexposed")

    return {
        "laplacian_variance": round(laplacian_var, 2),
        "mean_brightness": round(mean_val, 2),
        "contrast_std": round(std_val, 2),
        "is_acceptable": len(issues) == 0,
        "detected_issues": issues
    }


def preprocess(
    frame: np.ndarray, 
    clahe_clip: float = 3.0, 
    apply_bilateral: bool = False,
    gamma: float = 1.0
) -> np.ndarray:
    """Preprocesses industrial metal frames with CLAHE, LAB color, and denoising."""
    img = frame.copy()
    
    # Gamma correction if specified
    if gamma != 1.0:
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        img = cv2.LUT(img, table)

    # Optional bilateral filter to preserve edges while smoothing metal grain
    if apply_bilateral:
        img = cv2.bilateralFilter(img, d=9, sigmaColor=75, sigmaSpace=75)

    # LAB color conversion + CLAHE on L-channel
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    clahe = cv2.createCLAHE(clipLimit=clahe_clip, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    
    merged = cv2.merge((cl, a, b))
    preprocessed_bgr = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
    
    # Denoise with mild Gaussian
    denoised = cv2.GaussianBlur(preprocessed_bgr, (3, 3), 0)
    return denoised


def segment(preprocessed_bgr: np.ndarray, threshold_offset: int = 0) -> np.ndarray:
    """
    Performs Grain-Neutral surface segmentation.
    Subtracts row-wise mean intensity to cancel brushed metal horizontal lines,
    isolating true surface anomalies (scratches, cracks, corrosion pits, edge chips).
    """
    gray = cv2.cvtColor(preprocessed_bgr, cv2.COLOR_BGR2GRAY)
    
    # Row-wise mean subtraction (cancels horizontal metal grain)
    row_means = np.mean(gray, axis=1, keepdims=True)
    grain_neutral = np.clip(np.abs(gray.astype(np.float32) - row_means), 0, 255).astype(np.uint8)

    # Thresholding
    thresh_val = max(15, 28 + threshold_offset)
    _, binary = cv2.threshold(grain_neutral, thresh_val, 255, cv2.THRESH_BINARY)

    # Morphological cleaning
    kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_open)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel_close)
    return cleaned


def recalibrate_frame(frame: np.ndarray, detected_issues: list) -> Tuple[np.ndarray, str]:
    """
    Autonomous Image Recovery: Applies targeted computer vision transforms
    to heal degraded frames (defocus blur, extreme darkness, high glare).
    """
    healed = frame.copy()
    actions = []

    # 1. Healing underexposure: Adaptive gamma lift + Histogram Equalization
    if "underexposed" in detected_issues or "low_contrast" in detected_issues:
        gray = cv2.cvtColor(healed, cv2.COLOR_BGR2GRAY)
        mean_b = np.mean(gray)
        gamma = max(1.8, min(3.5, 120.0 / (mean_b + 1e-5)))
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        healed = cv2.LUT(healed, table)
        actions.append(f"GammaCorrection(gamma={round(gamma, 2)})")

    # 2. Healing overexposure: Normalize dynamic range
    if "overexposed" in detected_issues:
        healed = cv2.normalize(healed, None, alpha=0, beta=200, norm_type=cv2.NORM_MINMAX)
        actions.append("DynamicRangeCompression")

    # 3. Healing blur: Unsharp masking & Laplacian sharpening
    if "blur" in detected_issues:
        gaussian = cv2.GaussianBlur(healed, (0, 0), 3.0)
        unsharp = cv2.addWeighted(healed, 1.8, gaussian, -0.8, 0)
        healed = np.clip(unsharp, 0, 255).astype(np.uint8)
        actions.append("UnsharpMaskSharpening")

    # Final contrast normalization
    actions_desc = " + ".join(actions) if actions else "DefaultCLAHEEqualization"
    return healed, actions_desc
