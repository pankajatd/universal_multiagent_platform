import cv2
import numpy as np
from typing import Dict, Any, List

class QualityInspectorAgent:
    """
    Quality Inspector Agent: Diagnoses image quality flaws (blur, under-exposure,
    low contrast, resolution issues) on the detected face Region of Interest (ROI).
    """

    def inspect_quality(self, image: np.ndarray, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates sharpness (Laplacian variance), mean luminance, and contrast metrics.
        """
        if not detections:
            return {
                "status": "NO_FACE_DETECTED",
                "quality_score": 0.0,
                "blur_score": 0.0,
                "luminance": 0.0,
                "contrast": 0.0,
                "issues": ["NO_FACE_FOUND"]
            }

        # Take primary face detection ROI
        bbox = detections[0]["bbox"]
        x, y, w, h = bbox
        
        # Clamp ROI bounds to image dimensions
        img_h, img_w = image.shape[:2]
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(img_w, x + w), min(img_h, y + h)

        face_crop = image[y1:y2, x1:x2]
        if face_crop.size == 0:
            face_crop = image

        gray_face = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)

        # 1. Blur Detection using Variance of Laplacian
        laplacian_var = float(cv2.Laplacian(gray_face, cv2.CV_64F).var())

        # 2. Illumination / Luminance check
        mean_luminance = float(np.mean(gray_face))

        # 3. Contrast check
        contrast_std = float(np.std(gray_face))

        issues = []
        status = "ACCEPTABLE"

        if laplacian_var < 110.0:
            issues.append("BLURRY")
        
        if mean_luminance < 75.0:
            issues.append("UNDER_EXPOSED")
        elif mean_luminance > 215.0:
            issues.append("OVER_EXPOSED")

        if contrast_std < 25.0:
            issues.append("LOW_CONTRAST")

        # Determine overall quality score (0.0 to 100.0)
        sharpness_subscore = min(50.0, (laplacian_var / 300.0) * 50.0)
        illum_subscore = max(0.0, 50.0 - abs(mean_luminance - 140.0) * 0.35)
        overall_score = round(max(0.0, min(100.0, sharpness_subscore + illum_subscore)), 1)

        if not issues and overall_score >= 75.0:
            status = "EXCELLENT"
        elif issues:
            status = issues[0] # Primary issue driving state routing

        return {
            "status": status,
            "quality_score": overall_score,
            "blur_score": round(laplacian_var, 2),
            "luminance": round(mean_luminance, 2),
            "contrast": round(contrast_std, 2),
            "issues": issues,
            "face_roi_box": [x1, y1, x2 - x1, y2 - y1]
        }
