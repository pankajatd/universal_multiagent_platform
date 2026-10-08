"""
State definition for the Multi-Agent OCR LangGraph System.
"""
from typing import TypedDict, List, Dict, Any, Optional, Literal

TaskType = Literal["auto", "document", "license_plate", "invoice"]
DocumentClass = Literal["document", "license_plate", "invoice", "unknown"]
WorkflowStatus = Literal["initialized", "preprocessed", "routed", "extracted", "resolving_error", "completed", "failed"]

class OCRBox(TypedDict, total=False):
    text: str
    confidence: float
    box: List[List[float]]  # [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]

class ErrorRecord(TypedDict):
    step: str
    error_type: str
    message: str
    attempt: int
    resolution_attempted: Optional[str]
    success: bool

class OCRWorkflowState(TypedDict, total=False):
    # Input
    image_path: str
    original_file_path: str
    file_type: str  # 'image', 'pdf', 'txt', 'csv'
    direct_text: str  # embedded digital text from PDF/TXT/CSV
    file_metadata: Dict[str, Any]
    task_type: TaskType  # user override or 'auto'
    
    # Preprocessing
    image_metadata: Dict[str, Any]
    preprocessed_image_path: str
    preprocessing_history: List[str]
    quality_metrics: Dict[str, Any]  # blur_score, contrast, skew_angle
    
    # Orchestration & Classification
    classified_type: DocumentClass
    classification_confidence: float
    routing_reason: str
    
    # Raw OCR Output
    ocr_raw_boxes: List[OCRBox]
    full_raw_text: str
    average_ocr_confidence: float
    
    # Specialist Extraction Output
    extracted_data: Dict[str, Any]
    
    # Validation & Error Handling
    is_valid: bool
    validation_errors: List[str]
    needs_error_resolution: bool
    retry_count: int
    max_retries: int
    error_history: List[ErrorRecord]
    active_resolution_strategy: Optional[str]
    
    # Final Result
    final_output: Dict[str, Any]
    status: WorkflowStatus
    status_message: str
