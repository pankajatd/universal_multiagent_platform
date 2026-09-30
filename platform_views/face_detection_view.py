"""
Face Detection Dashboard View — Live Interactive Inspector
===========================================================
Integrates the complete standalone Face Detection dashboard (Port 8050)
with native support for:
  • Upload Photos (drag-and-drop & multi-file upload)
  • Delete Uploads (one-click gallery purge)
  • Auto Play All (continuous 2.2s slideshow carousel)
  • Play Uploads Only
  • Step Prev / Step Next navigation
  • Interactive Thumbnails Gallery
  • Side-by-Side: Input Image vs Healed/Detected Face with Bounding Boxes
"""
import streamlit as st


def render_face_detection_results(st_module, result):
    """Render the complete live interactive Face Detection dashboard."""
    st_module.markdown(
        """
        <div style="display:flex; justify-content:flex-end; margin-bottom:4px;">
            <a href="http://localhost:8050" target="_blank" style="display:inline-flex; align-items:center; gap:6px; background:#0284c7; color:white; padding:4px 12px; border-radius:6px; text-decoration:none; font-size:11px; font-weight:600; box-shadow:0 2px 6px rgba(2,132,199,0.3);">
                ↗ Open in Dedicated Tab (Port 8050)
            </a>
        </div>
        <iframe src="http://localhost:8050" width="100%" height="680" style="border:none; border-radius:12px; background:#0b1120; overflow:hidden;"></iframe>
        """,
        unsafe_allow_html=True
    )
