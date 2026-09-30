"""Face Detection Multi-Agent adapter for the Universal Platform."""
import sys
import time
import cv2
import base64
import numpy as np
from typing import Any, Dict, Tuple

# Source project root (used with scoped_project_environment)
_SOURCE_ROOT = r"C:\Users\panka\.gemini\antigravity\scratch\multi_agent_face_detection"

from .base_adapter import BaseProjectAdapter, UniversalResult, scoped_project_environment


class FaceDetectionAdapter(BaseProjectAdapter):
    """Adapter wrapping the Multi-Agent Face Detection platform."""

    def get_name(self) -> str:
        return "face_detection"

    def get_description(self) -> str:
        return (
            "YuNet DNN face detection with quality inspection, "
            "adaptive image enhancement self-healing loop, and IoU-based audit certification."
        )

    def is_available(self) -> Tuple[bool, str]:
        try:
            with scoped_project_environment(_SOURCE_ROOT):
                from src.graph.workflow import MultiAgentFaceOrchestrator  # noqa: F401
            return True, "Ready"
        except Exception as exc:
            return False, f"Import error: {exc}"

    def get_graph_definition(self) -> Dict[str, Any]:
        return {
            "nodes": [
                {"name": "detector_node", "role": "Face Detector (YuNet DNN + Haar + HSV)"},
                {"name": "quality_node", "role": "Quality Inspector (Blur / Luminance / Contrast)"},
                {"name": "enhancer_node", "role": "Image Enhancer (CLAHE / Unsharp / Histogram EQ)"},
                {"name": "auditor_node", "role": "Test Auditor (IoU Verification & Certification)"},
            ],
            "edges": [
                {"from": "detector_node", "to": "quality_node", "label": "always"},
                {"from": "quality_node", "to": "auditor_node", "label": "quality OK or max retries"},
                {"from": "quality_node", "to": "enhancer_node", "label": "quality degraded"},
                {"from": "enhancer_node", "to": "detector_node", "label": "retry detection"},
            ],
        }

    def render_input_controls(self, st_module) -> Dict[str, Any]:
        st_module.markdown("### 👤 Face Detection Controls")

        st_module.info(
            "📷 **Interactive Workspace Active**\n\n"
            "Upload photos directly using the **Upload Photos** button in the main panel on the right.\n\n"
            "You can also click any thumbnail or use **Auto Play All** to inspect the live detection and self-healing loop."
        )

        st_module.markdown("---")
        st_module.markdown("**Multi-Agent Architecture:**")
        st_module.markdown(
            "• **Detector**: YuNet DNN (300×300)\n"
            "• **Inspector**: Blur / Luminance / Contrast\n"
            "• **Enhancer**: CLAHE / Unsharp Mask / Hist EQ\n"
            "• **Auditor**: IoU Verification & Certification"
        )

        return {
            "input_mode": "Interactive",
            "max_iterations": 3,
            "degradation_type": "none",
            "severity": "moderate"
        }

    def execute(self, inputs: Dict[str, Any]) -> UniversalResult:
        with scoped_project_environment(_SOURCE_ROOT):
            from src.graph.workflow import MultiAgentFaceOrchestrator
            from src.generator.face_streamer import SyntheticFaceStreamer

            t0 = time.perf_counter()
            input_mode = inputs.get("input_mode")
            max_iterations = inputs.get("max_iterations", 3)

            image = None
            metadata: Dict[str, Any] = {}

            if input_mode == "Synthetic Test Image":
                streamer = SyntheticFaceStreamer()
                degradation_type = inputs.get("degradation_type", "none")
                severity_map = {"mild": 0.25, "moderate": 0.5, "severe": 0.8}
                severity = severity_map.get(inputs.get("severity", "moderate"), 0.5)
                image, metadata = streamer.generate_face_image(
                    degradation_type=degradation_type, severity=severity
                )
            else:
                upload_file = inputs.get("upload_file")
                if upload_file is not None:
                    file_bytes = np.asarray(bytearray(upload_file.read()), dtype=np.uint8)
                    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                else:
                    streamer = SyntheticFaceStreamer()
                    image, metadata = streamer.generate_face_image()

            orchestrator = MultiAgentFaceOrchestrator()
            final_state = orchestrator.run(
                input_image=image, metadata=metadata, max_iterations=max_iterations
            )

            elapsed_ms = (time.perf_counter() - t0) * 1000

        # --- Encode images to base64 ---
        def _img_to_b64(img):
            if img is None:
                return None
            _, buf = cv2.imencode(".jpg", img)
            return "data:image/jpeg;base64," + base64.b64encode(buf).decode("utf-8")

        # Draw detection boxes on the current image for the output visualization
        output_image = (final_state.get("current_image") if final_state.get("current_image") is not None else image)
        if output_image is not None:
            output_image = output_image.copy()
            for det in final_state.get("detections", []):
                bbox = det.get("bbox", [])
                conf = det.get("confidence", 0.0)
                if len(bbox) == 4:
                    x, y, w, h = [int(v) for v in bbox]
                    cv2.rectangle(output_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(output_image, f"{conf:.2f}", (x, max(0, y - 5)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        visualizations = {
            "original_image": _img_to_b64(final_state.get("original_image")),
            "output_image": _img_to_b64(output_image),
        }

        quality_report = final_state.get("quality_report", {})
        audit_report = final_state.get("audit_report", {})
        detections = final_state.get("detections", [])
        enhancement_history = final_state.get("enhancement_history", [])

        summary = {
            "detection_count": len(detections),
            "detections": detections,
            "quality_report": quality_report,
            "audit_report": audit_report,
        }

        # Build execution log
        execution_log = [
            f"[System] Started face detection pipeline (max iterations: {max_iterations}).",
        ]
        for i, step in enumerate(enhancement_history, 1):
            execution_log.append(f"[Self-Healing] Iteration {i}: Applied {step}")
        execution_log.append(
            f"[System] Completed in {elapsed_ms:.0f}ms | "
            f"Iterations: {final_state.get('iteration_count', 1)} | "
            f"Verdict: {audit_report.get('verdict', 'N/A')}"
        )

        # Map enhancement history to errors_healed format
        errors_healed = [
            {"step": f"iteration_{i+1}", "action": step, "success": True}
            for i, step in enumerate(enhancement_history)
        ]

        agents_invoked = ["detector_node", "quality_node"]
        if enhancement_history:
            agents_invoked.append("enhancer_node")
        agents_invoked.append("auditor_node")

        status = "SUCCESS"
        verdict = audit_report.get("verdict", "")
        if "FAILED" in verdict:
            status = "FAILED"
        elif "SELF_HEALING" in verdict:
            status = "PARTIAL_RECOVERY"

        return UniversalResult(
            project_name=self.get_name(),
            status=status,
            execution_time_ms=elapsed_ms,
            agents_invoked=agents_invoked,
            execution_log=execution_log,
            summary=summary,
            visualizations=visualizations,
            errors_healed=errors_healed,
            metadata={"iteration_count": final_state.get("iteration_count", 1)},
        )

    def render_results(self, st_module, result: UniversalResult) -> None:
        from platform_views.face_detection_view import render_face_detection_results
        render_face_detection_results(st_module, result)
