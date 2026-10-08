from typing import TypedDict, List, Dict, Any
import numpy as np

class AgentState(TypedDict):
    """Global state passed across agents in the LangGraph workflow."""
    current_image: np.ndarray
    original_image: np.ndarray
    metadata: Dict[str, Any]
    detections: List[Dict[str, Any]]
    quality_report: Dict[str, Any]
    iteration_count: int
    max_iterations: int
    enhancement_history: List[str]
    audit_report: Dict[str, Any]
