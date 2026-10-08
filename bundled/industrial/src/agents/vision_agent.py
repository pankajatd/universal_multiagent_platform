import traceback
import numpy as np
from typing import Dict, Any
from src.state import AgenticState, ErrorRecord
from src.tools.cv_tools import assess_image_quality, preprocess, segment
from src.tools.feature_tools import extract_features

class VisionAgent:
    """Vision & Preprocessing Agent: Ingests frames, assesses quality, segments defects, and extracts features."""

    def __init__(self):
        self.name = "VisionAgent"

    def __call__(self, state: AgenticState) -> AgenticState:
        new_state = dict(state)
        new_state.setdefault("execution_log", [])
        new_state.setdefault("errors", [])
        new_state["execution_log"].append(f"[{self.name}] Ingesting frame index {state.get('frame_index', 0)}...")

        raw_frame = state.get("raw_frame")
        if raw_frame is None:
            new_state["errors"].append({
                "component": "vision_agent",
                "error_type": "missing_frame",
                "message": "Raw frame is None. No visual input received.",
                "resolved": False
            })
            new_state["status"] = "NEEDS_HEALING"
            return new_state

        try:
            # 1. Optical Quality Assessment
            quality = assess_image_quality(raw_frame)
            new_state["image_quality"] = quality

            if not quality["is_acceptable"]:
                # Degraded frame detected - log error for SelfHealingAgent
                issues_str = ", ".join(quality["detected_issues"])
                new_state["execution_log"].append(f"[{self.name}] WARNING: Optical degradation detected: {issues_str}")
                new_state["errors"].append({
                    "component": "vision_agent",
                    "error_type": "image_degraded",
                    "message": f"Frame quality degraded: {issues_str}. Laplacian var: {quality['laplacian_variance']}, Mean brightness: {quality['mean_brightness']}",
                    "resolved": False
                })
                new_state["status"] = "NEEDS_HEALING"
                return new_state

            # 2. Preprocessing & Grain-Neutral Segmentation
            preprocessed = preprocess(raw_frame)
            mask = segment(preprocessed)
            new_state["processed_frame"] = preprocessed
            new_state["mask"] = mask

            # 3. 21-D Feature Extraction
            features = extract_features(preprocessed, mask)
            new_state["features"] = features
            new_state["execution_log"].append(
                f"[{self.name}] Vision pipeline success. Extracted {len(features)} features. Contours found: {features.get('contour_count', 0)}"
            )

        except Exception as e:
            tb = traceback.format_exc()
            new_state["execution_log"].append(f"[{self.name}] ERROR: Exception in vision pipeline: {str(e)}")
            new_state["errors"].append({
                "component": "vision_agent",
                "error_type": "runtime_exception",
                "message": f"Vision processing exception: {str(e)}",
                "traceback": tb,
                "resolved": False
            })
            new_state["status"] = "NEEDS_HEALING"

        return new_state
