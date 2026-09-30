# 📋 Operational Tasks & Code Walkthroughs Guide
> **Universal Multi-Agent LangGraph Platform**

This document provides a complete hands-on operational guide, command cheat-sheet, and annotated code snippets for running, testing, maintaining, and extending the Universal Multi-Agent LangGraph Platform.

---

## 📑 Table of Contents
1. [Operational Task Workflows](#-operational-task-workflows)
   - [Task 1: Environment Setup & Installation](#task-1-environment-setup--installation)
   - [Task 2: Service Launching (Unified vs Standalone)](#task-2-service-launching-unified-vs-standalone)
   - [Task 3: Automated Regression Testing](#task-3-automated-regression-testing)
   - [Task 4: Port Management & Background Daemons](#task-4-port-management--background-daemons)
   - [Task 5: Adding a New Project Adapter](#task-5-adding-a-new-project-adapter)
2. [Architectural Code Snippets](#-architectural-code-snippets)
   - [Snippet 1: Universal State Contract (`UniversalResult`)](#snippet-1-universal-state-contract-universalresult)
   - [Snippet 2: The Base Project Adapter](#snippet-2-the-base-project-adapter)
   - [Snippet 3: Dynamic Project Registry](#snippet-3-dynamic-project-registry)
   - [Snippet 4: Master Streamlit Router & Execution Loop](#snippet-4-master-streamlit-router--execution-loop)
   - [Snippet 5: Industrial Vision LangGraph Supervisor](#snippet-5-industrial-vision-langgraph-supervisor)
   - [Snippet 6: Face Detection Self-Healing Feedback Loop](#snippet-6-face-detection-self-healing-feedback-loop)
   - [Snippet 7: OCR Specialist Routing & Levenshtein Correction](#snippet-7-ocr-specialist-routing--levenshtein-correction)

---

## 🛠️ Operational Task Workflows

### Task 1: Environment Setup & Installation

#### PowerShell (Windows):
```powershell
# Navigate to the platform repository
cd C:\Users\panka\.gemini\antigravity\scratch\universal_multiagent_platform

# Create virtual environment (if not already present)
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Upgrade pip and install all core dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### Bash (macOS / Linux):
```bash
cd universal_multiagent_platform
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Task 2: Service Launching (Unified vs Standalone)

#### Launch Universal Master Hub (Port 8550)
The Master Hub allows switching between Industrial Vision, Face Detection, and Document OCR from a single web interface:
```powershell
# Auto-detects Python environment and launches Streamlit on 8550
python run_platform.py 8550
```
Access at: **`http://localhost:8550`**

#### Launch Individual Standalone Micro-Services
If you want to isolate or benchmark a single project without the master platform:

1. **Industrial Vision Dashboard (Port 8080)**:
   ```powershell
   python ..\industrial_multiagent_rag\dashboard.py
   ```
   Access at: `http://localhost:8080`

2. **Face Detection Server (Port 8050)**:
   ```powershell
   python ..\multi_agent_face_detection\app.py
   ```
   Access at: `http://localhost:8050`

---

### Task 3: Automated Regression Testing

To verify all multi-agent graph flows, adapters, and output normalizers without opening a browser:

```powershell
python test_all_three_projects.py
```

#### Verification Matrix:
| Test Component | Target Graph | Verified Outcome |
|----------------|--------------|-------------------|
| Test 1: Industrial | `industrial_multiagent_rag` | Defect classification, SOP FAISS retrieval, Quality Gate verification |
| Test 2: Face Detection | `multi_agent_face_detection` | Face detection, quality inspection, CLAHE/gamma self-healing trigger |
| Test 3: Document OCR | `ocr_multiagent_system` | Dual OCR consensus, specialist routing, typo correction |

---

### Task 4: Port Management & Background Daemons

Check which ports are active and kill dangling processes if needed:

```powershell
# Check which process is occupying port 8550 or 8080
Get-NetTCPConnection -LocalPort 8550, 8080, 8050 -ErrorAction SilentlyContinue | Select-Object LocalPort, OwningProcess, State

# Stop a process by PID
Stop-Process -Id <PID> -Force
```

---

### Task 5: Adding a New Project Adapter

When onboarding a new project into the platform:
1. Create `engine/<project_name>_adapter.py`.
2. Implement subclasses of `BaseProjectAdapter`.
3. Create `platform_views/<project_name>_view.py`.
4. Register the adapter in `engine/project_registry.py`.
5. Add project metadata in `config.py`.

---

## 💻 Architectural Code Snippets

### Snippet 1: Universal State Contract (`UniversalResult`)
*File: `engine/base_adapter.py`*

```python
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time

@dataclass
class UniversalResult:
    """Normalized result schema across all multi-agent projects."""
    project_key: str
    status: str                         # 'success', 'partial', 'failed'
    execution_time_ms: float
    agent_flow: List[str]               # Ordered list of executed agents
    self_healing_occurred: bool = False
    self_healing_details: Dict[str, Any] = field(default_factory=dict)
    structured_data: Dict[str, Any] = field(default_factory=dict)
    execution_log: List[str] = field(default_factory=list)
    raw_state: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
```

---

### Snippet 2: The Base Project Adapter
*File: `engine/base_adapter.py`*

```python
from abc import ABC, abstractmethod

class BaseProjectAdapter(ABC):
    """Abstract interface defining the contract for any multi-agent project."""
    
    @abstractmethod
    def get_name(self) -> str:
        """Human-readable display name of the system."""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """One-paragraph summary of capabilities and domain."""
        pass

    @abstractmethod
    def get_graph_definition(self) -> Dict[str, Any]:
        """Returns Mermaid diagram string and node metadata."""
        pass

    @abstractmethod
    def render_input_controls(self) -> Dict[str, Any]:
        """Renders Streamlit sidebar controls and returns user parameters."""
        pass

    @abstractmethod
    def execute(self, inputs: Dict[str, Any]) -> UniversalResult:
        """Executes the underlying LangGraph workflow and normalizes output."""
        pass

    @abstractmethod
    def render_results(self, result: UniversalResult) -> None:
        """Renders domain-specific charts, bounding boxes, or tables."""
        pass
```

---

### Snippet 3: Dynamic Project Registry
*File: `engine/project_registry.py`*

```python
import sys
from pathlib import Path
from typing import Dict, List, Optional
from engine.base_adapter import BaseProjectAdapter

class ProjectRegistry:
    """Singleton registry managing all multi-agent adapters."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._adapters = {}
            cls._instance._initialized = False
        return cls._instance

    def register(self, key: str, adapter: BaseProjectAdapter):
        self._adapters[key] = adapter

    def get(self, key: str) -> Optional[BaseProjectAdapter]:
        return self._adapters.get(key)

    def list_projects(self) -> List[Dict[str, str]]:
        return [
            {
                "key": k,
                "name": adapter.get_name(),
                "description": adapter.get_description()
            }
            for k, adapter in self._adapters.items()
        ]
```

---

### Snippet 4: Master Streamlit Router & Execution Loop
*File: `app.py`*

```python
import streamlit as st
from engine.project_registry import get_project_registry

registry = get_project_registry()
selected_key = st.sidebar.selectbox("Select Agent System", list(registry.keys()))
adapter = registry.get(selected_key)

# Render Dynamic Sidebar Inputs
user_inputs = adapter.render_input_controls()

# Execution Trigger
if st.sidebar.button("🚀 Execute Pipeline", type="primary"):
    with st.spinner("Multi-Agent Graph Executing..."):
        result = adapter.execute(user_inputs)
        st.session_state["last_result"] = result

# Tabbed Results Rendering
if "last_result" in st.session_state:
    res = st.session_state["last_result"]
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Structured Output", 
        "📜 Execution Log", 
        "🔧 Self-Healing Audit", 
        "🗂️ Raw State"
    ])
    with tab1:
        adapter.render_results(res)
    with tab2:
        for log in res.execution_log:
            st.code(log)
    with tab3:
        st.json(res.self_healing_details)
    with tab4:
        st.json(res.raw_state)
```

---

### Snippet 5: Industrial Vision LangGraph Supervisor
*Extract from: `industrial_multiagent_rag/graph.py`*

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class IndustrialState(TypedDict):
    defect_type: str
    image_features: dict
    diagnostic_report: str
    sop_documents: List[dict]
    quality_confidence: float
    healing_attempts: int

def supervisor_router(state: IndustrialState) -> str:
    """Conditional edge routing based on quality gate threshold."""
    if state["quality_confidence"] < 0.80 and state["healing_attempts"] < 2:
        return "self_healing_agent"
    return "formatter_agent"

builder = StateGraph(IndustrialState)
builder.add_node("vision_analysis", vision_analysis_agent)
builder.add_node("diagnostic_rag", diagnostic_rag_agent)
builder.add_node("self_healing_agent", self_healing_agent)
builder.add_node("formatter_agent", final_report_formatter)

builder.add_edge("vision_analysis", "diagnostic_rag")
builder.add_conditional_edges("diagnostic_rag", supervisor_router)
builder.add_edge("self_healing_agent", "diagnostic_rag")
builder.add_edge("formatter_agent", END)
graph = builder.compile()
```

---

### Snippet 6: Face Detection Self-Healing Feedback Loop
*Extract from: `multi_agent_face_detection/engine/graph.py`*

```python
def quality_conditional_edge(state: FaceDetectionState) -> str:
    """Route to Enhancer if contrast or blur falls below target threshold."""
    metrics = state["quality_metrics"]
    if (metrics["blur_variance"] < 100.0 or metrics["contrast"] < 35.0) and state["iterations"] < 3:
        return "enhancement_agent"
    return "auditor_agent"

def enhancement_agent(state: FaceDetectionState) -> FaceDetectionState:
    """Self-healing action: Applies CLAHE and unsharp masking."""
    img = state["current_image"]
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    enhanced = cv2.merge((cl, a, b))
    state["current_image"] = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    state["iterations"] += 1
    state["healing_history"].append("Applied CLAHE contrast correction")
    return state
```

---

### Snippet 7: OCR Specialist Routing & Levenshtein Correction
*Extract from: `ocr_multiagent_system/engine/nodes.py`*

```python
import re

COMMON_OCR_REPLACEMENTS = {
    r'\bT0TAL\b': 'TOTAL',
    r'\bSUBT0TAL\b': 'SUBTOTAL',
    r'\bINV0ICE\b': 'INVOICE',
    r'\bAM0UNT\b': 'AMOUNT',
    r'(\d+)[oO](\d+)': r'\1.0\2'
}

def error_resolver_agent(state: OCRState) -> OCRState:
    """Self-healing node: Cleans garbled OCR tokens using regex and heuristic dictionaries."""
    raw_text = state["extracted_text"]
    corrected = raw_text
    corrections_made = []
    
    for pattern, replacement in COMMON_OCR_REPLACEMENTS.items():
        if re.search(pattern, corrected, re.IGNORECASE):
            corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
            corrections_made.append(f"Fixed typo: {pattern} -> {replacement}")
            
    state["cleaned_text"] = corrected
    state["healing_log"] = corrections_made
    return state
```
