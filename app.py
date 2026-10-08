"""
Universal Multi-Agent LangGraph Platform — Streamlit Dashboard
==============================================================
A single unified dashboard to select, execute, and visualize any of the
three multi-agent LangGraph projects:
  1. Industrial Vision & Diagnostic RAG
  2. Multi-Agent Face Detection
  3. OCR Multi-Agent System

Launch:
    streamlit run app.py
"""
import sys
import os
import time
import json
from pathlib import Path

# Ensure the platform root is on sys.path so relative imports work
PLATFORM_ROOT = Path(__file__).parent
if str(PLATFORM_ROOT) not in sys.path:
    sys.path.insert(0, str(PLATFORM_ROOT))

# Ensure shared venv site-packages is always accessible
_SITE_PACKAGES = r"C:\Users\panka\.gemini\antigravity\scratch\ocr_multiagent_system\venv_ocr\Lib\site-packages"
if os.path.isdir(_SITE_PACKAGES) and _SITE_PACKAGES not in sys.path:
    sys.path.insert(1, _SITE_PACKAGES)

import streamlit as st
import subprocess

# Auto-relaunch via run_platform.py if user runs "python app.py" directly
if not st.runtime.exists():
    runner = PLATFORM_ROOT / "run_platform.py"
    sys.exit(subprocess.call([sys.executable, str(runner)] + sys.argv[1:]))

from config import PROJECT_METADATA
from engine.project_registry import ProjectRegistry

