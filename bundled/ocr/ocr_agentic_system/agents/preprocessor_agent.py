"""
Preprocessor Agent:
Analyzes image quality (blur, contrast, skew, illumination) and applies
adaptive computer vision operations (deskewing, CLAHE, bilateral filtering,
adaptive thresholding, and morphological enhancement).
Also supports guided re-processing invocations by the Error Resolver.
"""
import os
import cv2
import numpy as np
from typing import Dict, Any, Tuple, List, Optional
import logging

logger = logging.getLogger("PreprocessorAgent")

class PreprocessorAgent:
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or os.path.join(os.getcwd(), "ocr_output", "preprocessed")
        os.makedirs(self.output_dir, exist_ok=True)

    def analyze_quality(self, image: np.ndarray) -> Dict[str, Any]:
        """Calculates blur score, contrast, brightness, and estimated skew angle."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # 1. Blur detection via variance of the Laplacian
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        is_blurry = laplacian_var < 80.0

        # 2. Contrast & Brightness
        mean_brightness = float(np.mean(gray))
        contrast_std = float(np.std(gray))
        is_low_contrast = contrast_std < 40.0

        # 3. Skew estimation
        skew_angle = self._estimate_skew_angle(gray)

        # 4. Check if predominantly dark (inverted text)
        is_dark_background = mean_brightness < 90.0

        return {
            "laplacian_variance": round(laplacian_var, 2),
            "is_blurry": is_blurry,
            "mean_brightness": round(mean_brightness, 2),
            "contrast_std": round(contrast_std, 2),
            "is_low_contrast": is_low_contrast,
            "estimated_skew_angle": round(skew_angle, 2),
            "is_dark_background": is_dark_background,
            "dimensions": {"height": image.shape[0], "width": image.shape[1], "channels": image.shape[2] if len(image.shape) == 3 else 1}
        }

    def _estimate_skew_angle(self, gray: np.ndarray) -> float:
        """Estimates skew angle of text lines using Canny and HoughLinesP."""
        try:
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=80, maxLineGap=10)
            if lines is None or len(lines) == 0:
                return 0.0
            
            angles = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if x2 - x1 == 0:
                    continue
                angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                # Text lines are nearly horizontal (between -25 and +25 degrees)
                if -25.0 <= angle <= 25.0:
                    angles.append(angle)

            if not angles:
                return 0.0

            median_angle = float(np.median(angles))
            if abs(median_angle) < 0.8:
                return 0.0
            return float(median_angle)
        except Exception:
            return 0.0

    def rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        """Rotates image around its center by angle degrees."""
        if abs(angle) < 0.5:
            return image
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, rot_mat, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return rotated

    def enhance(self, image_path: str, strategy: Optional[str] = None) -> Tuple[str, List[str], Dict[str, Any]]:
        """
        Enhances the image based on initial quality analysis or a targeted strategy requested by Error Resolver.
        Returns:
            (preprocessed_image_path, history_of_steps, quality_metrics)
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Input image not found: {image_path}")

        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image from {image_path}")

        history: List[str] = []
        metrics = self.analyze_quality(img)
        enhanced = img.copy()

        # Step 1: Handle Targeted Error Resolution Strategies if passed
        if strategy == "invert_colors":
            enhanced = cv2.bitwise_not(enhanced)
            history.append("bitwise_inversion_applied")

        elif strategy == "aggressive_clahe":
            if len(enhanced.shape) == 3:
                lab = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
                l = clahe.apply(l)
                enhanced = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)
            else:
                clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
                enhanced = clahe.apply(enhanced)
            history.append("aggressive_clahe_contrast_boost")

        elif strategy == "sharpen_edges":
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
            enhanced = cv2.filter2D(enhanced, -1, kernel)
            history.append("unsharp_masking_applied")

        elif strategy == "binarize_otsu":
            gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY) if len(enhanced.shape) == 3 else enhanced
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            enhanced = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
            history.append("otsu_binarization_applied")

        elif strategy == "morphological_cleanup":
            gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY) if len(enhanced.shape) == 3 else enhanced
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            closed = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            enhanced = cv2.cvtColor(closed, cv2.COLOR_GRAY2BGR)
            history.append("morphological_close_cleanup")

        else:
            # Standard Adaptive Auto-Enhancement Pipeline
            # 1. Deskew if skew angle is significant
            if abs(metrics["estimated_skew_angle"]) >= 1.0:
                enhanced = self.rotate_image(enhanced, -metrics["estimated_skew_angle"])
                history.append(f"deskew_rotated_{-metrics['estimated_skew_angle']:.1f}deg")

            # 2. Invert if dark background (common in license plates or negative scans)
            if metrics["is_dark_background"]:
                enhanced = cv2.bitwise_not(enhanced)
                history.append("auto_invert_dark_background")

            # 3. Contrast enhancement via CLAHE if low contrast
            if metrics["is_low_contrast"] or metrics["mean_brightness"] > 210:
                if len(enhanced.shape) == 3:
                    lab = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
                    l, a, b = cv2.split(lab)
                    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
                    l = clahe.apply(l)
                    enhanced = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)
                else:
                    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
                    enhanced = clahe.apply(enhanced)
                history.append("clahe_contrast_equalization")

            # 4. Mild bilateral filtering to suppress sensor noise while preserving text edges
            enhanced = cv2.bilateralFilter(enhanced, d=5, sigmaColor=50, sigmaSpace=50)
            history.append("bilateral_filter_denoising")

        # Save preprocessed image to disk
        base_name = os.path.basename(image_path)
        name, ext = os.path.splitext(base_name)
        suffix = f"_{strategy}" if strategy else "_enhanced"
        out_filename = f"{name}{suffix}.png"
        out_path = os.path.join(self.output_dir, out_filename)
        cv2.imwrite(out_path, enhanced)

        return out_path, history, metrics
