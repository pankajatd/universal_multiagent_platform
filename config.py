"""Universal Multi-Agent LangGraph Platform — Configuration."""
import os
from pathlib import Path

# Platform paths
PLATFORM_ROOT = Path(__file__).parent
SCRATCH_DIR = PLATFORM_ROOT.parent  # parent scratch directory

# Source project paths
PROJECT_PATHS = {
    "industrial_vision_rag": SCRATCH_DIR / "industrial_multiagent_rag",
    "face_detection": SCRATCH_DIR / "multi_agent_face_detection",
    "ocr_system": SCRATCH_DIR / "ocr_multiagent_system",
}

# Project display metadata
PROJECT_METADATA = {
    "industrial_vision_rag": {
        "display_name": "Industrial Vision & Diagnostic RAG",
        "icon": "🏭",
        "description": "Real-time industrial defect detection with 21-D feature extraction, Random Forest ML classification, SOP-based maintenance RAG, and autonomous self-healing.",
        "color": "#FF6B35",
    },
    "face_detection": {
        "display_name": "Multi-Agent Face Detection",
        "icon": "👤",
        "description": "YuNet DNN face detection with quality inspection, adaptive image enhancement self-healing loop, and IoU-based audit certification.",
        "color": "#4ECDC4",
    },
    "ocr_system": {
        "display_name": "OCR Multi-Agent System",
        "icon": "📄",
        "description": "Multi-format document OCR with domain-specific specialists (documents, license plates, invoices), mathematical audit, and self-healing error resolution.",
        "color": "#7B68EE",
    },
}

# Output directory
OUTPUT_DIR = PLATFORM_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
