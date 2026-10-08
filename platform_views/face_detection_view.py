"""
Face Detection Dashboard View — Live Multi-Agent Face Diagnostics
==================================================================
Renders live Face Detection results with side-by-side visual inspection
(Original vs YuNet Deep Neural Network Detections), real-time quality
metrics (Blur / Luminance / Contrast), and IoU verification audit certificates.
"""
import streamlit as st


def render_face_detection_results(st_module, result=None):
    """Render the native Face Detection dashboard view."""
    if result is None:
        # Standby view before pipeline execution
        st_module.markdown("""
        <div style="background:#0f172a; border:1px solid #1e293b; border-radius:14px; padding:32px 24px; text-align:center; margin-top:12px;">
            <div style="font-size:42px; margin-bottom:10px;">👤</div>
            <h2 style="color:#f8fafc; font-size:20px; font-weight:700; margin:0 0 8px 0;">
                Multi-Agent Face Detection & Self-Healing Platform
            </h2>
            <p style="color:#94a3b8; font-size:14px; max-width:620px; margin:0 auto 16px auto; line-height:1.6;">
                Autonomous 4-Agent Pipeline powered by Deep Learning YuNet DNN, real-time quality inspection (Blur, Luminance, Contrast), CLAHE self-healing, and IoU audit verification.
            </p>
            <div style="display:inline-flex; align-items:center; gap:8px; background:rgba(56,189,248,0.1); border:1px solid rgba(56,189,248,0.3); padding:8px 18px; border-radius:10px; color:#38bdf8; font-size:13px; font-weight:600;">
                <span>👈 Select a <strong>Gallery Photo</strong> or test pattern in the sidebar, then click <strong>🚀 Execute Pipeline</strong></span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Extract result fields
    summary = result.summary or {}
    vis = result.visualizations or {}
    detections = summary.get("detections", [])
    detection_count = summary.get("detection_count", len(detections))
    quality_report = summary.get("quality_report", {})
    audit_report = summary.get("audit_report", {})

    orig_b64 = vis.get("original_image")
    out_b64 = vis.get("output_image")

    primary_conf = detections[0].get("confidence", 0.0) if detections else 0.0
    quality_status = quality_report.get("status", "NORMAL")
    quality_score = quality_report.get("quality_score", 0.0)
    audit_verdict = audit_report.get("verdict", "PASSED")
    iou_score = audit_report.get("iou_vs_ground_truth")

    # 1. KPI Telemetry Bar
    kpi1, kpi2, kpi3, kpi4 = st_module.columns(4)
    with kpi1:
        st_module.metric("👤 Faces Detected", f"{detection_count} Face{'s' if detection_count != 1 else ''}")
    with kpi2:
        conf_label = f"{primary_conf*100:.1f}%" if primary_conf <= 1.0 else f"{primary_conf:.1f}%"
        st_module.metric("🎯 Detection Confidence", conf_label, "YuNet DNN")
    with kpi3:
        st_module.metric("🔬 Image Quality", f"{quality_score:.1f} / 100", quality_status)
    with kpi4:
        audit_display = "PASSED ✅" if "PASSED" in audit_verdict else audit_verdict
        st_module.metric("🛡️ Audit Certification", audit_display, f"IoU: {iou_score:.2f}" if iou_score is not None else "Verified")

    st_module.markdown("---")

    # 2. Side-by-Side Dual Viewport
    st_module.markdown("### 📷 Dual Camera Viewport — Original vs Detection & Landmarks")
    col_left, col_right = st_module.columns(2, gap="medium")

    with col_left:
        st_module.markdown("**Original Input Capture**")
        if orig_b64:
            st_module.markdown(
                f'<div style="background:#000; border:1px solid #334155; border-radius:10px; overflow:hidden; text-align:center; padding:4px;">'
                f'<img src="{orig_b64}" style="max-height:380px; width:100%; object-fit:contain; display:block;"/>'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            st_module.info("Original image preview unavailable.")

    with col_right:
        st_module.markdown("**YuNet DNN Face Detections (Bounding Box & Confidence)**")
        if out_b64:
            st_module.markdown(
                f'<div style="background:#000; border:2px solid #10b981; border-radius:10px; overflow:hidden; text-align:center; padding:4px;">'
                f'<img src="{out_b64}" style="max-height:380px; width:100%; object-fit:contain; display:block;"/>'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            st_module.info("Detection visualization preview unavailable.")

    st_module.markdown("---")

    # 3. Deep Telemetry & Diagnostics
    t1, t2, t3 = st_module.tabs(["🔬 Quality Metrics", "🛡️ Audit & Self-Healing Trail", "📐 Bounding Box Geometry"])

    with t1:
        qc1, qc2, qc3 = st_module.columns(3)
        with qc1:
            blur_val = quality_report.get("blur_score", 0.0)
            st_module.metric("Laplacian Blur Variance", f"{blur_val:.1f}", "Sharp" if blur_val > 100 else "Blurry")
        with qc2:
            lum_val = quality_report.get("luminance", 0.0)
            st_module.metric("Mean Luminance (L/Y)", f"{lum_val:.1f}", "Optimal" if 40 <= lum_val <= 210 else "Extreme")
        with qc3:
            con_val = quality_report.get("contrast", 0.0)
            st_module.metric("RMS Contrast", f"{con_val:.1f}")

        issues = quality_report.get("issues", [])
        if issues:
            st_module.warning(f"⚠️ Quality Issues Detected: {', '.join(issues)}")
        else:
            st_module.success("✨ Image quality passed all optical inspection thresholds.")

    with t2:
        st_module.markdown(f"**Audit Verdict:** `{audit_verdict}`")
        st_module.markdown(f"**Self-Healing Iterations Applied:** `{audit_report.get('self_healing_iterations', 0)}`")
        applied_enhancements = audit_report.get("applied_enhancements", [])
        if applied_enhancements:
            st_module.markdown("**Applied Self-Healing Techniques:**")
            for enh in applied_enhancements:
                st_module.markdown(f"- 🔧 `{enh}`")
        else:
            st_module.success("✨ First-pass detection succeeded with zero degraded iterations required.")

    with t3:
        if detections:
            for i, det in enumerate(detections, 1):
                st_module.markdown(f"**Face #{i}** — Engine: `{det.get('detection_method', 'yunet_dnn')}` • Confidence: **{det.get('confidence', 0.0):.2f}** • Bounding Box `[x, y, w, h]`: `{det.get('bbox')}`")
        else:
            st_module.info("No face bounding boxes detected in this frame.")
