"""Industrial Vision & Diagnostic RAG adapter for the Universal Platform."""
import sys
import time
import cv2
import base64
import numpy as np
from typing import Any, Dict, List, Tuple

from pathlib import Path

# Source project root (bundled in repo or local scratch)
_BUNDLED_ROOT = Path(__file__).parent.parent / "bundled" / "industrial"
_SCRATCH_ROOT = Path(r"C:\Users\panka\.gemini\antigravity\scratch\industrial_multiagent_rag")
_SOURCE_ROOT = str(_BUNDLED_ROOT if _BUNDLED_ROOT.exists() else _SCRATCH_ROOT)

from .base_adapter import BaseProjectAdapter, UniversalResult, scoped_project_environment


class IndustrialAdapter(BaseProjectAdapter):
    """Adapter wrapping the Industrial Multi-Agent Vision & Diagnostic RAG platform."""

    def get_name(self) -> str:
        return "industrial_vision_rag"

    def get_description(self) -> str:
        return (
            "Real-time industrial defect detection with 21-D feature extraction, "
            "Random Forest ML classification, SOP-based maintenance RAG, "
            "and autonomous self-healing."
        )

    def is_available(self) -> Tuple[bool, str]:
        try:
            with scoped_project_environment(_SOURCE_ROOT):
                from src.graph import build_multiagent_graph  # noqa: F401
            return True, "Ready"
        except Exception as exc:
            return False, f"Import error: {exc}"

    def get_graph_definition(self) -> Dict[str, Any]:
        return {
            "nodes": [
                {"name": "orchestrator", "role": "Supervisor & Dynamic Router"},
                {"name": "vision_agent", "role": "Optics / LAB-CLAHE / 21-D Feature Extraction"},
                {"name": "diagnostic_agent", "role": "Random Forest ML Classifier & Severity Scoring"},
                {"name": "maintenance_rag_agent", "role": "SOP Vector Retrieval & Work Order Synthesis"},
                {"name": "self_healing_agent", "role": "Autonomous 4-Engine Failure Remediation"},
                {"name": "quality_gate_agent", "role": "OSHA/ISO Safety Gate & Engineering Signoff"},
            ],
            "edges": [
                {"from": "orchestrator", "to": "vision_agent", "label": "needs features"},
                {"from": "orchestrator", "to": "diagnostic_agent", "label": "needs diagnosis"},
                {"from": "orchestrator", "to": "maintenance_rag_agent", "label": "MEDIUM/CRITICAL"},
                {"from": "orchestrator", "to": "self_healing_agent", "label": "unresolved errors"},
                {"from": "orchestrator", "to": "quality_gate_agent", "label": "needs signoff"},
                {"from": "vision_agent", "to": "orchestrator", "label": "report back"},
                {"from": "diagnostic_agent", "to": "orchestrator", "label": "report back"},
                {"from": "maintenance_rag_agent", "to": "orchestrator", "label": "report back"},
                {"from": "self_healing_agent", "to": "orchestrator", "label": "report back"},
                {"from": "quality_gate_agent", "to": "orchestrator", "label": "report back"},
            ],
        }

    def render_input_controls(self, st_module) -> Dict[str, Any]:
        st_module.markdown("### 🏭 Industrial Vision Controls")

        defect_options = [
            "crack",
            "corrosion",
            "scratch",
            "dimensional",
            "normal",
            "auto"
        ]

        defect_labels = {
            "crack": "Branching Crack",
            "corrosion": "Oxidation Corrosion",
            "scratch": "Surface Scratch",
            "dimensional": "Dimensional Notch",
            "normal": "Normal (Pass - Clean)",
            "auto": "Auto (Conveyor Sequence)"
        }

        defect_type = st_module.selectbox(
            "Defect Type",
            defect_options,
            index=0,
            format_func=lambda d: defect_labels.get(d, d),
            key="ind_defect",
        )
        frame_index = st_module.number_input(
            "Frame Index", value=101, min_value=1, key="ind_frame"
        )
        return {
            "defect_type": defect_type,
            "frame_index": int(frame_index),
            "error_injection": "none",
        }

    def execute(self, inputs: Dict[str, Any]) -> UniversalResult:
        with scoped_project_environment(_SOURCE_ROOT):
            from src.graph import build_multiagent_graph
            from src.tools.camera import SyntheticIndustrialGenerator

            t0 = time.perf_counter()

            defect_choice = inputs.get("defect_type", "crack")
            if not defect_choice or defect_choice == "Select a Defect Type...":
                defect_choice = "crack"
            frame_idx = inputs.get("frame_index", 101)
            error_choice = inputs.get("error_injection", "none")

            generator = SyntheticIndustrialGenerator(seed=101)
            DEFECT_SEQUENCE = ["normal", "scratch", "crack", "corrosion", "dimensional"]
            target_defect = (
                DEFECT_SEQUENCE[(frame_idx - 1) % len(DEFECT_SEQUENCE)]
                if defect_choice in ("auto", "Select a Defect Type...", None, "")
                else defect_choice
            )

            clean_frame, _ = generator.generate(target_defect)
            degraded_frame = None

            initial_state = {
                "frame_index": frame_idx,
                "raw_frame": clean_frame,
                "target_defect": target_defect,
                "execution_log": [f"[Conveyor] Ingested frame #{frame_idx} (Target: {target_defect.upper()})."],
                "errors": [],
                "healing_actions": [],
                "retry_count": 0,
                "status": "PROCESSING",
            }

            # Apply error injections
            if error_choice == "blur":
                degraded_frame = generator.inject_blur(clean_frame, ksize=27)
                initial_state["raw_frame"] = degraded_frame
                initial_state["execution_log"].append("[Error Injected] Heavy defocus blur.")
            elif error_choice == "darkness":
                degraded_frame = generator.inject_underexposure(clean_frame, factor=0.15)
                initial_state["raw_frame"] = degraded_frame
                initial_state["execution_log"].append("[Error Injected] Severe underexposure.")
            elif error_choice == "glare":
                degraded_frame = generator.inject_overexposure(clean_frame, offset=155)
                initial_state["raw_frame"] = degraded_frame
                initial_state["execution_log"].append("[Error Injected] Blinding specular glare.")
            elif error_choice == "schema":
                initial_state["features"] = {
                    "contour_count": 2.0, "mean_intensity": np.nan, "glcm_contrast": np.nan,
                }
                initial_state["execution_log"].append("[Error Injected] Schema corruption.")
            elif error_choice == "rag":
                initial_state["features"] = {col: 1.0 for col in [
                    "contour_count", "total_area", "mean_area", "max_area", "mean_aspect_ratio",
                    "mean_extent", "mean_solidity", "mean_eccentricity", "mean_intensity",
                    "std_intensity", "intensity_range", "hu_1", "hu_2", "hu_3", "hu_4",
                    "hu_5", "hu_6", "hu_7", "glcm_contrast", "glcm_dissimilarity", "glcm_homogeneity",
                ]}
                initial_state["alert"] = {
                    "frame_index": frame_idx,
                    "defect_type": target_defect if target_defect != "normal" else "crack",
                    "confidence": 0.90, "severity_score": 8.0, "severity_level": "CRITICAL",
                }
                initial_state["search_queries"] = ["unrecognized manufacturing artifact nonexistent_keyword_xyz999"]
                initial_state["execution_log"].append("[Error Injected] Ambiguous RAG query.")
            elif error_choice == "exception":
                initial_state["raw_frame"] = None
                initial_state["errors"] = [{
                    "component": "diagnostic_agent",
                    "error_type": "runtime_exception",
                    "message": "ZeroDivisionError: float division by zero",
                    "resolved": False,
                }]
                initial_state["execution_log"].append("[Error Injected] Worker runtime crash.")

            multiagent_app = build_multiagent_graph()
            final_state = multiagent_app.invoke(initial_state)

            elapsed_ms = (time.perf_counter() - t0) * 1000

        # --- Encode frames to base64 ---
        def _frame_to_b64(img):
            if img is None:
                return None
            _, buf = cv2.imencode(".jpg", img)
            return "data:image/jpeg;base64," + base64.b64encode(buf).decode("utf-8")

        def _mask_to_b64(mask):
            if mask is None:
                return None
            h, w = mask.shape[:2]
            colored = np.zeros((h, w, 3), dtype=np.uint8)
            colored[mask > 0] = [0, 0, 255]
            _, buf = cv2.imencode(".png", colored)
            return "data:image/png;base64," + base64.b64encode(buf).decode("utf-8")

        visualizations = {
            "raw_frame": _frame_to_b64(final_state.get("raw_frame")),
            "processed_frame": _frame_to_b64(final_state.get("processed_frame")),
            "mask": _mask_to_b64(final_state.get("mask")),
        }

        alert = final_state.get("alert", {})
        summary = {
            "alert": alert,
            "work_order": final_state.get("work_order"),
            "features": final_state.get("features"),
        }

        # Determine agents invoked
        agents_invoked = ["orchestrator", "vision_agent", "diagnostic_agent"]
        sev = alert.get("severity_level", "PASS") if alert else "PASS"
        if sev in ("MEDIUM", "CRITICAL") and final_state.get("work_order"):
            agents_invoked.append("maintenance_rag_agent")
        if final_state.get("healing_actions"):
            agents_invoked.append("self_healing_agent")
        agents_invoked.append("quality_gate_agent")

        errors_healed = final_state.get("healing_actions", [])
        execution_log = final_state.get("execution_log", [])
        status = final_state.get("status", "COMPLETED")

        return UniversalResult(
            project_name=self.get_name(),
            status=status,
            execution_time_ms=elapsed_ms,
            agents_invoked=agents_invoked,
            execution_log=execution_log,
            summary=summary,
            visualizations=visualizations,
            errors_healed=errors_healed,
            metadata={
                "target_defect": target_defect,
                "error_injection": error_choice,
                "frame_index": frame_idx,
            },
        )

    def render_results(self, st_module, result: UniversalResult) -> None:
        from platform_views.industrial_view import render_industrial_results
        render_industrial_results(st_module, result)
