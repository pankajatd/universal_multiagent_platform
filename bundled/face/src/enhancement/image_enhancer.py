import cv2
import numpy as np
from typing import Dict, Any, Tuple

class ImageEnhancerAgent:
    """
    Auto-Fix / Enhancer Agent: Executes targeted self-healing transformations
    (CLAHE, unsharp masking, gamma adjustment) based on the Quality Agent's feedback.
    """

    def enhance_image(self, image: np.ndarray, quality_report: Dict[str, Any]) -> Tuple[np.ndarray, str]:
        """
        Applies fix transformation according to diagnosed quality issues.
        """
        issues = quality_report.get("issues", [])
        if not issues:
            return image, "NO_ENHANCEMENT_NEEDED"

        primary_issue = issues[0]
        enhanced = image.copy()
        fix_action = "GENERAL_CONTRAST_BOOST"

        if primary_issue == "UNDER_EXPOSED":
            # Apply CLAHE on Lab luminance channel + brightness boost
            lab = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.5, tileGridSize=(8, 8))
            l_enhanced = clahe.apply(l)
            lab_enhanced = cv2.merge((l_enhanced, a, b))
            enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
            # Gamma correction to brighten dark shadows
            gamma = 1.6
            inv_gamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
            enhanced = cv2.LUT(enhanced, table)
            fix_action = "CLAHE_BRIGHTNESS_BOOST"

        elif primary_issue == "BLURRY":
            # Apply Unsharp Masking to restore edge micro-contrast
            gaussian_blur = cv2.GaussianBlur(enhanced, (0, 0), sigmaX=3.0)
            enhanced = cv2.addWeighted(enhanced, 1.6, gaussian_blur, -0.6, 0)
            # High-pass sharpening kernel filter
            kernel = np.array([[0, -1, 0],
                               [-1, 5, -1],
                               [0, -1, 0]], dtype=np.float32)
            enhanced = cv2.filter2D(enhanced, -1, kernel)
            fix_action = "UNSHARP_MASK_SHARPENING"

        elif primary_issue == "LOW_CONTRAST":
            # Equalize histogram across channels
            for c in range(3):
                enhanced[:, :, c] = cv2.equalizeHist(enhanced[:, :, c])
            fix_action = "HISTOGRAM_EQUALIZATION"

        return enhanced, fix_action
