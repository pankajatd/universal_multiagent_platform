from typing import List, Dict, Any, Optional, TypedDict
import numpy as np

class ErrorRecord(TypedDict, total=False):
    component: str             # e.g., 'vision_agent', 'diagnostic_agent', 'rag_agent'
    error_type: str            # e.g., 'image_degraded', 'feature_schema_invalid', 'rag_low_relevance', 'runtime_exception'
    message: str              # Description of the issue
    traceback: Optional[str]   # Stack trace if available
    resolved: bool             # Whether SelfHealingAgent resolved it
    recovery_strategy: Optional[str] # Action taken to resolve

class HealingRecord(TypedDict, total=False):
    timestamp: str
    target_component: str
    failure_type: str
    action_taken: str
    status: str
    details: Dict[str, Any]

class AgenticState(TypedDict, total=False):
    # Streaming & Visual Inputs
    frame_index: int
    raw_frame: Optional[np.ndarray]
    processed_frame: Optional[np.ndarray]
    mask: Optional[np.ndarray]
    
    # Image Quality Metrics
    image_quality: Dict[str, float]
    
    # Feature Extraction (21 dimensions)
    features: Dict[str, float]
    
    # Diagnostics & Classification
    alert: Dict[str, Any]
    
    # RAG & Maintenance
    search_queries: List[str]
    retrieved_docs: List[Dict[str, Any]]
    retrieval_relevance_score: float
    work_order: Optional[Dict[str, Any]]
    
    # Human-in-the-Loop & Compliance
    requires_human_signoff: bool
    human_approved: bool
    
    # Error Tracking & Autonomous Self-Healing
    errors: List[ErrorRecord]
    healing_actions: List[HealingRecord]
    retry_count: int
    status: str  # "PROCESSING", "NEEDS_HEALING", "HEALED", "COMPLETED", "FAILED"
    
    # Multi-Agent Routing & Lifecycle
    next_agent: str
    execution_log: List[str]
