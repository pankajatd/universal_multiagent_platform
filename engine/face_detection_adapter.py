import os
import sys
import time
import cv2
import base64
import numpy as np
from typing import Any, Dict, Tuple
from pathlib import Path

# Source project root (bundled in repo or local scratch)
_BUNDLED_ROOT = Path(__file__).parent.parent / "bundled" / "face"
_SCRATCH_ROOT = Path(r"C:\Users\panka\.gemini\antigravity\scratch\multi_agent_face_detection")
_SOURCE_ROOT = str(_BUNDLED_ROOT if _BUNDLED_ROOT.exists() else _SCRATCH_ROOT)

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

        input_mode = st_module.radio(
            "Input Mode",
            ["Sample Gallery", "Synthetic Streamer", "Upload Photo"],
            index=0,
            key="face_input_mode",
            horizontal=False,
        )

        sample_gallery_dir = Path(_SOURCE_ROOT) / "FaceDetection_Test_images"
        gallery_images = ["Img1.webp", "Img2.webp", "Img3.jpg", "Img4.jpg", "Img5.jpg", "Img6.jpg"]
        gallery_labels = {
            "Img1.webp": "🖼️ Img 1 — Portrait (Clean)",
            "Img2.webp": "🖼️ Img 2 — Low Light & Shadow",
            "Img3.jpg": "🖼️ Img 3 — Outdoor Natural Light",
            "Img4.jpg": "🖼️ Img 4 — High Definition Profile",
            "Img5.jpg": "🖼️ Img 5 — Group & Multi-Face",
            "Img6.jpg": "🖼️ Img 6 — Side Profile Angle",
        }

        inputs: Dict[str, Any] = {
            "input_mode": input_mode,
            "max_iterations": 3,
        }

        if input_mode == "Sample Gallery":
            selected_sample = st_module.selectbox(
                "Gallery Photo",
                gallery_images,
                index=0,
                format_func=lambda f: gallery_labels.get(f, f),
                key="face_gallery_select",
            )
            inputs["image_path"] = str(sample_gallery_dir / selected_sample)
            inputs["sample_name"] = selected_sample
        elif input_mode == "Synthetic Streamer":
            deg = st_module.selectbox(
                "Degradation Pattern",
                ["none", "underexposed", "blurred", "overexposed"],
                format_func=lambda d: {
                    "none": "✨ None (Clean Standard)",
                    "underexposed": "🌑 Underexposed (Low Light / Dark)",
                    "blurred": "💨 Motion Blur",
                    "overexposed": "☀️ Overexposed (High Glare)",
                }.get(d, d),
                key="face_synth_deg",
            )
            sev = st_module.select_slider(
                "Degradation Severity",
                options=["mild", "moderate", "severe"],
                value="moderate",
                key="face_synth_sev",
            )
            inputs["degradation_type"] = deg
            inputs["severity"] = sev
        else:
            uploaded = st_module.file_uploader(
                "Upload Face Photo",
                type=["jpg", "jpeg", "png", "webp"],
                key="face_upload",
            )
            inputs["upload_file"] = uploaded

        inputs["max_iterations"] = st_module.slider(
            "Max Self-Healing Retries",
            min_value=1,
            max_value=5,
            value=3,
            key="face_max_iter",
        )

        return inputs

    def execute(self, inputs: Dict[str, Any]) -> UniversalResult:
        with scoped_project_environment(_SOURCE_ROOT):
            from src.graph.workflow import MultiAgentFaceOrchestrator
            from src.generator.face_streamer import SyntheticFaceStreamer

            t0 = time.perf_counter()
            input_mode = inputs.get("input_mode", "Sample Gallery")
            max_iterations = inputs.get("max_iterations", 3)

            image = None
            metadata: Dict[str, Any] = {}

            if input_mode == "Sample Gallery" and inputs.get("image_path") and os.path.exists(inputs["image_path"]):
                image = cv2.imread(inputs["image_path"])
                metadata = {"source": inputs.get("sample_name", "gallery")}
            elif input_mode == "Synthetic Streamer":
                streamer = SyntheticFaceStreamer()
                degradation_type = inputs.get("degradation_type", "none")
                severity_map = {"mild": 0.25, "moderate": 0.5, "severe": 0.8}
                severity = severity_map.get(inputs.get("severity", "moderate"), 0.5)
                image, metadata = streamer.generate_face_image(
                    degradation_type=degradation_type, severity=severity
                )
            elif input_mode == "Upload Photo" and inputs.get("upload_file") is not None:
                upload_file = inputs["upload_file"]
                file_bytes = np.asarray(bytearray(upload_file.read()), dtype=np.uint8)
                image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                metadata = {"source": getattr(upload_file, "name", "upload")}
            else:
                # Default fallback: load first gallery image if exists, else synthetic
                gallery_first = Path(_SOURCE_ROOT) / "FaceDetection_Test_images" / "Img1.webp"
                if gallery_first.exists():
                    image = cv2.imread(str(gallery_first))
                    metadata = {"source": "Img1.webp"}
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
                    cv2.rectangle(output_image, (x, y), (x + w, y + h), (0, 255, 128), 2)
                    label = f"YuNet {conf*100:.0f}%" if conf <= 1.0 else f"YuNet {conf:.0f}%"
                    cv2.putText(output_image, label, (x, max(15, y - 6)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 128), 2)

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
