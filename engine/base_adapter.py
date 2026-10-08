"""Base adapter interface for all project adapters."""
from __future__ import annotations
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager
import sys


@contextmanager
def scoped_project_environment(project_root: str):
    """
    Context manager that ensures a specific project root is at the head of sys.path,
    and isolates generic package names (like 'src') to prevent cross-project conflicts.
    """
    project_root = str(project_root)
    old_path = list(sys.path)

    # Clean out any previously loaded 'src' modules from other projects
    removed_modules = {}
    for mod_name in list(sys.modules.keys()):
        if mod_name == "src" or mod_name.startswith("src."):
            removed_modules[mod_name] = sys.modules.pop(mod_name)

    import os
    sp = r"C:\Users\panka\.gemini\antigravity\scratch\ocr_multiagent_system\venv_ocr\Lib\site-packages"
    if os.path.isdir(sp) and sp not in sys.path:
        sys.path.insert(0, sp)

    if project_root in sys.path:
        sys.path.remove(project_root)
    sys.path.insert(0, project_root)

    try:
        yield
    finally:
        sys.path[:] = old_path
        for mod_name in list(sys.modules.keys()):
            if mod_name == "src" or mod_name.startswith("src."):
                sys.modules.pop(mod_name, None)
        for k, v in removed_modules.items():
            sys.modules[k] = v


@dataclass
class UniversalResult:
    """Normalized result schema across all projects."""
    project_name: str
    status: str  # SUCCESS, PARTIAL_RECOVERY, FAILED
    execution_time_ms: float = 0.0
    agents_invoked: List[str] = field(default_factory=list)
    execution_log: List[str] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    raw_state: Dict[str, Any] = field(default_factory=dict)
    visualizations: Dict[str, Any] = field(default_factory=dict)  # key -> base64 image strings
    errors_healed: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    graph_nodes: List[Dict[str, str]] = field(default_factory=list)  # [{"name": ..., "role": ...}]
    graph_edges: List[Dict[str, str]] = field(default_factory=list)  # [{"from": ..., "to": ..., "label": ...}]


class BaseProjectAdapter(ABC):
    """Abstract adapter that each project must implement."""

    @abstractmethod
    def get_name(self) -> str:
        """Return the project registry key."""
        ...

    @abstractmethod
    def get_description(self) -> str:
        """Return a human-readable description."""
        ...

    @abstractmethod
    def get_graph_definition(self) -> Dict[str, Any]:
        """Return nodes and edges for graph visualization."""
        ...

    @abstractmethod
    def render_input_controls(self, st_module) -> Dict[str, Any]:
        """Render Streamlit sidebar controls and return collected inputs."""
        ...

    @abstractmethod
    def execute(self, inputs: Dict[str, Any]) -> UniversalResult:
        """Execute the project's LangGraph workflow and return a UniversalResult."""
        ...

    @abstractmethod
    def render_results(self, st_module, result: UniversalResult) -> None:
        """Render project-specific result visualizations in the Streamlit main area."""
        ...

    def is_available(self) -> Tuple[bool, str]:
        """Check if this project's dependencies are available. Returns (available, message)."""
        return True, "Ready"
