"""
OCR Multi-Agent Dashboard View — High-Resolution Readable Document Inspector
=============================================================================
Renders OCR results with crystal-clear readable document viewports (Source & Preprocessed),
interactive view switcher (Original / Preprocessed / Side-by-Side), dynamic text zoom controls
(Bigger 150% / Large 200% / Fit), classification telemetry, and structured domain intelligence.
"""
import os
import base64
import html
import streamlit as st


def _file_to_b64(path):
    """Read a local file and return a base64 data URI."""
    if path and os.path.exists(path):
        try:
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                ext = os.path.splitext(path)[1].lower().replace(".", "")
                if ext == "jpg":
                    ext = "jpeg"
                elif ext not in ("png", "jpeg", "webp", "gif"):
                    ext = "png"
                return f"data:image/{ext};base64,{b64}"
        except Exception:
            return None
    return None


def render_ocr_results(st_module, result):
    """Render high-resolution, readable OCR multi-agent results."""
    summary = result.summary or {}
    metadata = result.metadata or {}
    vis = result.visualizations or {}
    final_output = summary.get("final_output", {})

    file_path = metadata.get("file_path")
    classified_type = str(summary.get("classified_type", "unknown")).lower()
    ocr_conf = summary.get("ocr_confidence")
    cls_conf = summary.get("classification_confidence")
    routing_reason = summary.get("routing_reason") or ""
    ext_data = metadata.get("extracted_data", {})
    raw_text = metadata.get("full_raw_text") or ext_data.get("full_raw_text") or ""

    # Source & preprocessed image data URIs
    src_b64 = _file_to_b64(file_path)
    prep_b64 = vis.get("preprocessed_image") or src_b64

    # Two-Column Dashboard Viewport (Give left visual column 58% width in Side-by-Side for maximum readability)
    col_left, col_right = st_module.columns([1.18, 0.82], gap="medium")

    # ──────────────────────────────────────────────────────────────────────────
    # LEFT COLUMN: High-Resolution Readable Visual Inspection & Classification
    # ──────────────────────────────────────────────────────────────────────────
    with col_left:
        # Header with view switcher
        hdr_col1, hdr_col2 = st_module.columns([1, 1.25])
        with hdr_col1:
            st_module.markdown(
                '<div style="font-size:12px; font-weight:700; color:#38bdf8; margin-top:3px;">'
                '📷 Visual Document Inspector'
                '</div>',
                unsafe_allow_html=True
            )
        with hdr_col2:
            view_mode = st_module.radio(
                "Document View",
                ["Original", "Preprocessed", "Side-by-Side"],
                index=2,  # Default to Side-by-Side as requested
                horizontal=True,
                key="ocr_view_mode",
                label_visibility="collapsed"
            )

        # Zoom level controller for large, clear, human-readable text
        zcol1, zcol2 = st_module.columns([0.45, 1.55])
        with zcol1:
            st_module.markdown('<div style="font-size:11px; font-weight:600; color:#94a3b8; margin-top:3px;">🔍 Text Zoom:</div>', unsafe_allow_html=True)
        with zcol2:
            zoom_mode = st_module.radio(
                "Text Zoom",
                ["Bigger (150%)", "Large (200%)", "Fit Page"],
                index=0,  # Default to 150% Bigger text
                horizontal=True,
                key="ocr_zoom_mode",
                label_visibility="collapsed"
            )

        # Sizing and scaling CSS
        if zoom_mode == "Bigger (150%)":
            scale_css = "min-width:350px; width:155%; height:auto;"
        elif zoom_mode == "Large (200%)":
            scale_css = "min-width:480px; width:200%; height:auto;"
        else:
            scale_css = "width:100%; height:auto;"

        is_plate = (classified_type == "license_plate")
        bg_style = "background:#0f172a;" if is_plate else "background:#ffffff;"
        border_style = "border:1px solid #334155;" if is_plate else "border:1px solid #cbd5e1; box-shadow:0 2px 10px rgba(0,0,0,0.25);"

        if is_plate:
            # License plate: Horizontal format with large, bold text
            plate_scale_css = "min-width:320px; max-height:130px;" if zoom_mode != "Fit Page" else "max-height:120px; max-width:100%;"
            if view_mode == "Side-by-Side":
                p1, p2 = st_module.columns(2, gap="small")
                with p1:
                    st_module.markdown('<div style="font-size:10px; color:#94a3b8; font-weight:bold; margin-bottom:2px;">Original Capture</div>', unsafe_allow_html=True)
                    st_module.markdown(
                        f'<div style="height:155px; overflow-x:auto; {bg_style} {border_style} border-radius:8px; display:flex; align-items:center; justify-content:center; padding:6px;">'
                        f'<img src="{src_b64}" style="{plate_scale_css} object-fit:contain; border-radius:4px; image-rendering:-webkit-optimize-contrast;"/>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                with p2:
                    st_module.markdown('<div style="font-size:10px; color:#94a3b8; font-weight:bold; margin-bottom:2px;">Preprocessed</div>', unsafe_allow_html=True)
                    st_module.markdown(
                        f'<div style="height:155px; overflow-x:auto; {bg_style} {border_style} border-radius:8px; display:flex; align-items:center; justify-content:center; padding:6px;">'
                        f'<img src="{prep_b64}" style="{plate_scale_css} object-fit:contain; border-radius:4px; image-rendering:-webkit-optimize-contrast;"/>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            else:
                active_b64 = src_b64 if view_mode == "Original" else prep_b64
                label_text = "Original Camera Capture" if view_mode == "Original" else "Denoised & Binarized Plate"
                st_module.markdown(
                    f'<div style="height:175px; {bg_style} {border_style} border-radius:8px; display:flex; flex-col items-center justify-center p-3 relative">'
                    f'<img src="{active_b64}" style="max-height:130px; max-width:100%; object-fit:contain; border-radius:4px; image-rendering:-webkit-optimize-contrast;"/>'
                    f'<span style="position:absolute; bottom:6px; right:10px; font-size:10px; color:#94a3b8; font-family:monospace;">{label_text}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        else:
            # Documents & Invoices: Full Readable Paper View with Zoom and Smooth Scrolling
            if view_mode == "Side-by-Side":
                d1, d2 = st_module.columns(2, gap="small")
                with d1:
                    st_module.markdown('<div style="font-size:10px; color:#94a3b8; font-weight:bold; margin-bottom:2px;">Original Source</div>', unsafe_allow_html=True)
                    st_module.markdown(
                        f'<div style="height:275px; max-height:275px; overflow-x:auto; overflow-y:auto; {bg_style} {border_style} border-radius:8px; padding:6px;">'
                        f'<img src="{src_b64}" style="{scale_css} display:block; border-radius:2px; image-rendering:-webkit-optimize-contrast;"/>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                with d2:
                    st_module.markdown('<div style="font-size:10px; color:#94a3b8; font-weight:bold; margin-bottom:2px;">Preprocessed (Deskewed)</div>', unsafe_allow_html=True)
                    st_module.markdown(
                        f'<div style="height:275px; max-height:275px; overflow-x:auto; overflow-y:auto; {bg_style} {border_style} border-radius:8px; padding:6px;">'
                        f'<img src="{prep_b64}" style="{scale_css} display:block; border-radius:2px; image-rendering:-webkit-optimize-contrast;"/>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            else:
                # Single view: Maximum clarity & readability!
                active_b64 = src_b64 if view_mode == "Original" else prep_b64
                label_text = "Original Raw Document (Scroll to read)" if view_mode == "Original" else "Preprocessed Deskewed & Denoised (Scroll to read)"
                st_module.markdown(
                    f'<div style="height:275px; max-height:275px; overflow-x:auto; overflow-y:auto; {bg_style} {border_style} border-radius:8px; padding:8px;">'
                    f'<div style="font-size:10px; color:#64748b; font-family:sans-serif; margin-bottom:4px; font-weight:bold;">🔍 {label_text}</div>'
                    f'<img src="{active_b64}" style="{scale_css} display:block; border-radius:2px; image-rendering:-webkit-optimize-contrast;"/>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        # Classification & Telemetry Ribbon
        ocr_conf_str = f"{ocr_conf:.1%}" if isinstance(ocr_conf, (int, float)) else "N/A"
        cls_conf_str = f"{cls_conf:.1%}" if isinstance(cls_conf, (int, float)) else "N/A"

        type_icon = "📄"
        if classified_type == "invoice":
            type_icon = "🧾"
        elif classified_type == "license_plate":
            type_icon = "🚗"

        st_module.markdown(
            f'<div style="background:#0f172a; border:1px solid #334155; border-radius:8px; padding:6px 12px; margin-top:6px; display:flex; justify-content:space-between; align-items:center; font-size:11px;">'
            f'  <span style="font-weight:700; color:#38bdf8;">{type_icon} {classified_type.upper()}</span>'
            f'  <span style="color:#cbd5e1;">OCR Conf: <strong style="color:#34d399;">{ocr_conf_str}</strong></span>'
            f'  <span style="color:#cbd5e1;">Routing Conf: <strong style="color:#a78bfa;">{cls_conf_str}</strong></span>'
            f'</div>',
            unsafe_allow_html=True
        )

        if routing_reason:
            st_module.markdown(
                f'<div style="font-size:10px; color:#64748b; margin-top:2px; truncate:true;">'
                f'  <strong>Routing:</strong> {html.escape(routing_reason)}'
                f'</div>',
                unsafe_allow_html=True
            )

    # ──────────────────────────────────────────────────────────────────────────
    # RIGHT COLUMN: Structured Intelligence & Extracted Content (Clean & Readable)
    # ──────────────────────────────────────────────────────────────────────────
    with col_right:
        st_module.markdown(
            '<div style="font-size:12px; font-weight:700; color:#a78bfa; margin-bottom:4px;">'
            '📊 Extracted Intelligence & Text Content'
            '</div>',
            unsafe_allow_html=True
        )

        if classified_type == "document":
            title = ext_data.get("title") or os.path.basename(file_path or "Document")
            word_count = ext_data.get("total_word_count", "N/A")
            reading_time = ext_data.get("estimated_reading_time_minutes", 1)
            sections_count = len(ext_data.get("sections", []))

            st_module.markdown(
                f'<div style="background:#0f172a; border:1px solid #334155; border-radius:8px; padding:8px 12px; margin-bottom:6px;">'
                f'  <div style="font-weight:700; font-size:12px; color:#f8fafc; truncate:true;">{html.escape(str(title))}</div>'
                f'  <div style="font-size:11px; color:#94a3b8; margin-top:2px;">'
                f'    📝 <strong>{word_count}</strong> words • ⏱️ <strong>{reading_time} min</strong> read • 📑 <strong>{sections_count}</strong> sections'
                f'  </div>'
                f'</div>',
                unsafe_allow_html=True
            )

            # Scrollable Raw Text Box with Large Readable Font (13px font)
            escaped_text = html.escape(raw_text if raw_text else "No raw text extracted.")
            st_module.markdown(
                f'<div style="height:250px; max-height:250px; overflow-y:auto; background:#0a0f1d; border:1px solid #334155; border-radius:8px; padding:10px 12px; font-family:monospace; font-size:13px; font-weight:500; line-height:1.55; color:#f1f5f9; white-space:pre-wrap;">'
                f'{escaped_text}'
                f'</div>',
                unsafe_allow_html=True
            )

            if ext_data.get("search_index"):
                keywords = ", ".join(list(ext_data["search_index"].keys())[:6])
                st_module.markdown(f'<div style="font-size:10px; color:#64748b; margin-top:4px;"><strong>Keywords:</strong> {keywords}</div>', unsafe_allow_html=True)

        elif classified_type == "invoice":
            vendor = ext_data.get("vendor_name", "N/A")
            inv_no = ext_data.get("invoice_number", "N/A")
            bdate = ext_data.get("billing_date", "N/A")
            fin = ext_data.get("financial_summary", {})
            curr = ext_data.get("currency", "$")
            subtotal = fin.get("subtotal", 0.0)
            tax = fin.get("tax", 0.0)
            grand_total = fin.get("grand_total", 0.0)
            math_ok = fin.get("math_verified")

            math_badge = '<span style="color:#34d399; font-weight:bold;">[Math Verified ✅]</span>' if math_ok else '<span style="color:#f87171; font-weight:bold;">[Math Check ❌]</span>'

            st_module.markdown(
                f'<div style="background:#0f172a; border:1px solid #334155; border-radius:8px; padding:8px 12px; margin-bottom:6px;">'
                f'  <div style="font-weight:700; font-size:13px; color:#f8fafc;">Vendor: {html.escape(str(vendor))}</div>'
                f'  <div style="font-size:11px; color:#94a3b8; display:flex; justify-content:space-between; margin-top:2px;">'
                f'    <span>Inv #: <strong>{inv_no}</strong> • Date: <strong>{bdate}</strong></span>'
                f'    <span>{math_badge}</span>'
                f'  </div>'
                f'</div>',
                unsafe_allow_html=True
            )

            # Financial metrics bar
            st_module.markdown(
                f'<div style="display:flex; justify-content:space-between; background:#1e293b; border:1px solid #334155; border-radius:8px; padding:6px 12px; margin-bottom:6px; font-size:11px;">'
                f'  <span>Subtotal: <strong style="color:#cbd5e1;">{curr}{subtotal:,.2f}</strong></span>'
                f'  <span>Tax: <strong style="color:#cbd5e1;">{curr}{tax:,.2f}</strong></span>'
                f'  <span>Total: <strong style="color:#34d399; font-size:12px;">{curr}{grand_total:,.2f}</strong></span>'
                f'</div>',
                unsafe_allow_html=True
            )

            # Line Items Table
            line_items = ext_data.get("line_items", [])
            if line_items:
                rows_html = ""
                for itm in line_items:
                    desc = itm.get("description", "Item")
                    qty = itm.get("quantity", 1)
                    amt = itm.get("amount", 0.0)
                    rows_html += f"<tr><td style='padding:5px 8px; border-bottom:1px solid #1e293b;'>{desc}</td><td style='padding:5px 8px; border-bottom:1px solid #1e293b; text-align:center;'>{qty}</td><td style='padding:5px 8px; border-bottom:1px solid #1e293b; text-align:right;'>{curr}{amt:,.2f}</td></tr>"

                st_module.markdown(
                    f'<div style="max-height:180px; overflow-y:auto; border:1px solid #334155; border-radius:6px; font-size:11px;">'
                    f'<table style="width:100%; border-collapse:collapse; color:#cbd5e1;">'
                    f'<thead style="background:#0f172a; color:#94a3b8;"><tr><th style="padding:5px 8px; text-align:left;">Description</th><th style="padding:5px 8px; text-align:center;">Qty</th><th style="padding:5px 8px; text-align:right;">Amount</th></tr></thead>'
                    f'<tbody>{rows_html}</tbody>'
                    f'</table>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            elif raw_text:
                escaped_text = html.escape(raw_text)
                st_module.markdown(
                    f'<div style="height:180px; max-height:180px; overflow-y:auto; background:#0a0f1d; border:1px solid #334155; border-radius:8px; padding:8px 10px; font-family:monospace; font-size:12px; color:#cbd5e1; white-space:pre-wrap;">'
                    f'{escaped_text}'
                    f'</div>',
                    unsafe_allow_html=True
                )

        elif classified_type == "license_plate":
            pnum = ext_data.get("plate_number", "UNKNOWN")
            j_format = ext_data.get("matched_jurisdiction_format", "Standard Jurisdiction")
            p_conf = ext_data.get("plate_confidence", 0.0)
            traffic = ext_data.get("traffic_metadata", {})

            st_module.markdown(
                f'<div style="background:#1e293b; border:2px solid #38bdf8; border-radius:10px; padding:18px; text-align:center; margin-bottom:8px; box-shadow:0 0 16px rgba(56,189,248,0.25);">'
                f'  <div style="font-size:26px; font-weight:800; letter-spacing:5px; color:#ffffff; font-family:monospace;">'
                f'    {html.escape(str(pnum))}'
                f'  </div>'
                f'  <div style="font-size:12px; color:#94a3b8; margin-top:6px;">'
                f'    {html.escape(str(j_format))} • Match Confidence: <strong>{p_conf:.1%}</strong>'
                f'  </div>'
                f'</div>',
                unsafe_allow_html=True
            )

            if traffic:
                st_module.markdown(
                    f'<div style="background:#0f172a; border:1px solid #334155; border-radius:8px; padding:10px 14px; font-size:12px; color:#cbd5e1;">'
                    f'  <div>🚦 <strong>Traffic Sensor:</strong> {traffic.get("camera_id", "CAM-01")} • Lane: {traffic.get("lane", 1)}</div>'
                    f'  <div style="margin-top:3px;">⚡ <strong>Estimated Speed:</strong> {traffic.get("estimated_speed_mph", 65)} mph • Status: Normal Flow</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        else:
            # Fallback display for generic text/data
            if raw_text:
                escaped_text = html.escape(raw_text)
                st_module.markdown(
                    f'<div style="height:260px; max-height:260px; overflow-y:auto; background:#0a0f1d; border:1px solid #334155; border-radius:8px; padding:8px 10px; font-family:monospace; font-size:12px; line-height:1.45; color:#e2e8f0; white-space:pre-wrap;">'
                    f'{escaped_text}'
                    f'</div>',
                    unsafe_allow_html=True
                )
            else:
                st_module.json(ext_data)
