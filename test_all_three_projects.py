"""
End-to-End Test Suite for Universal Multi-Agent LangGraph Platform.
Tests the registry, adapters, graph compilation, and execution for all 3 projects.
"""
import sys
import os
import time
from pathlib import Path

PLATFORM_ROOT = Path(r"C:\Users\panka\.gemini\antigravity\scratch\universal_multiagent_platform")
if str(PLATFORM_ROOT) not in sys.path:
    sys.path.insert(0, str(PLATFORM_ROOT))

# Ensure shared venv site-packages is in sys.path
_SITE_PACKAGES = r"C:\Users\panka\.gemini\antigravity\scratch\ocr_multiagent_system\venv_ocr\Lib\site-packages"
if os.path.isdir(_SITE_PACKAGES) and _SITE_PACKAGES not in sys.path:
    sys.path.insert(1, _SITE_PACKAGES)

from engine.project_registry import ProjectRegistry

def run_tests():
    registry = ProjectRegistry()
    projects = registry.list_projects()
    print("=" * 75)
    print("UNIVERSAL MULTI-AGENT PLATFORM — END-TO-END VALIDATION SUITE")
    print("=" * 75)
    print(f"Registered Projects: {projects}")
    print("=" * 75)

    test_results = {}

    # -------------------------------------------------------------------------
    # TEST 1: Industrial Vision & Diagnostic RAG
    # -------------------------------------------------------------------------
    print("\n[TEST 1/3] Testing: industrial_vision_rag ...")
    ind_adapter = registry.get("industrial_vision_rag")
    avail, reason = ind_adapter.is_available()
    print(f"  Availability: {avail} (Reason: {reason})")
    assert avail, f"Industrial adapter not available: {reason}"

    graph_def = ind_adapter.get_graph_definition()
    print(f"  Graph Nodes ({len(graph_def['nodes'])}): {[n['name'] for n in graph_def['nodes']]}")
    print(f"  Graph Edges ({len(graph_def['edges'])}): {len(graph_def['edges'])} routed pathways")

    print("  Executing pipeline with target defect: 'crack' ...")
    t0 = time.time()
    res1 = ind_adapter.execute({"defect_type": "crack", "frame_index": 105})
    elapsed1 = time.time() - t0

    print(f"  Status:         {res1.status}")
    print(f"  Elapsed:        {elapsed1:.2f}s ({res1.execution_time_ms:.1f}ms reported)")
    print(f"  Agents Invoked: {res1.agents_invoked}")
    alert = res1.summary.get('alert') or {}
    wo = res1.summary.get('work_order') or {}
    print(f"  Defect Type:    {alert.get('defect_type')}")
    print(f"  Severity:       {alert.get('severity_score')} / 10.0 [{alert.get('severity_level')}]")
    print(f"  Work Order:     {res1.summary.get('work_order_id') or wo.get('work_order_id')}")
    print(f"  Has Raw B64:    {bool(res1.visualizations.get('raw_frame'))}")
    print(f"  Has Mask B64:   {bool(res1.visualizations.get('mask'))}")
    print(f"  Execution Logs: {len(res1.execution_log)} entries recorded")

    assert res1.status in ["SUCCESS", "COMPLETED"], f"Execution failed: {res1.status}"
    assert res1.visualizations.get('raw_frame'), "Missing raw_frame base64"
    assert res1.visualizations.get('mask'), "Missing mask base64"
    test_results["industrial_vision_rag"] = "PASSED"
    print("  >>> [TEST 1 PASSED]: Industrial Vision RAG fully functional! <<<")

    # -------------------------------------------------------------------------
    # TEST 2: Multi-Agent Face Detection
    # -------------------------------------------------------------------------
    print("\n[TEST 2/3] Testing: face_detection ...")
    fd_adapter = registry.get("face_detection")
    avail, reason = fd_adapter.is_available()
    print(f"  Availability: {avail} (Reason: {reason})")
    assert avail, f"Face Detection adapter not available: {reason}"

    graph_def2 = fd_adapter.get_graph_definition()
    print(f"  Graph Nodes ({len(graph_def2['nodes'])}): {[n['name'] for n in graph_def2['nodes']]}")
    print(f"  Graph Edges ({len(graph_def2['edges'])}): {len(graph_def2['edges'])} routed pathways")

    print("  Executing pipeline with synthetic image & 'blur' degradation ...")
    t0 = time.time()
    res2 = fd_adapter.execute({
        "input_mode": "Synthetic Test Image",
        "degradation_type": "blur",
        "degradation_severity": 0.5,
        "score_threshold": 0.5,
    })
    elapsed2 = time.time() - t0

    print(f"  Status:         {res2.status}")
    print(f"  Elapsed:        {elapsed2:.2f}s ({res2.execution_time_ms:.1f}ms reported)")
    print(f"  Agents Invoked: {res2.agents_invoked}")
    print(f"  Detection Count:{res2.summary.get('detection_count')}")
    print(f"  Quality Status: {res2.summary.get('quality_report', {}).get('status')}")
    print(f"  Audit Verdict:  {res2.summary.get('audit_report', {}).get('verdict')}")
    print(f"  Healed/Enhanced:{len(res2.errors_healed)} enhancement operations")
    print(f"  Has Vis B64:    {bool(res2.visualizations.get('output_image'))}")

    assert res2.status in ["SUCCESS", "PARTIAL_RECOVERY"], f"Execution failed: {res2.status}"
    assert res2.visualizations.get('output_image'), "Missing output_image base64"
    test_results["face_detection"] = "PASSED"
    print("  >>> [TEST 2 PASSED]: Face Detection fully functional! <<<")

    # -------------------------------------------------------------------------
    # TEST 3: OCR Multi-Agent System
    # -------------------------------------------------------------------------
    print("\n[TEST 3/3] Testing: ocr_system ...")
    ocr_adapter = registry.get("ocr_system")
    avail, reason = ocr_adapter.is_available()
    print(f"  Availability: {avail} (Reason: {reason})")
    assert avail, f"OCR adapter not available: {reason}"

    graph_def3 = ocr_adapter.get_graph_definition()
    print(f"  Graph Nodes ({len(graph_def3['nodes'])}): {[n['name'] for n in graph_def3['nodes']]}")
    print(f"  Graph Edges ({len(graph_def3['edges'])}): {len(graph_def3['edges'])} routed pathways")

    print("  Executing pipeline with sample invoice: 'invoice_clean.png' ...")
    t0 = time.time()
    res3 = ocr_adapter.execute({
        "input_mode": "Sample Data Files",
        "sample_file": "invoice_clean.png",
        "task_type": "auto",
        "max_retries": 2,
    })
    elapsed3 = time.time() - t0

    print(f"  Status:         {res3.status}")
    print(f"  Elapsed:        {elapsed3:.2f}s ({res3.execution_time_ms:.1f}ms reported)")
    print(f"  Agents Invoked: {res3.agents_invoked}")
    print(f"  Classified Type:{res3.summary.get('classified_type')}")
    print(f"  OCR Confidence: {res3.summary.get('ocr_confidence')}")
    print(f"  Routing Reason: {res3.summary.get('routing_reason')}")
    print(f"  Execution Logs: {len(res3.execution_log)} entries recorded")

    assert res3.status.lower() in ["completed", "success", "partial_recovery"], f"Execution failed: {res3.status}"
    test_results["ocr_system"] = "PASSED"
    print("  >>> [TEST 3 PASSED]: OCR Multi-Agent System fully functional! <<<")

    print("\n" + "=" * 75)
    print("FINAL SUMMARY: ALL 3 MULTI-AGENT PROJECTS PASSED ALL CHECKS!")
    for proj, outcome in test_results.items():
        print(f"  * {proj.ljust(25)}: {outcome}")
    print("=" * 75)

if __name__ == "__main__":
    run_tests()
