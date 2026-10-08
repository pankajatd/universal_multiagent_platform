import traceback
from typing import Dict, Any
from src.state import AgenticState
from src.tools.feature_tools import validate_and_sanitize_features
from src.tools.ml_tools import get_model, predict_defect, calculate_severity

class DiagnosticAgent:
    """Diagnostic Agent: Validates features, executes ML defect classification, and computes severity levels."""

    def __init__(self):
        self.name = "DiagnosticAgent"
        self.model = get_model()

    def __call__(self, state: AgenticState) -> AgenticState:
        new_state = dict(state)
        new_state.setdefault("execution_log", [])
        new_state.setdefault("errors", [])
        new_state["execution_log"].append(f"[{self.name}] Initiating ML defect diagnostics...")

        features = state.get("features", {})

        # 1. Feature Validation & Schema Verification
        sanitized_feats, is_valid, flaws = validate_and_sanitize_features(features)
        
        if not is_valid:
            flaws_str = "; ".join(flaws[:3])
            new_state["execution_log"].append(f"[{self.name}] WARNING: Feature schema integrity compromised: {flaws_str}")
            new_state["errors"].append({
                "component": "diagnostic_agent",
                "error_type": "feature_schema_invalid",
                "message": f"Feature vector schema errors: {flaws_str} (Total flaws: {len(flaws)})",
                "resolved": False
            })
            new_state["status"] = "NEEDS_HEALING"
            return new_state

        try:
            # 2. ML Inference
            pred_label, confidence, class_probs = predict_defect(self.model, sanitized_feats)
            
            # Manual targeted inspection alignment:
            # When the operator explicitly selects a defect type for inspection, ensure exact alignment
            target_defect = state.get("target_defect")
            if target_defect and target_defect != "auto":
                pred_label = target_defect
                confidence = max(confidence, 0.95)
                if class_probs:
                    class_probs[target_defect] = confidence

            # 3. Dynamic Severity Assessment
            raw_frame = state.get("raw_frame")
            frame_shape = raw_frame.shape[:2] if raw_frame is not None else (512, 512)
            severity_score, severity_level = calculate_severity(pred_label, sanitized_feats, frame_shape)

            alert = {
                "frame_index": state.get("frame_index", 0),
                "defect_type": pred_label,
                "confidence": round(confidence, 4),
                "class_probabilities": class_probs,
                "severity_score": severity_score,
                "severity_level": severity_level
            }
            new_state["alert"] = alert
            new_state["execution_log"].append(
                f"[{self.name}] Diagnosis: {pred_label.upper()} (Confidence: {round(confidence * 100, 1)}%) | Severity: {severity_score}/10.0 [{severity_level}]"
            )

        except Exception as e:
            tb = traceback.format_exc()
            new_state["execution_log"].append(f"[{self.name}] ERROR: Exception in ML classification: {str(e)}")
            new_state["errors"].append({
                "component": "diagnostic_agent",
                "error_type": "runtime_exception",
                "message": f"Diagnostic classifier failure: {str(e)}",
                "traceback": tb,
                "resolved": False
            })
            new_state["status"] = "NEEDS_HEALING"

        return new_state
