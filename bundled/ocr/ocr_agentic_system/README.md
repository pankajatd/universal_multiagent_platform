# 🔍 LangGraph Multi-Agent OCR & Self-Healing Platform

An agentic Optical Character Recognition (OCR) platform built with **LangGraph**, designed for high-accuracy text extraction, intelligent domain routing, and **autonomous error resolution with self-healing feedback loops**.

---

## 🎯 Key Use Cases Supported

1. **📄 Paper Document Digitizer (Archiving & Full-Text Search)**
   - Layout extraction: Headings, subheadings, paragraphs, and reading order sequencing.
   - Inverted search index creation with token positions and keyword frequency analysis.
   - Exports clean Markdown and archival JSON.

2. **🚗 License Plate Recognition (ANPR / ALPR in Smart Traffic Systems)**
   - Vehicle registration number extraction and format matching (US, UK, EU, Generic Alphanumeric).
   - Resolves character confusion (e.g. `'O'` vs `'0'`, `'I'` vs `'1'`, `'B'` vs `'8'`).
   - Simulates smart traffic telemetry: Toll gate ID, lane allocation, speed estimation, and compliance checks.

3. **🧾 Invoice & Receipt Scanner (Automated ERP Data Entry)**
   - Financial entity extraction: Vendor name, invoice ID, billing date, currency, itemized line tables.
   - **Mathematical Integrity Audit**: Validates `sum(line_items) == Subtotal` and `Subtotal + Tax == Grand Total`.
   - Reconciles decimal point shifts and missing taxes.

4. **🩺 Autonomous Error Resolver & Self-Correction Agent**
   - **Crucial Requirement**: Intercepts extraction failures, low OCR confidence, or mathematical mismatches.
   - Applies targeted healing strategies:
     - **Image Re-filtering**: Triggers deskewing, Otsu binarization, aggressive CLAHE, or color inversion.
     - **Constraint Reconciliation**: Solves missing fields and math discrepancies.
     - **Optical Confusion Repair**: Maps confusable characters according to domain syntax.
   - Cycles back into the LangGraph loop and **continues workflow execution without crashing**.

---

## 🏗️ Multi-Agent Architecture

```mermaid
flowchart TD
    Start([Input Image]) --> Preprocessor["🛠️ Preprocessor Agent\n(Deskew, CLAHE, Noise Filtering)"]
    Preprocessor --> OCR["👁️ Unified OCR Engine\n(RapidOCR ONNX / Tesseract)"]
    OCR --> Orchestrator["🧠 Orchestrator Agent\n(Domain Classification & Intent Routing)"]
    
    Orchestrator -->|Document| DocAgent["📄 Document Digitizer Agent\n(Layout & Search Indexing)"]
    Orchestrator -->|License Plate| PlateAgent["🚗 License Plate Agent\n(ANPR & Smart Traffic Telemetry)"]
    Orchestrator -->|Invoice| InvAgent["🧾 Invoice Scanner Agent\n(Accounting & Mathematical Audit)"]
    
    DocAgent --> Evaluator{"Validation Check"}
    PlateAgent --> Evaluator
    InvAgent --> Evaluator
    
    Evaluator -->|Valid| Postprocessor["📦 Postprocessor Agent\n(JSON / Markdown / Packaging)"]
    Evaluator -->|Errors Detected| ErrorResolver["🩺 Error Resolver Agent\n(Self-Correction & Diagnosis)"]
    
    ErrorResolver -->|Re-filter Image (Loop)| Preprocessor
    ErrorResolver -->|In-Memory Reconciled| Postprocessor
    
    Postprocessor --> Finish([Structured Result Delivered])
```

---

## 📁 Project Directory Structure

```text
ocr_agentic_system/
├── core/
│   ├── __init__.py
│   └── state.py                    # TypedDict State definition for LangGraph
├── engine/
│   ├── __init__.py
│   └── ocr_engine.py               # RapidOCR (ONNX) + Tesseract fallback wrapper
├── agents/
│   ├── __init__.py
│   ├── preprocessor_agent.py       # Adaptive CV filters (deskew, CLAHE, binarization)
│   ├── orchestrator_agent.py       # Domain classifier & intelligent dispatcher
│   ├── document_digitizer_agent.py # Archival document specialist & search indexer
│   ├── license_plate_agent.py      # ANPR smart traffic specialist
│   ├── invoice_scanner_agent.py    # Accounting & math integrity specialist
│   └── error_resolver_agent.py     # Self-healing loop & error recovery
├── graph/
│   ├── __init__.py
│   └── workflow.py                 # LangGraph StateGraph orchestration & conditional edges
├── utils/
│   ├── __init__.py
│   └── synthetic_generator.py      # Generates synthetic test images for all domains
├── app.py                          # Interactive Streamlit Web Dashboard
├── cli.py                          # Rich terminal CLI interface
└── README.md
```

---

## 🚀 Getting Started

### 1. Launch the Interactive Web Dashboard
Run the Streamlit application to upload any image, test preloaded scenarios, and inspect the real-time agent execution timeline:

```powershell
.\venv_ocr\Scripts\python.exe run_ocr_app.py ui
```
*Or directly via Streamlit:*
```powershell
.\venv_ocr\Scripts\streamlit.exe run ocr_agentic_system/app.py
```

### 2. Run the Command Line Interface (CLI)

**Run an automated end-to-end demo across all test datasets:**
```powershell
.\venv_ocr\Scripts\python.exe -m ocr_agentic_system.cli --demo
```

**Run on a specific image:**
```powershell
.\venv_ocr\Scripts\python.exe -m ocr_agentic_system.cli --image sample_data/invoice_with_math_error.png
```

### 3. Run Automated Unit & Integration Tests
```powershell
.\venv_ocr\Scripts\pytest.exe -v --basetemp=./tests_tmp tests/test_ocr_multiagent.py
```

---

## 💡 How Self-Healing Works in Action

When an invoice image with an OCR slip (e.g. Subtotal `$250.00` + Tax `$25.00` read with Grand Total `$2750.00` due to a lost decimal point) enters the system:
1. **Invoice Specialist** runs the mathematical check `subtotal + tax == grand_total` and flags `Mathematical Mismatch`.
2. **LangGraph Router** detects `is_valid == False` and routes execution to `ErrorResolverAgent`.
3. **Error Resolver** checks decimal ratio and constraint equations, diagnoses the missing decimal point, reconciles Grand Total to `$275.00`, records an audit event, and marks `is_valid = True`.
4. **Workflow continues** to `PostprocessorAgent`, returning valid data and a complete audit trail without failing the execution.