# ──────────────────────────────────────────────────────────────────────
# Page Configuration
# ──────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Universal Multi-Agent Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────
# Custom CSS
# ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Compact top padding to fit full dashboard in one screen */
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 1rem !important;
    }

    /* Header gradient */
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 0.7rem 1.4rem;
        border-radius: 10px;
        margin-bottom: 0.8rem;
        color: white;
        border: 1px solid #334155;
    }
    .main-header h1 { margin: 0; font-size: 1.35rem; }
    .main-header p { margin: 0.2rem 0 0; opacity: 0.8; font-size: 0.85rem; }

    /* Compact sidebar so all controls and Execute button fit without scrolling */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0.35rem !important;
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 0.8rem !important;
        padding-bottom: 0.8rem !important;
    }
    [data-testid="stSidebarUserContent"] {
        padding-top: 0.4rem !important;
    }
    .project-card {
        border: 1px solid;
        border-radius: 8px;
        padding: 0.4rem 0.7rem;
        margin-bottom: 0.2rem;
    }
    .project-card h4 { margin: 0; font-size: 0.95rem; }
    .project-card p { margin: 0.15rem 0 0; font-size: 0.73rem; opacity: 0.75; line-height: 1.25; }

    /* Agent flow badges */
    .agent-badge {
        display: inline-block;
        background: #1e3a5f;
        color: #7dd3fc;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.75rem;
        margin: 0.15rem;
        font-family: monospace;
    }

    /* Status badges */
    .status-success { background: #065f46; color: #6ee7b7; padding: 0.3rem 0.8rem; border-radius: 8px; font-weight: bold; }
    .status-partial { background: #78350f; color: #fbbf24; padding: 0.3rem 0.8rem; border-radius: 8px; font-weight: bold; }
    .status-failed  { background: #7f1d1d; color: #fca5a5; padding: 0.3rem 0.8rem; border-radius: 8px; font-weight: bold; }

    /* Streamlit tweaks */
    .stMetric { border: 1px solid #333; border-radius: 8px; padding: 0.5rem; }
    div[data-testid="stExpander"] { border: 1px solid #333; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────
# Register all project adapters
# ──────────────────────────────────────────────────────────────────────
ProjectRegistry.register_all()

# ──────────────────────────────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🧠 Universal Multi-Agent LangGraph Platform</h1>
    <p>Select a project • Configure inputs • Execute the multi-agent pipeline • View results</p>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────
# Sidebar — Project Selection
# ──────────────────────────────────────────────────────────────────────
st.sidebar.markdown('<div style="font-weight:700; font-size:13px; color:#e2e8f0; margin-bottom:3px;">🎯 Project Selector</div>', unsafe_allow_html=True)

project_keys = list(ProjectRegistry.list_projects().keys())
project_labels = []
for key in project_keys:
    meta = PROJECT_METADATA.get(key, {})
    icon = meta.get("icon", "📦")
    name = meta.get("display_name", key)
    project_labels.append(f"{icon} {name}")

selected_idx = st.sidebar.selectbox(
    "Choose a project",
    range(len(project_keys)),
    format_func=lambda i: project_labels[i],
    key="project_selector",
)
selected_key = project_keys[selected_idx]
selected_meta = PROJECT_METADATA.get(selected_key, {})

# Detect project switch and purge stale execution state
if "active_project" not in st.session_state or st.session_state["active_project"] != selected_key:
    st.session_state["active_project"] = selected_key
    st.session_state.pop("last_result", None)
    st.session_state.pop("last_project", None)
    st.session_state.pop("executed_defect", None)

# Show project description
st.sidebar.markdown(f"""
<div class="project-card" style="border-color: {selected_meta.get('color', '#555')};">
    <h4>{selected_meta.get('icon', '📦')} {selected_meta.get('display_name', selected_key)}</h4>
    <p>{selected_meta.get('description', '')}</p>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────
# Get Adapter
# ──────────────────────────────────────────────────────────────────────
adapter = ProjectRegistry.get(selected_key)

if adapter is None:
    st.error(f"❌ Project `{selected_key}` adapter could not be loaded.")
    st.stop()

available, msg = adapter.is_available()
if not available:
    st.error(f"❌ Project `{selected_key}`: {msg}")
    st.stop()

# ──────────────────────────────────────────────────────────────────────
# Sidebar — Project-specific Input Controls
# ──────────────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
inputs = adapter.render_input_controls(st.sidebar)

# ──────────────────────────────────────────────────────────────────────
# Sidebar — Execute Button (Unified for all projects)
# ──────────────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
execute_btn = st.sidebar.button(
    "🚀 Execute Pipeline",
    use_container_width=True,
    type="primary",
)

# ──────────────────────────────────────────────────────────────────────
# Graph Visualization (always shown)
# ──────────────────────────────────────────────────────────────────────
graph_def = adapter.get_graph_definition()
nodes = graph_def.get("nodes", [])
edges = graph_def.get("edges", [])

with st.expander(f"🔗 Agent Workflow Graph — {selected_meta.get('display_name', selected_key)}", expanded=False):
    # Build mermaid diagram
    mermaid_lines = ["graph LR"]
    for node in nodes:
        if isinstance(node, dict):
            name = node["name"]
            role = node.get("role", name)
            safe_role = role.replace('"', "'")
            mermaid_lines.append(f'    {name}["{name}\\n{safe_role}"]')
        else:
            mermaid_lines.append(f'    {node}["{node}"]')

    for edge in edges:
        if isinstance(edge, dict):
            src = edge["from"]
            dst = edge["to"]
            label = edge.get("label", "")
            safe_label = label.replace('"', "'")
            if label:
                mermaid_lines.append(f'    {src} -->|"{safe_label}"| {dst}')
            else:
                mermaid_lines.append(f"    {src} --> {dst}")
        elif isinstance(edge, (list, tuple)) and len(edge) >= 2:
            src, dst = edge[0], edge[1]
            mermaid_lines.append(f"    {src} --> {dst}")

    mermaid_code = "\n".join(mermaid_lines)
    st.markdown(f"```mermaid\n{mermaid_code}\n```")

    # Also show agent list
    st.markdown("**Agents in this pipeline:**")
    for node in nodes:
        if isinstance(node, dict):
            st.markdown(f'<span class="agent-badge">{node["name"]}</span> — {node.get("role", "")}', unsafe_allow_html=True)
        else:
            st.markdown(f'<span class="agent-badge">{node}</span>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────
# Execution & View Rendering (Unified across all 3 platforms)
# ──────────────────────────────────────────────────────────────────────
if execute_btn:
    with st.spinner(f"⚙️ Running {selected_meta.get('display_name', selected_key)} pipeline..."):
        try:
            result = adapter.execute(inputs)
            st.session_state["last_result"] = result
            st.session_state["last_project"] = selected_key
        except Exception as exc:
            st.error(f"❌ Pipeline execution failed: {exc}")
            st.stop()

# Show results if available for active project
if "last_result" in st.session_state and st.session_state.get("last_project") == selected_key:
    result = st.session_state["last_result"]

    # ── Compact Results Header & Status Bar ──
    status = result.status
    if status in ("SUCCESS", "COMPLETED", "HEALED"):
        status_class = "status-success"
    elif "PARTIAL" in str(status).upper() or status == "HEALED":
        status_class = "status-partial"
    else:
        status_class = "status-failed"

    agent_html = " → ".join(
        f'<span class="agent-badge">{a}</span>' for a in result.agents_invoked
    ) if result.agents_invoked else "direct"

    st.markdown(f"""
    <div style="background:#1e293b; border:1px solid #334155; border-radius:10px; padding:7px 14px; margin-top:2px; margin-bottom:6px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
        <div style="display:flex; align-items:center; gap:10px;">
            <span class="{status_class}">{status}</span>
            <span style="color:white; font-weight:700; font-size:13px;">{selected_meta.get('icon', '')} {selected_meta.get('display_name', selected_key)}</span>
            <span style="color:#94a3b8; font-size:11px; font-family:monospace;">⏱️ {result.execution_time_ms:.0f} ms • 🤖 {len(result.agents_invoked)} Agents • 🔧 {len(result.errors_healed)} Healed</span>
        </div>
        <div style="font-size:11px; font-family:monospace;">
            {agent_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Tabbed Results ──
    tab_structured, tab_log, tab_healing, tab_raw = st.tabs([
        "📊 Structured Output & Inspection",
        "📜 Execution Log",
        "🔧 Self-Healing Audit",
        "🗂️ Raw State",
    ])

    with tab_structured:
        adapter.render_results(st, result)

    with tab_log:
        st.subheader("📜 Execution Log")
        if result.execution_log:
            for i, entry in enumerate(result.execution_log, 1):
                st.text(f"{i:3d}. {entry}")
        else:
            st.info("No execution log entries recorded.")

    with tab_healing:
        st.subheader("🔧 Self-Healing Audit Trail")
        if result.errors_healed:
            for i, record in enumerate(result.errors_healed, 1):
                if isinstance(record, dict):
                    with st.container():
                        st.markdown(f"**Healing Event #{i}**")
                        for k, v in record.items():
                            st.markdown(f"- **{k}:** {v}")
                        st.markdown("---")
                else:
                    st.markdown(f"**{i}.** {record}")
        else:
            st.success("✨ Clean execution pass — zero unhandled errors.")

    with tab_raw:
        st.subheader("🗂️ Raw State / Summary")
        raw_display = {
            "project_name": result.project_name,
            "status": result.status,
            "execution_time_ms": result.execution_time_ms,
            "agents_invoked": result.agents_invoked,
            "summary": result.summary,
            "metadata": result.metadata,
            "errors_healed": result.errors_healed,
        }
        def _make_serializable(obj):
            if isinstance(obj, dict):
                return {k: _make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_make_serializable(v) for v in obj]
            elif isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            else:
                return str(obj)

        st.json(json.dumps(_make_serializable(raw_display), indent=2, default=str))

else:
    # Standby views per project
    if selected_key == "face_detection":
        from platform_views.face_detection_view import render_face_detection_results
        render_face_detection_results(st, None)
    elif selected_key == "industrial_vision_rag":
        st.markdown("---")
        st.markdown("""
        <div style="background:#0f172a; border:1px solid #1e293b; border-radius:14px; padding:32px 24px; text-align:center; margin-top:12px;">
            <div style="font-size:42px; margin-bottom:10px;">🏭</div>
            <h2 style="color:#f8fafc; font-size:20px; font-weight:700; margin:0 0 8px 0;">
                Industrial Multi-Agent Vision & Diagnostic RAG Platform
            </h2>
            <p style="color:#94a3b8; font-size:14px; max-width:620px; margin:0 auto 16px auto; line-height:1.6;">
                Continuous Conveyor Stream, Real-Time Defect Classification & Autonomous Self-Healing.
            </p>
            <div style="display:inline-flex; align-items:center; gap:8px; background:rgba(99,102,241,0.1); border:1px solid rgba(99,102,241,0.3); padding:8px 18px; border-radius:10px; color:#a5b4fc; font-size:13px; font-weight:600;">
                <span>👈 Select a <strong>Defect Type</strong> in the sidebar, then click <strong>🚀 Execute Pipeline</strong></span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("---")
        st.markdown("""
        <div style="background:#0f172a; border:1px solid #1e293b; border-radius:14px; padding:32px 24px; text-align:center; margin-top:12px;">
            <div style="font-size:42px; margin-bottom:10px;">📄</div>
            <h2 style="color:#f8fafc; font-size:20px; font-weight:700; margin:0 0 8px 0;">
                OCR Multi-Agent System
            </h2>
            <p style="color:#94a3b8; font-size:14px; max-width:620px; margin:0 auto 16px auto; line-height:1.6;">
                Multi-format OCR with intelligent autonomous routing (Documents, License Plates, Invoices) and mathematical audit.
            </p>
            <div style="display:inline-flex; align-items:center; gap:8px; background:rgba(14,165,233,0.1); border:1px solid rgba(14,165,233,0.3); padding:8px 18px; border-radius:10px; color:#38bdf8; font-size:13px; font-weight:600;">
                <span>👈 Select a <strong>Sample Document</strong> in the sidebar, then click <strong>🚀 Execute Pipeline</strong></span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
# ──────────────────────────────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div style="text-align:center; opacity:0.5; font-size:0.8rem;">'
    '🧠 Universal Multi-Agent LangGraph Platform — '
    'Unifying Industrial Vision RAG • Face Detection • OCR Systems'
    '</div>',
    unsafe_allow_html=True,
)
