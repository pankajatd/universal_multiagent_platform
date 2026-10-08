"""
Streamlit Web Application: LangGraph Multi-Agent OCR Platform.
Interactive visual dashboard with real-time agent execution,
error resolution inspection, and multi-domain structured extractions.
"""
import os
import json
import tempfile
import streamlit as st
from PIL import Image

from ocr_agentic_system.graph.workflow import OCRMultiAgentGraph
from ocr_agentic_system.utils.synthetic_generator import create_synthetic_datasets

st.set_page_config(
    page_title="LangGraph Multi-Agent OCR Platform",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-success { background-color: #DCFCE7; color: #166534; }
    .badge-warning { background-color: #FEF9C3; color: #854D0E; }
    .badge-info { background-color: #E0F2FE; color: #075985; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🔍 LangGraph Multi-Agent OCR Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Self-Correcting Multi-Agent System for Document Archiving, Smart Traffic ANPR, and Invoice Extraction</div>', unsafe_allow_html=True)

# Generate or load synthetic samples
sample_paths = create_synthetic_datasets(os.path.join(os.getcwd(), "sample_data"))

# Sidebar Controls
st.sidebar.header("⚙️ Configuration & Input")

input_mode = st.sidebar.radio(
    "Choose Input Source:",
    options=["📂 Upload Your Own File", "📋 Use Preloaded Sample Scenario"],
    index=0
)

# Determine file path
file_path = None
uploaded_file = None

if input_mode == "📂 Upload Your Own File":
    uploaded_file = st.sidebar.file_uploader(
        "Upload a File (.PDF, .TXT, .CSV, .PNG, .JPG):", 
        type=["pdf", "txt", "csv", "png", "jpg", "jpeg", "tiff"],
        help="Upload any PDF invoice/document, TXT transcript, CSV table, or Image file."
    )
    if uploaded_file is not None:
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, uploaded_file.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        file_path = temp_path
        st.sidebar.success(f"Loaded: `{uploaded_file.name}`")
    else:
        st.sidebar.info("👆 Please drag and drop or browse a PDF, TXT, CSV, or Image above.")

else:
    sample_choice = st.sidebar.selectbox(
        "Select Preloaded Scenario:",
        options=[
            "⚠️ Invoice with Math Error (Self-Healing Demo) [.PNG]",
            "📑 Official Invoice Document [.PDF]",
            "📝 Commercial Agreement [.TXT]",
            "📊 Invoice Line Items Table [.CSV]",
            "📄 Paper Document (Archiving & Search) [.PNG]",
            "📄 Skewed & Noisy Document [.PNG]",
            "🚗 Clean License Plate (Smart Traffic) [.PNG]",
            "🚗 Dark/Inverted License Plate [.PNG]",
            "🧾 Clean Accounting Invoice [.PNG]"
        ],
        index=0  # Default to self-healing demo
    )
    sample_key_map = {
        "📄 Paper Document (Archiving & Search) [.PNG]": "document_clean",
        "📄 Skewed & Noisy Document [.PNG]": "document_noisy",
        "🚗 Clean License Plate (Smart Traffic) [.PNG]": "license_plate_clean",
        "🚗 Dark/Inverted License Plate [.PNG]": "license_plate_dark",
        "🧾 Clean Accounting Invoice [.PNG]": "invoice_clean",
        "⚠️ Invoice with Math Error (Self-Healing Demo) [.PNG]": "invoice_with_math_error",
        "📑 Official Invoice Document [.PDF]": "invoice_pdf",
        "📝 Commercial Agreement [.TXT]": "text_document",
        "📊 Invoice Line Items Table [.CSV]": "invoice_csv"
    }
    key = sample_key_map.get(sample_choice)
    file_path = sample_paths.get(key)

task_mode = st.sidebar.selectbox(
    "Target Domain / Specialist:",
    options=["auto", "document", "license_plate", "invoice"],
    format_func=lambda x: {
        "auto": "🤖 Auto-Detect (Orchestrator)",
        "document": "📄 Paper Document Digitizer",
        "license_plate": "🚗 License Plate Recognition (ANPR)",
        "invoice": "🧾 Invoice & Receipt Scanner"
    }[x]
)

max_retries = st.sidebar.slider("Max Error Self-Correction Retries:", min_value=1, max_value=5, value=2)

# Execute Graph Button
run_analysis = st.sidebar.button("🚀 Run Multi-Agent OCR Workflow", type="primary")

# Display System Architecture Info in expander
with st.expander("ℹ️ Multi-Agent Architecture & Error Resolution Workflow"):
    st.markdown("""
    ```mermaid
    flowchart LR
        Input["Input File\n(PDF, TXT, CSV, Image)"] --> Loader["📥 Document Loader\n(Render / Direct Text)"]
        Loader --> Preprocessor["🛠️ Preprocessor Agent\n(Deskew, CLAHE, Denoise)"]
        Preprocessor --> OCR["👁️ Unified OCR Engine\n(RapidOCR / Direct Text)"]
        OCR --> Orchestrator["🧠 Orchestrator Agent\n(Domain Classification)"]
        
        Orchestrator -->|Document| DocAgent["📄 Document Digitizer\n(Layout, Search Index)"]
        Orchestrator -->|License Plate| PlateAgent["🚗 License Plate Agent\n(ANPR, Traffic Meta)"]
        Orchestrator -->|Invoice| InvAgent["🧾 Invoice Scanner\n(Accounting, Math Audit)"]
        
        DocAgent --> Validation{"Validation Check"}
        PlateAgent --> Validation
        InvAgent --> Validation
        
        Validation -->|Errors Detected| ErrorResolver["🩺 Error Resolver Agent\n(Self-Correction Loop)"]
        ErrorResolver -->|Re-filter Image| Preprocessor
        ErrorResolver -->|Direct Repair| Postprocessor["📦 Postprocessor Agent\n(Packaging & Export)"]
        Validation -->|Clean| Postprocessor
        Postprocessor --> EndNode(["Final Output"])
    ```
    """)

if file_path and os.path.exists(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader(f"📁 Source Input File ({ext.upper()})")
        if ext in [".png", ".jpg", ".jpeg", ".tiff"]:
            st.image(file_path, use_container_width=True)
        elif ext == ".pdf":
            st.info(f"📑 PDF File Loaded: `{os.path.basename(file_path)}`")
            # Render page preview
            try:
                import pymupdf
                doc = pymupdf.open(file_path)
                page = doc[0]
                pix = page.get_pixmap(dpi=150)
                temp_pdf_prev = os.path.join(tempfile.gettempdir(), "pdf_preview.png")
                pix.save(temp_pdf_prev)
                st.image(temp_pdf_prev, caption="PDF Page 1 Preview", use_container_width=True)
                doc.close()
            except Exception as e:
                st.write(f"PDF Preview not available: {e}")
        elif ext == ".csv":
            st.info(f"📊 Tabular CSV File: `{os.path.basename(file_path)}`")
            import pandas as pd
            df = pd.read_csv(file_path)
            st.dataframe(df, use_container_width=True)
        elif ext == ".txt":
            st.info(f"📝 Text File: `{os.path.basename(file_path)}`")
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            st.text_area("File Content", content, height=260)

    if run_analysis or "last_result" in st.session_state:
        if run_analysis:
            with st.spinner("Executing LangGraph Multi-Agent Workflow on loaded file..."):
                graph = OCRMultiAgentGraph()
                result = graph.run(file_path=file_path, task_type=task_mode, max_retries=max_retries)
                st.session_state["last_result"] = result
        
        result = st.session_state.get("last_result", {})
        final_out = result.get("final_output", {})
        doc_type = final_out.get("document_type", "unknown")
        
        with col2:
            st.subheader("⚙️ Preprocessed & Enhanced View")
            prep_path = result.get("preprocessed_image_path")
            if prep_path and os.path.exists(prep_path):
                st.image(prep_path, caption="Vision Engine Input", use_container_width=True)
            else:
                st.info("Direct digital stream ingested.")
            
            prep_steps = final_out.get("preprocessing_history", [])
            st.write(f"**Applied CV / Normalization:** `{', '.join(prep_steps) if prep_steps else 'Direct Ingestion'}`")
            st.write(f"**Source Format:** `{final_out.get('file_type', 'image').upper()}`")

        # Status Summary Metrics
        st.markdown("---")
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        mcol1.metric("Classified Domain", doc_type.upper(), f"Conf: {final_out.get('classification_confidence', 0):.2f}")
        mcol2.metric("Confidence Score", f"{final_out.get('ocr_confidence_score', 0):.1%}")
        
        has_errors_resolved = final_out.get("errors_resolved", False)
        status_label = "Self-Healed (Success)" if has_errors_resolved else "Clean Pass"
        mcol3.metric("Error Resolution", status_label, f"Retries: {final_out.get('retry_count', 0)}")
        mcol4.metric("Workflow Outcome", final_out.get("workflow_status", "COMPLETED"))

        # Error Resolution Notification Banner
        if has_errors_resolved:
            st.success("✨ **Self-Healing Agent Intercepted and Resolved Errors!** The pipeline detected validation discrepancies, executed autonomous corrections, and continued without interruption.")

        # Tabbed Details
        tab_ext, tab_err, tab_raw, tab_exp = st.tabs([
            "📊 Structured Domain Extraction", 
            "🩺 Error Resolution Audit Trail", 
            "📝 Raw OCR Detections", 
            "💾 Export Artifacts"
        ])

        # TAB 1: STRUCTURED EXTRACTION
        with tab_ext:
            ext = final_out.get("extracted_data", {})
            if doc_type == "license_plate":
                st.markdown("### 🚗 Smart Traffic ANPR Output")
                pcol1, pcol2 = st.columns(2)
                with pcol1:
                    st.markdown(f"**Registration Mark:** <h1 style='color:#1E3A8A;'>{ext.get('plate_number')}</h1>", unsafe_allow_html=True)
                    st.write(f"**Format Standard:** `{ext.get('matched_jurisdiction_format')}`")
                    st.write(f"**Character Length:** `{ext.get('character_count')} chars`")
                    st.write(f"**Raw OCR Token:** `{ext.get('original_ocr_raw')}`")
                with pcol2:
                    tmeta = ext.get("traffic_metadata", {})
                    st.markdown("**Traffic Telemetry & Enforcement:**")
                    st.json(tmeta)

            elif doc_type == "invoice":
                st.markdown("### 🧾 Automated Accounting Data Entry")
                icol1, icol2 = st.columns(2)
                with icol1:
                    st.write(f"**Merchant / Vendor:** `{ext.get('vendor_name')}`")
                    st.write(f"**Invoice Number:** `{ext.get('invoice_number')}`")
                    st.write(f"**Billing Date:** `{ext.get('invoice_date')}`")
                with icol2:
                    fin = ext.get("financial_summary", {})
                    curr = ext.get("currency", "$")
                    st.markdown(f"**Subtotal:** {curr}{(fin.get('subtotal') or 0.0):.2f}")
                    st.markdown(f"**Tax / VAT:** {curr}{(fin.get('tax') or 0.0):.2f}")
                    st.markdown(f"### Grand Total: {curr}{(fin.get('grand_total') or 0.0):.2f}")

                st.markdown("#### Parsed Line Items:")
                line_items = ext.get("line_items", [])
                if line_items:
                    st.table(line_items)
                else:
                    st.info("No itemized line rows detected.")

            else: # document
                st.markdown("### 📄 Paper Document Archival & Search Summary")
                st.write(f"**Document Title:** `{ext.get('title')}`")
                st.write(f"**Total Words:** `{ext.get('total_word_count')}` | **Est. Reading Time:** `{ext.get('estimated_reading_time_minutes')} min`")
                
                st.markdown("#### Full-Text Search Keywords Index:")
                kw_data = ext.get("search_index", {}).get("top_keywords", [])
                if kw_data:
                    kws = [f"**{k['keyword']}** ({k['count']})" for k in kw_data]
                    st.markdown(" • ".join(kws))

                st.markdown("#### Extracted Layout Text:")
                st.text_area("Document Content", ext.get("raw_text", ""), height=220)

        # TAB 2: ERROR RESOLUTION AUDIT TRAIL
        with tab_err:
            st.markdown("### 🩺 Autonomous Error Resolver Log")
            err_history = final_out.get("error_history", [])
            if err_history:
                for idx, ev in enumerate(err_history, 1):
                    with st.container():
                        st.markdown(f"#### Incident #{idx}: `{ev.get('error_type')}` (Attempt #{ev.get('attempt')})")
                        st.error(f"**Validation Issue:** {ev.get('message')}")
                        st.success(f"**Corrective Action Executed:** {ev.get('resolution_attempted')}")
                        st.write(f"**Resolution Outcome:** {'✅ Resolved & Continued' if ev.get('success') else '⚠️ Re-filtered'}")
                        st.markdown("---")
            else:
                st.info("No validation failures detected. Document passed validation on the first pass.")

        # TAB 3: RAW OCR DETECTIONS
        with tab_raw:
            st.markdown("### 📝 Raw OCR Bounding Boxes & Confidence Scores")
            boxes = result.get("ocr_raw_boxes", [])
            if boxes:
                st.dataframe(boxes, use_container_width=True)
            else:
                st.info("No raw bounding boxes available.")

        # TAB 4: EXPORT ARTIFACTS
        with tab_exp:
            st.markdown("### 💾 Export Structured Results")
            json_str = json.dumps(final_out, indent=2)
            st.download_button(
                label="📥 Download Structured JSON",
                data=json_str,
                file_name=f"ocr_result_{doc_type}.json",
                mime="application/json"
            )
            
            if doc_type == "document":
                md_content = ext.get("markdown_representation", "")
                st.download_button(
                    label="📥 Download Markdown Document",
                    data=md_content,
                    file_name="digitized_document.md",
                    mime="text/markdown"
                )
else:
    st.info("👈 Please select a sample scenario from the sidebar or upload an image to begin.")
