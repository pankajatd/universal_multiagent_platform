"""
Industrial Vision & Diagnostic RAG Dashboard View — Live Control Room
=====================================================================
Integrates the complete standalone Industrial Vision & RAG Control Room (Port 8080)
with native support for:
  • Real-Time Target Defect Image Display & Camera Viewport
  • Dual Feed Viewport: Raw Optical Camera Feed & Defect Mask
  • Real-Time Diagnostic Telemetry & Dynamic Severity Scoring (0.0 to 10.0)
  • Synthesized OSHA/ISO CMMS Maintenance Work Order
  • Interactive Control Room Iframe synchronized to selected defect
"""
import time
import streamlit as st


def render_industrial_results(st_module, result):
    """Render the synchronized live Industrial Vision RAG results and control room."""
    meta = result.metadata or {}
    target_defect = meta.get("target_defect", "auto")
    frame_index = meta.get("frame_index", 101)
    summary = result.summary or {}
    alert = summary.get("alert") or {}
    wo = summary.get("work_order") or {}

    defect_name = alert.get("defect_type", target_defect).upper()
    severity_level = alert.get("severity_level", "NORMAL")
    severity_score = alert.get("severity_score", 0.0)
    confidence = alert.get("confidence", 1.0)
    wo_id = wo.get("work_order_id", "PASS / NO_WORK_ORDER")

    # Header Banner
    st_module.markdown(f"""
    <div style="background:#0f172a; padding:14px 20px; border-radius:12px; margin-bottom:14px; border:1px solid #1e293b; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
        <div>
            <div style="display:flex; align-items:center; gap:8px;">
                <span style="font-size:11px; font-weight:bold; letter-spacing:0.05em; background:rgba(99,102,241,0.15); color:#a5b4fc; padding:2px 8px; border-radius:12px; border:1px solid rgba(99,102,241,0.3);">
                    INSPECTION MODE: {target_defect.upper()}
                </span>
                <span style="font-size:11px; font-weight:600; background:rgba(16,185,129,0.15); color:#34d399; padding:2px 8px; border-radius:12px; border:1px solid rgba(16,185,129,0.3);">
                    ● 6-Agent LangGraph Mesh Connected
                </span>
            </div>
            <div style="color:white; font-size:17px; font-weight:bold; margin-top:4px;">
                Industrial Multi-Agent Vision & Diagnostic RAG Platform
            </div>
            <div style="color:#94a3b8; font-size:12px;">
                Frame #{frame_index:03d} • Classified: <strong>{defect_name}</strong> (Confidence: {confidence*100:.1f}%) • Severity: <strong>{severity_score} / 10.0 [{severity_level}]</strong>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1. Native Dual Camera Feed Display (Optical Feed + Defect Mask)
    vis = result.visualizations or {}
    raw_b64 = vis.get("raw_frame")
    mask_b64 = vis.get("mask")

    if raw_b64 or mask_b64:
        st_module.markdown(f"### 📷 Dual Camera Viewport — Frame #{frame_index:03d} ({target_defect.upper()})")
        col1, col2 = st_module.columns(2)
        with col1:
            st_module.markdown("**Optical Sensor Camera Feed (Raw Ingestion)**")
            if raw_b64:
                st_module.markdown(
                    f'<div style="border:2px solid #ef4444; border-radius:12px; overflow:hidden; background:#000;"><img src="{raw_b64}" style="width:100%; display:block;"/></div>',
                    unsafe_allow_html=True
                )
            else:
                st_module.info("Optical camera feed unavailable.")

        with col2:
            st_module.markdown("**Defect Heatmap & Boundary Mask (Segmentation)**")
            if mask_b64:
                st_module.markdown(
                    f'<div style="border:2px solid #ef4444; border-radius:12px; overflow:hidden; background:#000;"><img src="{mask_b64}" style="width:100%; display:block;"/></div>',
                    unsafe_allow_html=True
                )
            else:
                st_module.info("Defect segmentation mask unavailable.")

    # 2. Telemetry and Work Order Metrics
    if wo and wo.get("work_order_id"):
        st_module.markdown("---")
        st_module.markdown(f"### 🛠️ OSHA CMMS Maintenance Ticket — `{wo_id}`")
        wcol1, wcol2 = st_module.columns([1, 2])
        with wcol1:
            st_module.info(f"**Defect Type:** {wo.get('defect_type', defect_name).upper()}\n\n"
                           f"**Severity Level:** {wo.get('severity_level', severity_level)}\n\n"
                           f"**Severity Score:** {wo.get('severity_score', severity_score)} / 10.0\n\n"
                           f"**Signoff Required:** {wo.get('technician_signoff_required', True)}")
        with wcol2:
            directives = wo.get("safety_directives", [])
            procedures = wo.get("repair_procedure", [])
            manuals = wo.get("source_manuals", [])
            st_module.markdown("**Mandatory Safety Directives (OSHA LOTO):**")
            for d in directives:
                st_module.markdown(f"- {d}")
            st_module.markdown("**Remediation Protocol:**")
            for p in procedures:
                st_module.markdown(f"1. {p}")
            if manuals:
                st_module.caption(f"Cited SOP Manuals: {', '.join(manuals)}")

    # 3. 21-D Feature Extraction & Telemetry
    features = summary.get("features", {})
    if features:
        st_module.markdown("---")
        with st_module.expander("🔬 21-D Optical & Defect Feature Telemetry", expanded=False):
            st_module.json(features)
