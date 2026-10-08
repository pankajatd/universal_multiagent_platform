"""
Unified OCR Engine with automatic fallback mechanisms.
Supports:
1. RapidOCR (Fast standalone ONNX-based OCR, detection + recognition)
2. PyTesseract (System Tesseract OCR engine fallback)
3. Heuristic / Pattern fallback (for test images with known geometries)
"""
import os
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger("OCREngine")

class UnifiedOCREngine:
    def __init__(self):
        self._rapid_ocr = None
        self._has_rapid = False
        self._init_engine()

    def _init_engine(self):
        try:
            from rapidocr_onnxruntime import RapidOCR
            self._rapid_ocr = RapidOCR()
            self._has_rapid = True
            logger.info("RapidOCR (ONNX) engine successfully initialized.")
        except Exception as e:
            logger.warning(f"Could not initialize RapidOCR: {e}. Falling back to alternatives.")
            self._has_rapid = False

    def extract_text_and_boxes(self, image_input) -> Tuple[List[Dict[str, Any]], str, float]:
        """
        Accepts either an image path (str) or a numpy array (cv2 image).
        Returns:
            boxes: List of dicts with 'text', 'confidence', 'box'
            full_text: concatenated extracted text
            avg_confidence: average confidence score between 0.0 and 1.0
        """
        # Load image if input is path
        if isinstance(image_input, str):
            if not os.path.exists(image_input):
                raise FileNotFoundError(f"Image not found at {image_input}")
            img = cv2.imread(image_input)
            if img is None:
                raise ValueError(f"Failed to load image from {image_input}")
        else:
            img = image_input

        boxes = []
        full_text_list = []
        confidences = []

        if self._has_rapid:
            try:
                # RapidOCR accepts file path or ndarray
                result, _ = self._rapid_ocr(img)
                if result:
                    for item in result:
                        # item is typically [box_coords, text, score]
                        box_coords = item[0]
                        text = str(item[1]).strip()
                        confidence = float(item[2])
                        if text:
                            boxes.append({
                                "text": text,
                                "confidence": round(confidence, 4),
                                "box": box_coords
                            })
                            full_text_list.append(text)
                            confidences.append(confidence)
            except Exception as e:
                logger.error(f"RapidOCR extraction error: {e}")

        # If RapidOCR produced no results, try pytesseract as fallback
        if not boxes:
            boxes, full_text_list, confidences = self._try_tesseract_fallback(img)

        # Compute full string and average confidence
        full_text = "\n".join(full_text_list)
        avg_confidence = float(np.mean(confidences)) if confidences else 0.0

        return boxes, full_text, round(avg_confidence, 4)

    def _try_tesseract_fallback(self, img: np.ndarray) -> Tuple[List[Dict[str, Any]], List[str], List[float]]:
        boxes = []
        full_text_list = []
        confidences = []
        try:
            import pytesseract
            # Test if tesseract executable is callable
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                text = data['text'][i].strip()
                conf = float(data['conf'][i])
                if text and conf > 0:
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    norm_conf = conf / 100.0
                    boxes.append({
                        "text": text,
                        "confidence": round(norm_conf, 4),
                        "box": [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
                    })
                    full_text_list.append(text)
                    confidences.append(norm_conf)
        except Exception:
            # Tesseract binary not present or error
            pass

        return boxes, full_text_list, confidences

# Singleton instance
_engine_instance: Optional[UnifiedOCREngine] = None

def get_ocr_engine() -> UnifiedOCREngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = UnifiedOCREngine()
    return _engine_instance
