import cv2
import numpy as np
import random
from typing import Tuple, Dict, Any

class SyntheticFaceStreamer:
    """
    Generates synthetic facial test images with configurable quality degradations
    (blur, low illumination, noise) to test the Multi-Agent Detection & Self-Healing loop.
    """

    def __init__(self, img_size: Tuple[int, int] = (512, 512)):
        self.height, self.width = img_size

    def generate_face_image(
        self,
        degradation_type: str = "none",
        severity: float = 0.5
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Renders a synthetic head/face composition with optional quality degradation.
        
        degradation_type: 'none', 'blur', 'under_exposed', 'noise'
        """
        # Create a background canvas
        img = np.full((self.height, self.width, 3), (210, 210, 210), dtype=np.uint8)

        # Draw a synthetic face structure
        center_x = self.width // 2
        center_y = self.height // 2
        axes = (110, 150) # Head oval

        # Skin tone (BGR)
        skin_color = (180, 205, 240)
        cv2.ellipse(img, (center_x, center_y), axes, 0, 0, 360, skin_color, -1)
        cv2.ellipse(img, (center_x, center_y), axes, 0, 0, 360, (140, 165, 200), 3) # Outline

        # Eyes
        eye_y = center_y - 30
        left_eye_x = center_x - 45
        right_eye_x = center_x + 45
        cv2.circle(img, (left_eye_x, eye_y), 16, (255, 255, 255), -1)
        cv2.circle(img, (right_eye_x, eye_y), 16, (255, 255, 255), -1)
        cv2.circle(img, (left_eye_x, eye_y), 7, (80, 40, 20), -1)
        cv2.circle(img, (right_eye_x, eye_y), 7, (80, 40, 20), -1)

        # Eyebrows
        cv2.line(img, (left_eye_x - 20, eye_y - 25), (left_eye_x + 20, eye_y - 28), (40, 30, 20), 4)
        cv2.line(img, (right_eye_x - 20, eye_y - 28), (right_eye_x + 20, eye_y - 25), (40, 30, 20), 4)

        # Nose
        nose_pts = np.array([
            [center_x, center_y - 10],
            [center_x - 12, center_y + 25],
            [center_x + 12, center_y + 25]
        ], np.int32)
        cv2.polylines(img, [nose_pts], isClosed=False, color=(130, 150, 180), thickness=3)

        # Mouth / Smile
        cv2.ellipse(img, (center_x, center_y + 60), (35, 20), 0, 0, 180, (60, 50, 150), 4)

        # Ground truth face bounding box [x, y, w, h]
        gt_bbox = [center_x - axes[0], center_y - axes[1], axes[0] * 2, axes[1] * 2]

        # Apply Requested Degradation
        applied_degradation = degradation_type
        if degradation_type == "blur":
            ksize = int(severity * 25) | 1 # Ensure odd kernel size >= 3
            ksize = max(3, ksize)
            img = cv2.GaussianBlur(img, (ksize, ksize), 0)
        elif degradation_type == "under_exposed":
            factor = max(0.1, 1.0 - severity * 0.8)
            img = np.clip(img.astype(np.float32) * factor, 0, 255).astype(np.uint8)
        elif degradation_type == "noise":
            noise = np.random.normal(0, severity * 40, img.shape).astype(np.float32)
            img = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)

        meta = {
            "ground_truth_bbox": gt_bbox,
            "degradation": applied_degradation,
            "severity": severity,
            "image_size": [self.width, self.height]
        }

        return img, meta
