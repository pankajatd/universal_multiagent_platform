"""
CLI Interface for LangGraph Multi-Agent OCR System.
Usage:
    python -m ocr_agentic_system.cli --image sample_data/invoice_clean.png
    python -m ocr_agentic_system.cli --demo
"""
import argparse
import json
import os
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.json import JSON

from .graph.workflow import OCRMultiAgentGraph
from .utils.synthetic_generator import create_synthetic_datasets

console = Console()

def run_single(file_path: str, task_type: str = "auto"):
    if not os.path.exists(file_path):
        console.print(f"[bold red]Error:[/bold red] File not found: {file_path}")
        sys.exit(1)

    ext = os.path.splitext(file_path)[1].lower()
    console.print(Panel(f"[bold cyan]LangGraph Multi-Agent OCR Pipeline[/bold cyan]\nProcessing: [green]{file_path}[/green] ({ext.upper()}) | Mode: [yellow]{task_type}[/yellow]", expand=False))
    
    with console.status("[bold blue]Executing Multi-Agent Graph...[/bold blue]", spinner="dots"):
        graph = OCRMultiAgentGraph()
        result = graph.run(file_path=file_path, task_type=task_type)

    final_out = result.get("final_output", {})
    doc_type = final_out.get("document_type", "unknown")
    cls_conf = final_out.get("classification_confidence", 0.0)
    ocr_conf = final_out.get("ocr_confidence_score", 0.0)
    status = final_out.get("workflow_status", "UNKNOWN")

    # Summary Table
    table = Table(title="Agentic Execution Summary", show_header=True, header_style="bold magenta")
    table.add_column("Property", style="dim", width=24)
    table.add_column("Value")
    
    table.add_row("Input File Format", f"[bold cyan]{final_out.get('file_type', ext[1:]).upper()}[/bold cyan]")
    table.add_row("Classified Domain", f"[bold yellow]{doc_type.upper()}[/bold yellow] (Confidence: {cls_conf:.2f})")
    table.add_row("Orchestrator Reason", final_out.get("routing_reason", "N/A"))
    table.add_row("OCR / Text Confidence", f"{ocr_conf:.2%}")
    table.add_row("Workflow Status", f"[bold green]{status}[/bold green]" if status == "SUCCESS" else f"[bold yellow]{status}[/bold yellow]")
    table.add_row("Error Resolver Invoked", "[bold green]YES (Healed)[/bold green]" if final_out.get("errors_resolved") else "NO (Zero Errors)")
    table.add_row("Preprocessing Steps", ", ".join(final_out.get("preprocessing_history", [])))
    
    console.print(table)

    # Error Resolution Details
    if final_out.get("error_history"):
        console.print("\n[bold yellow]Self-Correction & Error Resolution Audit Log:[/bold yellow]")
        for idx, rec in enumerate(final_out.get("error_history", []), 1):
            console.print(Panel(
                f"[red]Detected Error:[/red] {rec.get('message')}\n"
                f"[green]Resolution Applied:[/green] {rec.get('resolution_attempted')}\n"
                f"[cyan]Retry Attempt:[/cyan] #{rec.get('attempt')} | [bold green]Resolved Successfully[/bold green]",
                title=f"Error Resolver Event #{idx}",
                border_style="yellow"
            ))

    # Extracted Domain Data
    ext = final_out.get("extracted_data", {})
    console.print("\n[bold cyan]Structured Domain Extraction:[/bold cyan]")
    if doc_type == "license_plate":
        plate_tbl = Table(title="Smart Traffic ANPR", show_header=True)
        plate_tbl.add_column("Field")
        plate_tbl.add_column("Value", style="bold green")
        plate_tbl.add_row("Registration Plate", ext.get("plate_number", ""))
        plate_tbl.add_row("Jurisdiction Format", ext.get("matched_jurisdiction_format", ""))
        plate_tbl.add_row("Toll Gate ID", ext.get("traffic_metadata", {}).get("toll_gate_id", ""))
        plate_tbl.add_row("Compliance Check", ext.get("traffic_metadata", {}).get("watchlist_check", ""))
        console.print(plate_tbl)

    elif doc_type == "invoice":
        inv_tbl = Table(title="Automated Invoice / Accounting Entry", show_header=True)
        inv_tbl.add_column("Field")
        inv_tbl.add_column("Value", style="bold green")
        inv_tbl.add_row("Vendor Name", ext.get("vendor_name", ""))
        inv_tbl.add_row("Invoice Number", ext.get("invoice_number", ""))
        inv_tbl.add_row("Invoice Date", ext.get("invoice_date", ""))
        fin = ext.get("financial_summary", {})
        curr = ext.get("currency", "$")
        inv_tbl.add_row("Subtotal", f"{curr}{(fin.get('subtotal') or 0.0):.2f}")
        inv_tbl.add_row("Tax", f"{curr}{(fin.get('tax') or 0.0):.2f}")
        inv_tbl.add_row("Grand Total", f"[bold underline]{curr}{(fin.get('grand_total') or 0.0):.2f}[/bold underline]")
        console.print(inv_tbl)

    else: # document
        doc_tbl = Table(title="Digitized Paper Document & Search Archive", show_header=True)
        doc_tbl.add_column("Field")
        doc_tbl.add_column("Value", style="bold green")
        doc_tbl.add_row("Title", ext.get("title", ""))
        doc_tbl.add_row("Word Count", str(ext.get("total_word_count", 0)))
        doc_tbl.add_row("Reading Time", f"{ext.get('estimated_reading_time_minutes', 0)} mins")
        keywords = [k.get("keyword") for k in ext.get("search_index", {}).get("top_keywords", [])[:6]]
        doc_tbl.add_row("Top Search Keywords", ", ".join(keywords))
        console.print(doc_tbl)

def run_demo():
    console.print(Panel("[bold green]Generating Synthetic Test Datasets & Running Multi-Agent Suite...[/bold green]"))
    datasets = create_synthetic_datasets()
    for name, path in datasets.items():
        console.print(f"\n[bold magenta]>>> Processing Scenario: {name.upper()}[/bold magenta]")
        run_single(path)

def main():
    parser = argparse.ArgumentParser(description="LangGraph Multi-Agent OCR System")
    parser.add_argument("--file", "--image", dest="file", type=str, help="Path to input file (PDF, TXT, CSV, PNG, JPG, TIFF)")
    parser.add_argument("--type", type=str, default="auto", choices=["auto", "document", "license_plate", "invoice"], help="Target task type")
    parser.add_argument("--demo", action="store_true", help="Generate synthetic test datasets and run end-to-end demo across all formats")
    
    args = parser.parse_args()
    if args.demo:
        run_demo()
    elif args.file:
        run_single(args.file, args.type)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
