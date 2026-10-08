"""
LangGraph Multi-Agent OCR Workflow.
Orchestrates:
- Preprocessor Agent (Adaptive image enhancement & dynamic re-filtering)
- OCR Engine (RapidOCR / PyTesseract)
- Orchestrator Agent (Task classification and dynamic routing)
- Specialists (Document Digitizer, License Plate Recognizer, Invoice Scanner)
- Error Resolver Agent (Self-healing loop for error correction and re-execution)
- Postprocessor (Final compilation & packaging)
"""
import os
import time
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END

from ..core.state import OCRWorkflowState, ErrorRecord
from ..engine.ocr_engine import get_ocr_engine
from ..engine.document_loader import DocumentLoader
from ..agents.preprocessor_agent import PreprocessorAgent
from ..agents.orchestrator_agent import OrchestratorAgent
from ..agents.document_digitizer_agent import DocumentDigitizerAgent
from ..agents.license_plate_agent import LicensePlateAgent
from ..agents.invoice_scanner_agent import InvoiceScannerAgent
from ..agents.error_resolver_agent import ErrorResolverAgent
import logging

logger = logging.getLogger("OCRWorkflow")

class OCRMultiAgentGraph:
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or os.path.join(os.getcwd(), "ocr_output")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize component agents and loaders
        self.doc_loader = DocumentLoader(cache_dir=os.path.join(self.output_dir, "loaded_media"))
        self.preprocessor = PreprocessorAgent(output_dir=os.path.join(self.output_dir, "preprocessed"))
        self.orchestrator = OrchestratorAgent()
        self.doc_agent = DocumentDigitizerAgent()
        self.plate_agent = LicensePlateAgent()
        self.invoice_agent = InvoiceScannerAgent()
        self.error_resolver = ErrorResolverAgent()
        self.ocr_engine = get_ocr_engine()
        
        # Build the graph
        self.graph = self._build_graph()

    # -------------------------------------------------------------
    # GRAPH NODES
    # -------------------------------------------------------------
    def _preprocessor_node(self, state: OCRWorkflowState) -> Dict[str, Any]:
        """Preprocesses image with adaptive CV filters or error-directed strategy."""
        image_path = state.get("image_path")
        active_strategy = state.get("active_resolution_strategy")
        existing_history = list(state.get("preprocessing_history", []))

        enhanced_path, steps, metrics = self.preprocessor.enhance(
            image_path=image_path,
            strategy=active_strategy
        )
        existing_history.extend(steps)

        return {
            "preprocessed_image_path": enhanced_path,
            "preprocessing_history": existing_history,
            "quality_metrics": metrics,
            "active_resolution_strategy": None,  # Reset active strategy
            "status": "preprocessed"
        }

    def _ocr_node(self, state: OCRWorkflowState) -> Dict[str, Any]:
        """Runs the unified OCR engine on the preprocessed image and merges direct text."""
        img_to_read = state.get("preprocessed_image_path") or state.get("image_path")
        boxes, full_text, avg_conf = self.ocr_engine.extract_text_and_boxes(img_to_read)

        direct_text = state.get("direct_text", "")
        # If direct text is embedded (digital PDF, TXT, or CSV) and richer, merge it
        if direct_text and len(direct_text.strip()) > len(full_text.strip()):
            full_text = direct_text
            if avg_conf < 0.8:
                avg_conf = 0.99  # Digital text has near-perfect confidence

        return {
            "ocr_raw_boxes": boxes,
            "full_raw_text": full_text,
            "average_ocr_confidence": avg_conf
        }

    def _orchestrator_node(self, state: OCRWorkflowState) -> Dict[str, Any]:
        """Decides which specialist agent should handle the document."""
        # If already classified in a previous cycle, retain it
        if state.get("classified_type") and state.get("classified_type") != "unknown":
            return {}

        task_override = state.get("task_type", "auto")
        full_text = state.get("full_raw_text", "")
        metrics = state.get("quality_metrics", {})
        dims = metrics.get("dimensions", {"width": 1, "height": 1})
        boxes_count = len(state.get("ocr_raw_boxes", []))

        doc_type, confidence, reason = self.orchestrator.classify_and_route(
            task_override=task_override,
            raw_text=full_text,
            dimensions=dims,
            boxes_count=boxes_count
        )

        return {
            "classified_type": doc_type,
            "classification_confidence": confidence,
            "routing_reason": reason,
            "status": "routed"
        }

    def _document_specialist_node(self, state: OCRWorkflowState) -> Dict[str, Any]:
        """Document Digitization Specialist Agent."""
        boxes = state.get("ocr_raw_boxes", [])
        text = state.get("full_raw_text", "")
        data, errs = self.doc_agent.process_document(boxes, text)
        return {
            "extracted_data": data,
            "validation_errors": errs,
            "is_valid": len(errs) == 0,
            "status": "extracted"
        }

    def _license_plate_specialist_node(self, state: OCRWorkflowState) -> Dict[str, Any]:
        """Smart Traffic / ANPR Specialist Agent."""
        boxes = state.get("ocr_raw_boxes", [])
        text = state.get("full_raw_text", "")
        data, errs = self.plate_agent.process_plate(boxes, text)
        return {
            "extracted_data": data,
            "validation_errors": errs,
            "is_valid": len(errs) == 0,
            "status": "extracted"
        }

    def _invoice_specialist_node(self, state: OCRWorkflowState) -> Dict[str, Any]:
        """Invoice & Receipt Automated Accounting Specialist Agent."""
        boxes = state.get("ocr_raw_boxes", [])
        text = state.get("full_raw_text", "")
        data, errs = self.invoice_agent.process_invoice(boxes, text)
        return {
            "extracted_data": data,
            "validation_errors": errs,
            "is_valid": len(errs) == 0,
            "status": "extracted"
        }

    def _error_resolver_node(self, state: OCRWorkflowState) -> Dict[str, Any]:
        """
        Self-Correction Agent: Resolves errors if present and enables workflow continuation.
        """
        repaired_data, is_now_valid, strategy, diagnosis = self.error_resolver.resolve(state)
        
        current_retry = state.get("retry_count", 0) + 1
        history = list(state.get("error_history", []))
        
        record: ErrorRecord = {
            "step": state.get("status", "extracted"),
            "error_type": "ValidationFailure",
            "message": "; ".join(state.get("validation_errors", [])),
            "attempt": current_retry,
            "resolution_attempted": diagnosis,
            "success": is_now_valid
        }
        history.append(record)

        return {
            "extracted_data": repaired_data,
            "is_valid": is_now_valid,
            "validation_errors": [] if is_now_valid else state.get("validation_errors", []),
            "retry_count": current_retry,
            "error_history": history,
            "active_resolution_strategy": strategy,
            "status": "resolving_error"
        }

    def _postprocessor_node(self, state: OCRWorkflowState) -> Dict[str, Any]:
        """Compiles final output artifact, formats result, and marks completion."""
        final_payload = {
            "file_type": state.get("file_type", "image"),
            "original_file_path": state.get("original_file_path", state.get("image_path")),
            "file_metadata": state.get("file_metadata", {}),
            "document_type": state.get("classified_type"),
            "classification_confidence": state.get("classification_confidence"),
            "routing_reason": state.get("routing_reason"),
            "ocr_confidence_score": state.get("average_ocr_confidence"),
            "quality_metrics": state.get("quality_metrics"),
            "preprocessing_history": state.get("preprocessing_history"),
            "extracted_data": state.get("extracted_data"),
            "retry_count": state.get("retry_count", 0),
            "errors_resolved": len(state.get("error_history", [])) > 0,
            "error_history": state.get("error_history", []),
            "workflow_status": "SUCCESS" if state.get("is_valid", True) else "PARTIAL_RECOVERY",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        return {
            "final_output": final_payload,
            "status": "completed",
            "status_message": "Multi-agent OCR workflow successfully executed."
        }

    # -------------------------------------------------------------
    # CONDITIONAL EDGES / ROUTING LOGIC
    # -------------------------------------------------------------
    def _route_after_orchestrator(self, state: OCRWorkflowState) -> Literal["doc_specialist", "plate_specialist", "invoice_specialist"]:
        doc_type = state.get("classified_type", "document")
        if doc_type == "license_plate":
            return "plate_specialist"
        elif doc_type == "invoice":
            return "invoice_specialist"
        else:
            return "doc_specialist"

    def _route_after_specialist(self, state: OCRWorkflowState) -> Literal["postprocessor", "error_resolver"]:
        is_valid = state.get("is_valid", False)
        errors = state.get("validation_errors", [])
        if is_valid and not errors:
            return "postprocessor"
        return "error_resolver"

    def _route_after_error_resolver(self, state: OCRWorkflowState) -> Literal["preprocessor", "specialist_reentry", "postprocessor"]:
        # If in-memory correction succeeded, proceed to postprocessor
        if state.get("is_valid", False):
            return "postprocessor"
        
        # If an image reprocess strategy was chosen and retries remain, loop back to preprocessor
        strategy = state.get("active_resolution_strategy")
        retries = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 2)
        
        if strategy and retries <= max_retries:
            return "preprocessor"

        # Otherwise continue to postprocessor as best-effort
        return "postprocessor"

    # -------------------------------------------------------------
    # BUILD THE GRAPH
    # -------------------------------------------------------------
    def _build_graph(self):
        builder = StateGraph(OCRWorkflowState)

        # Register nodes
        builder.add_node("preprocessor", self._preprocessor_node)
        builder.add_node("ocr", self._ocr_node)
        builder.add_node("orchestrator", self._orchestrator_node)
        builder.add_node("doc_specialist", self._document_specialist_node)
        builder.add_node("plate_specialist", self._license_plate_specialist_node)
        builder.add_node("invoice_specialist", self._invoice_specialist_node)
        builder.add_node("error_resolver", self._error_resolver_node)
        builder.add_node("postprocessor", self._postprocessor_node)

        # Entry point
        builder.set_entry_point("preprocessor")

        # Fixed transitions
        builder.add_edge("preprocessor", "ocr")
        builder.add_edge("ocr", "orchestrator")

        # Routing from orchestrator to specialist
        builder.add_conditional_edges(
            "orchestrator",
            self._route_after_orchestrator,
            {
                "doc_specialist": "doc_specialist",
                "plate_specialist": "plate_specialist",
                "invoice_specialist": "invoice_specialist"
            }
        )

        # Specialists to validation check
        for spec in ["doc_specialist", "plate_specialist", "invoice_specialist"]:
            builder.add_conditional_edges(
                spec,
                self._route_after_specialist,
                {
                    "postprocessor": "postprocessor",
                    "error_resolver": "error_resolver"
                }
            )

        # Error resolver self-correction loop or continuation
        builder.add_conditional_edges(
            "error_resolver",
            self._route_after_error_resolver,
            {
                "preprocessor": "preprocessor",  # Self-healing loop back to enhancement
                "postprocessor": "postprocessor"   # Continue workflow
            }
        )

        builder.add_edge("postprocessor", END)

        return builder.compile()

    def run(self, file_path: str, task_type: str = "auto", max_retries: int = 2, page_number: int = 0) -> Dict[str, Any]:
        """
        Executes the LangGraph Multi-Agent pipeline on an Image, PDF, TXT, or CSV file.
        """
        loaded = self.doc_loader.load_file(file_path, page_number=page_number)

        initial_state: OCRWorkflowState = {
            "image_path": loaded["rendered_image_path"],
            "original_file_path": loaded["file_path"],
            "file_type": loaded["file_type"],
            "direct_text": loaded["direct_text"],
            "file_metadata": loaded["metadata"],
            "task_type": task_type,
            "retry_count": 0,
            "max_retries": max_retries,
            "preprocessing_history": [],
            "error_history": [],
            "validation_errors": [],
            "is_valid": False,
            "status": "initialized"
        }

        final_state = self.graph.invoke(initial_state)
        return final_state
