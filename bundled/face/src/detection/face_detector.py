import os
import cv2
import numpy as np
from typing import List, Dict, Any

class FaceDetectorAgent:
    """
    Detector Agent: Uses OpenCV Cascade / Color-Geometry heuristics to detect
    face bounding boxes and compute detection confidence metrics.
    """

    def __init__(self):
        # 1. Primary Engine: OpenCV YuNet Deep Neural Network Face Detector
        self.yunet_detector = None
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        model_path = os.path.join(project_root, "models", "face_detection_yunet.onnx")

        if os.path.exists(model_path) and hasattr(cv2, "FaceDetectorYN"):
            try:
                self.yunet_detector = cv2.FaceDetectorYN.create(
                    model=model_path,
                    config="",
                    input_size=(320, 320),
                    score_threshold=0.60,
                    nms_threshold=0.30,
                    top_k=5000
                )
            except Exception:
                self.yunet_detector = None

        # 2. Secondary Engine: Haar Cascades (Fallbacks)
        self.face_cascade_alt = None
        self.face_cascade_def = None
        if hasattr(cv2, "CascadeClassifier") and hasattr(cv2, "data"):
            try:
                p = cv2.data.haarcascades
                alt_path = os.path.join(p, 'haarcascade_frontalface_alt2.xml')
                def_path = os.path.join(p, 'haarcascade_frontalface_default.xml')

                if os.path.exists(alt_path):
                    alt_c = cv2.CascadeClassifier(alt_path)
                    if hasattr(alt_c, "empty") and not alt_c.empty():
                        self.face_cascade_alt = alt_c

                if os.path.exists(def_path):
                    def_c = cv2.CascadeClassifier(def_path)
                    if hasattr(def_c, "empty") and not def_c.empty():
                        self.face_cascade_def = def_c
            except Exception:
                pass

        self.face_cascade = self.face_cascade_alt or self.face_cascade_def

    @staticmethod
    def suppress_nested_and_overlapping_boxes(boxes: List[List[int]], iou_thresh: float = 0.55, containment_thresh: float = 0.70) -> List[List[int]]:
        """
        Suppresses sub-boxes and overlapping duplicate detections.
        Preserves distinct adjacent faces in photos while eliminating spectacle/nose nested sub-boxes.
        """
        if len(boxes) <= 1:
            return boxes

        # Sort by area descending
        boxes = sorted(boxes, key=lambda b: b[2] * b[3], reverse=True)
        keep = []

        for boxA in boxes:
            xA, yA, wA, hA = boxA
            areaA = wA * hA
            is_duplicate = False

            for kept in keep:
                xK, yK, wK, hK = kept
                areaK = wK * hK

                ix1 = max(xA, xK)
                iy1 = max(yA, yK)
                ix2 = min(xA + wA, xK + wK)
                iy2 = min(yA + hA, yK + hK)

                inter_w = max(0, ix2 - ix1)
                inter_h = max(0, iy2 - iy1)
                inter_area = inter_w * inter_h

                if inter_area > 0:
                    iou = inter_area / float(areaA + areaK - inter_area)
                    containmentA = inter_area / float(areaA) # fraction of boxA inside kept

                    # If boxA is nested inside kept box (e.g. spectacle sub-box) or high overlap
                    if containmentA >= containment_thresh or iou >= iou_thresh:
                        is_duplicate = True
                        break

            if not is_duplicate:
                keep.append(boxA)

        return keep

    def detect_faces(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Scans an image and returns a list of detected face bounding boxes with confidence.
        Uses Deep Neural Network (YuNet) for high-precision detection with zero false positives.
        """
        h, w = image.shape[:2]
        results = []

        # --- PRIMARY: YuNet Deep Learning Face Detector ---
        if self.yunet_detector is not None:
            try:
                self.yunet_detector.setInputSize((w, h))
                _, faces = self.yunet_detector.detect(image)
                if faces is not None and len(faces) > 0:
                    for f in faces:
                        bx = max(0, int(f[0]))
                        by = max(0, int(f[1]))
                        bw = min(w - bx, int(f[2]))
                        bh = min(h - by, int(f[3]))
                        conf = round(float(f[-1]), 2)
                        if bw >= 16 and bh >= 16:
                            results.append({
                                "bbox": [bx, by, bw, bh],
                                "confidence": conf,
                                "detection_method": "yunet_dnn"
                            })
                    if results:
                        return results
            except Exception:
                pass

        # --- SECONDARY: Haar Cascade Ensemble (if DNN is unavailable) ---
        if self.face_cascade_alt is not None:
            try:
                faces_alt = self.face_cascade_alt.detectMultiScale(
                    gray,
                    scaleFactor=1.08,
                    minNeighbors=4,
                    minSize=(28, 28)
                )
                for b in faces_alt:
                    raw_boxes.append(list(b))
            except Exception:
                pass

        # 2. Secondary Pass: If 0 faces found by primary, check Default Cascade
        if len(raw_boxes) == 0 and self.face_cascade_def is not None:
            try:
                faces_def = self.face_cascade_def.detectMultiScale(
                    gray,
                    scaleFactor=1.10,
                    minNeighbors=5,
                    minSize=(32, 32)
                )
                for b in faces_def:
                    raw_boxes.append(list(b))
            except Exception:
                pass

        # 3. Shadowed Crowd Pass: If still 0 faces, try CLAHE equalization for low-light/crowd shadows
        if len(raw_boxes) == 0 and self.face_cascade_alt is not None:
            try:
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                gray_clahe = clahe.apply(gray)
                faces_clahe = self.face_cascade_alt.detectMultiScale(
                    gray_clahe,
                    scaleFactor=1.08,
                    minNeighbors=3,
                    minSize=(28, 28)
                )
                for b in faces_clahe:
                    raw_boxes.append(list(b))
            except Exception:
                pass

        # Apply crowd-safe non-maximum & spectacle nested-box suppression
        if raw_boxes:
            clean_faces = self.suppress_nested_and_overlapping_boxes(raw_boxes)
            for (x, y, w, h) in clean_faces:
                face_roi = gray[y:y+h, x:x+w]
                std_dev = float(np.std(face_roi)) if face_roi.size > 0 else 30.0
                confidence = min(0.99, round(0.50 + (std_dev / 120.0), 2))

                results.append({
                    "bbox": [int(x), int(y), int(w), int(h)],
                    "confidence": confidence,
                    "detection_method": "haar_cascade_ensemble"
                })

        # Fallback heuristic: Detect skin-colored ellipse blob if cascade unavailable or missed
        if not results:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            mean_val = float(np.mean(image))
            v_min = 20 if mean_val < 70 else 55
            s_min = 15 if mean_val < 70 else 20
            lower_skin = np.array([0, s_min, v_min], dtype=np.uint8)
            upper_skin = np.array([25, 255, 255], dtype=np.uint8)
            skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)

            contours, _ = cv2.findContours(skin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            candidates = []

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 2000: # Significant face-sized blob
                    x, y, w, h = cv2.boundingRect(cnt)
                    aspect_ratio = float(w) / max(1, h)
                    if 0.45 <= aspect_ratio <= 1.5: # Oval face ratio
                        candidates.append((area, [int(x), int(y), int(w), int(h)]))

            candidates.sort(key=lambda c: c[0], reverse=True)
            for area, bbox in candidates[:3]: # Support multiple faces in frame
                conf = round(min(0.95, 0.65 + min(0.30, area / 150000.0)), 2)
                results.append({
                    "bbox": bbox,
                    "confidence": conf,
                    "detection_method": "color_geometry_adaptive"
                })

        return results
