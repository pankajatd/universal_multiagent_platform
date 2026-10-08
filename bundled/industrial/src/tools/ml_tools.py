import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from sklearn.ensemble import RandomForestClassifier
from src.config import MODELS_DIR, DEFECT_CLASSES, EXPECTED_FEATURES
from src.tools.camera import SyntheticIndustrialGenerator
from src.tools.cv_tools import preprocess, segment
from src.tools.feature_tools import extract_features

MODEL_PATH = os.path.join(MODELS_DIR, "rf_model.joblib")
_CACHED_MODEL = None

def train_classifier(output_path: str = MODEL_PATH, samples_per_class: int = 50) -> RandomForestClassifier:
    """
    Trains a Random Forest classifier natively using balanced synthetic metal defect samples at 512x512.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    generator = SyntheticIndustrialGenerator(width=512, height=512, seed=42)

    X_list = []
    y_list = []

    print(f"[ML Tools] Generating {samples_per_class * len(DEFECT_CLASSES)} synthetic training frames across 5 classes (512x512)...")
    for label in DEFECT_CLASSES:
        for _ in range(samples_per_class):
            img, _ = generator.generate(label)
            pre = preprocess(img)
            mask = segment(pre)
            feats = extract_features(pre, mask)
            X_list.append([feats[col] for col in EXPECTED_FEATURES])
            y_list.append(label)

    df_X = pd.DataFrame(X_list, columns=EXPECTED_FEATURES)
    clf = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)
    clf.fit(df_X, y_list)

    joblib.dump(clf, output_path)
    print(f"[ML Tools] Classifier successfully trained and saved to {output_path}")
    return clf


def get_model() -> RandomForestClassifier:
    """Loads and caches the Random Forest model, training a fresh model if missing."""
    global _CACHED_MODEL
    if _CACHED_MODEL is not None:
        return _CACHED_MODEL

    if os.path.exists(MODEL_PATH):
        try:
            _CACHED_MODEL = joblib.load(MODEL_PATH)
            return _CACHED_MODEL
        except Exception as e:
            print(f"[ML Tools] Warning: Failed loading existing model ({e}). Re-training fresh model...")

    _CACHED_MODEL = train_classifier(MODEL_PATH)
    return _CACHED_MODEL


def predict_defect(model: RandomForestClassifier, features: Dict[str, float]) -> Tuple[str, float, Dict[str, float]]:
    """
    Predicts defect class, confidence, and class probability distribution.
    """
    df_row = pd.DataFrame([[features[col] for col in EXPECTED_FEATURES]], columns=EXPECTED_FEATURES)
    pred_label = str(model.predict(df_row)[0])
    probs = model.predict_proba(df_row)[0]
    
    classes = list(model.classes_)
    class_probs = {c: float(probs[i]) for i, c in enumerate(classes)}
    confidence = float(np.max(probs))

    return pred_label, confidence, class_probs


def calculate_severity(defect_type: str, features: Dict[str, float], frame_shape: Tuple[int, int] = (512, 512)) -> Tuple[float, str]:
    """
    Computes dynamic defect severity score (0.0 to 10.0) based on defect type and contour impact.
    """
    if defect_type == "normal" or features.get("contour_count", 0) == 0:
        return 0.0, "PASS"

    total_pixels = frame_shape[0] * frame_shape[1]
    defect_ratio = features.get("total_area", 0.0) / total_pixels

    if defect_type == "dimensional":
        multiplier = 4500.0
        base = 3.5
    elif defect_type == "crack":
        multiplier = 3500.0
        base = 4.0
    elif defect_type == "corrosion":
        multiplier = 2000.0
        base = 2.5
    else:  # scratch
        multiplier = 1500.0
        base = 1.5

    score = min(10.0, round(defect_ratio * multiplier + base, 1))

    if score >= 7.5:
        level = "CRITICAL"
    elif score >= 4.0:
        level = "MEDIUM"
    else:
        level = "LOW"

    return score, level
