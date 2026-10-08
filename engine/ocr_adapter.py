"""OCR Multi-Agent System adapter for the Universal Platform."""
import sys
import os
import time
import tempfile
import base64
from pathlib import Path
from typing import Any, Dict, Tuple

from pathlib import Path

# Source project root (bundled in repo or local scratch)
_BUNDLED_ROOT = Path(__file__).parent.parent / "bundled" / "ocr"
_SCRATCH_ROOT = Path(r"C:\Users\panka\.gemini\antigravity\scratch\ocr_multiagent_system")
_SOURCE_ROOT = str(_BUNDLED_ROOT if _BUNDLED_ROOT.exists() else _SCRATCH_ROOT)

from .base_adapter import BaseProjectAdapter, UniversalResult, scoped_project_environment

# Sample data files available in the source project
SAMPLE_FILES = [
    "document_clean.png",
    "document_skewed_noisy.png",
    "license_plate_clean.png",
    "license_plate_dark.png",
    "invoice_clean.png",
    "invoice_with_math_error.png",
    "contract_agreement.txt",
    "invoice_official.pdf",
    "invoice_line_items.csv",
]


class OCRAdapter(BaseProjectAdapter):
    """Adapter wrapping the OCR Multi-Agent System."""

    def get_name(self) -> str:
        return "ocr_system"

    def get_description(self) -> str:
        return (
            "Multi-format document OCR with domain-specific specialists "
            "(documents, license plates, invoices), mathematical audit, "
            "and self-healing error resolution."
        )

    def is_available(self) -> Tuple[bool, str]:
        try:
            with scoped_project_environment(_SOURCE_ROOT):
                from ocr_agentic_system.graph.workflow import OCRMultiAgentGraph  # noqa: F401
            return True, "Ready"
        except Exception as exc:
            return False, f"Import error: {exc}"

    def get_graph_definition(self) -> Dict[str, Any]:
        return {
            "nodes": [
                {"name": "preprocessor", "role": "CV Image Enhancement & Deskewing"},
                {"name": "ocr", "role": "RapidOCR + PyTesseract Engine"},
                {"name": "orchestrator", "role": "Domain Classifier & Router"},
                {"name": "doc_specialist", "role": "Document Digitizer & Indexer"},
                {"name": "plate_specialist", "role": "License Plate ANPR Validator"},
                {"name": "invoice_specialist", "role": "Invoice Scanner & Math Auditor"},
                {"name": "error_resolver", "role": "Self-Healing Error Resolution Loop"},
                {"name": "postprocessor", "role": "Final Output Compiler"},
            ],
            "edges": [
                {"from": "preprocessor", "to": "ocr", "label": "always"},
                {"from": "ocr", "to": "orchestrator", "label": "always"},
                {"from": "orchestrator", "to": "doc_specialist", "label": "document"},
                {"from": "orchestrator", "to": "plate_specialist", "label": "license_plate"},
                {"from": "orchestrator", "to": "invoice_specialist", "label": "invoice"},
                {"from": "doc_specialist", "to": "postprocessor", "label": "valid"},
                {"from": "doc_specialist", "to": "error_resolver", "label": "invalid"},
                {"from": "plate_specialist", "to": "postprocessor", "label": "valid"},
                {"from": "plate_specialist", "to": "error_resolver", "label": "invalid"},
                {"from": "invoice_specialist", "to": "postprocessor", "label": "valid"},
                {"from": "invoice_specialist", "to": "error_resolver", "label": "invalid"},
                {"from": "error_resolver", "to": "preprocessor", "label": "retry loop"},
                {"from": "error_resolver", "to": "postprocessor", "label": "healed / fallback"},
            ],
        }

    def render_input_controls(self, st_module) -> Dict[str, Any]:
        st_module.markdown("### 📄 OCR Controls")

        input_mode = st_module.radio(
            "Input Mode", ["Sample Files", "Upload File"], horizontal=True, key="ocr_input_mode"
        )
        inputs: Dict[str, Any] = {"input_mode": input_mode}

        sample_options = SAMPLE_FILES

        sample_labels = {
            "document_clean.png": "📄 Standard Document (Clean)",
            "document_skewed_noisy.png": "📄 Skewed & Noisy Document",
            "license_plate_clean.png": "🚗 License Plate (Clean)",
            "license_plate_dark.png": "🚗 License Plate (Night/Dark)",
            "invoice_clean.png": "🧾 Standard Invoice (Clean)",
            "invoice_with_math_error.png": "🧾 Invoice (Math Corruption)",
            "contract_agreement.txt": "📝 Legal Contract (Plaintext)",
            "invoice_official.pdf": "📑 PDF Document (Official)",
            "invoice_line_items.csv": "📊 CSV Spreadsheet (Table)",
        }

        if input_mode == "Sample Files":
            sample_choice = st_module.selectbox(
                "Sample Document",
                sample_options,
                index=0,
                format_func=lambda s: sample_labels.get(s, s),
                key="ocr_sample",
            )
            inputs["file_path"] = os.path.join(_SOURCE_ROOT, "sample_data", sample_choice)
            inputs["sample_file"] = sample_choice
        else:
            uploaded = st_module.file_uploader(
                "Upload Document",
                type=["png", "jpg", "jpeg", "tiff", "pdf", "txt", "csv"],
                key="ocr_upload",
            )
            if uploaded:
                temp_path = os.path.join(tempfile.gettempdir(), uploaded.name)
                with open(temp_path, "wb") as f:
                    f.write(uploaded.getbuffer())
                inputs["file_path"] = temp_path
            else:
                inputs["file_path"] = None

        # Autonomous Multi-Agent Routing: The AI Orchestrator classifies & routes automatically
        inputs["task_type"] = "auto"
        inputs["max_retries"] = 2
        return inputs

    def execute(self, inputs: Dict[str, Any]) -> UniversalResult:
        with scoped_project_environment(_SOURCE_ROOT):
            from ocr_agentic_system.graph.workflow import OCRMultiAgentGraph
            from config import OUTPUT_DIR

            file_path = inputs.get("file_path")
            if not file_path and inputs.get("sample_file"):
                file_path = os.path.join(_SOURCE_ROOT, "sample_data", inputs["sample_file"])

            # Fallback to default document if none specified or file doesn't exist
            if not file_path or not os.path.exists(file_path):
                file_path = os.path.join(_SOURCE_ROOT, "sample_data", "document_clean.png")

            task_type = inputs.get("task_type", "auto")
            max_retries = inputs.get("max_retries", 2)

            if not file_path or not os.path.exists(file_path):
                return UniversalResult(
                    project_name=self.get_name(),
                    status="FAILED",
                    summary={"error": "No valid file provided or file not found."},
                )

            t0 = time.perf_counter()

            out_dir = str(OUTPUT_DIR / "ocr")
            os.makedirs(out_dir, exist_ok=True)

            graph = OCRMultiAgentGraph(output_dir=out_dir)
            state = graph.run(file_path=file_path, task_type=task_type, max_retries=max_retries)

            elapsed_ms = (time.perf_counter() - t0) * 1000

        final_output = state.get("final_output", {})
        status = final_output.get("workflow_status", state.get("status", "completed"))

        # Encode preprocessed image to base64 if available
        visualizations: Dict[str, Any] = {}
        prep_path = state.get("preprocessed_image_path")
        if prep_path and os.path.exists(prep_path):
            with open(prep_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                visualizations["preprocessed_image"] = "data:image/png;base64," + b64

        errors_healed = final_output.get("error_history", [])

        # Determine agents invoked
        classified_type = state.get("classified_type", final_output.get("document_type"))
        agents_invoked = ["preprocessor", "ocr", "orchestrator"]
        specialist_map = {
            "document": "doc_specialist",
            "license_plate": "plate_specialist",
            "invoice": "invoice_specialist",
        }
        if classified_type in specialist_map:
            agents_invoked.append(specialist_map[classified_type])
        if errors_healed:
            agents_invoked.append("error_resolver")
        agents_invoked.append("postprocessor")

        summary = {
            "final_output": final_output,
            "classified_type": classified_type,
            "ocr_confidence": final_output.get("ocr_confidence_score"),
            "classification_confidence": final_output.get("classification_confidence"),
            "routing_reason": final_output.get("routing_reason"),
        }

        metadata = {
            "extracted_data": final_output.get("extracted_data", {}),
            "file_path": file_path,
            "original_file_path": state.get("original_file_path"),
            "full_raw_text": state.get("full_raw_text"),
            "quality_metrics": final_output.get("quality_metrics"),
            "preprocessing_history": final_output.get("preprocessing_history"),
        }

        return UniversalResult(
            project_name=self.get_name(),
            status=status,
            execution_time_ms=elapsed_ms,
            agents_invoked=agents_invoked,
            execution_log=[],
            summary=summary,
            visualizations=visualizations,
            errors_healed=errors_healed,
            metadata=metadata,
        )

    def render_results(self, st_module, result: UniversalResult) -> None:
        from platform_views.ocr_view import render_ocr_results
        render_ocr_results(st_module, result)
