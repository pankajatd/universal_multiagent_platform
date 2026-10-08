"""
Unified Document Loader:
Handles ingestion and normalization of multiple file formats:
- Images: PNG, JPG, JPEG, TIFF, BMP, WEBP
- PDF Documents: Scanned and digital PDFs (renders high-res pages & extracts text)
- Text Files: TXT transcripts & OCR text dumps (renders visual canvas & preserves text)
- CSV Tables: Tabular accounting records & traffic logs (formats tables & renders canvas)
"""
import os
import csv
import cv2
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, Tuple, Optional, List
import logging

logger = logging.getLogger("DocumentLoader")

class DocumentLoader:
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or os.path.join(os.getcwd(), "ocr_output", "loaded_media")
        os.makedirs(self.cache_dir, exist_ok=True)

    def load_file(self, file_path: str, page_number: int = 0) -> Dict[str, Any]:
        """
        Loads and standardizes input file into:
        - `rendered_image_path`: Path to an image file usable by OCR/computer vision
        - `direct_text`: Embedded text (if available from digital PDF, TXT, or CSV)
        - `file_type`: 'image', 'pdf', 'txt', 'csv'
        - `metadata`: format-specific metadata (page count, row count, etc.)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        base_name = os.path.basename(file_path)
        name, ext = os.path.splitext(base_name)
        ext_lower = ext.lower()

        # ---------------------------------------------------------
        # 1. Image Files
        # ---------------------------------------------------------
        if ext_lower in [".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"]:
            return {
                "file_path": os.path.abspath(file_path),
                "rendered_image_path": os.path.abspath(file_path),
                "direct_text": "",
                "file_type": "image",
                "metadata": {"format": ext_lower[1:].upper()}
            }

        # ---------------------------------------------------------
        # 2. PDF Documents
        # ---------------------------------------------------------
        elif ext_lower == ".pdf":
            return self._load_pdf(file_path, name, page_number)

        # ---------------------------------------------------------
        # 3. Plain Text Files (.txt)
        # ---------------------------------------------------------
        elif ext_lower == ".txt":
            return self._load_txt(file_path, name)

        # ---------------------------------------------------------
        # 4. Tabular CSV Files (.csv)
        # ---------------------------------------------------------
        elif ext_lower == ".csv":
            return self._load_csv(file_path, name)

        else:
            raise ValueError(f"Unsupported file format: {ext}. Supported: PNG, JPG, TIFF, PDF, TXT, CSV")

    def _load_pdf(self, file_path: str, name: str, page_number: int) -> Dict[str, Any]:
        """Renders specified PDF page as a high-resolution 200 DPI image and extracts digital text."""
        import pymupdf

        doc = pymupdf.open(file_path)
        total_pages = len(doc)
        page_idx = max(0, min(page_number, total_pages - 1))
        page = doc[page_idx]

        # Extract embedded text if available
        digital_text = page.get_text().strip()

        # Render page to high-res image (200 DPI)
        pix = page.get_pixmap(dpi=200)
        out_image_path = os.path.join(self.cache_dir, f"{name}_page_{page_idx + 1}.png")
        pix.save(out_image_path)
        doc.close()

        return {
            "file_path": os.path.abspath(file_path),
            "rendered_image_path": os.path.abspath(out_image_path),
            "direct_text": digital_text,
            "file_type": "pdf",
            "metadata": {
                "total_pages": total_pages,
                "current_page": page_idx + 1,
                "has_digital_text": len(digital_text) > 20
            }
        }

    def _load_txt(self, file_path: str, name: str) -> Dict[str, Any]:
        """Reads text file and renders it onto a crisp document canvas for visual processing."""
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            raw_text = f.read()

        lines = raw_text.splitlines()
        line_count = len(lines)

        # Render onto image canvas
        width = 750
        line_height = 24
        margin_top = 40
        margin_left = 40
        height = max(800, margin_top * 2 + (line_count + 2) * line_height)

        img = Image.new("RGB", (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        # Header title
        draw.text((margin_left, 15), f"FILE: {name}.txt (Direct Text Ingestion)", fill=(100, 100, 100))
        draw.line([(margin_left, 35), (width - margin_left, 35)], fill=(200, 200, 200), width=1)

        y = margin_top
        for line in lines:
            draw.text((margin_left, y), line, fill=(20, 20, 20))
            y += line_height

        out_image_path = os.path.join(self.cache_dir, f"{name}_rendered.png")
        img.save(out_image_path)

        return {
            "file_path": os.path.abspath(file_path),
            "rendered_image_path": os.path.abspath(out_image_path),
            "direct_text": raw_text,
            "file_type": "txt",
            "metadata": {
                "line_count": line_count,
                "character_count": len(raw_text)
            }
        }

    def _load_csv(self, file_path: str, name: str) -> Dict[str, Any]:
        """Reads CSV data, converts to tabular text representation, and renders a table canvas."""
        df = pd.read_csv(file_path)
        
        # Build text representation
        text_repr = df.to_string(index=False)
        
        # Check if CSV has invoice columns
        cols_lower = [c.lower() for c in df.columns]
        has_items = any(c in cols_lower for c in ["item", "description", "product"])
        has_totals = any(c in cols_lower for c in ["total", "price", "amount", "unit price"])

        # Render visually onto a clean table image
        width = 800
        row_height = 28
        height = max(500, 100 + (len(df) + 3) * row_height)
        img = Image.new("RGB", (width, height), color=(252, 252, 254))
        draw = ImageDraw.Draw(img)

        # Banner
        draw.rectangle([0, 0, width, 50], fill=(30, 58, 138))
        draw.text((30, 15), f"TABULAR DATASET: {name}.csv", fill=(255, 255, 255))

        # Render column headers
        col_widths = max(width // max(len(df.columns), 1), 120)
        x = 30
        y = 65
        for col in df.columns:
            draw.text((x, y), str(col).upper(), fill=(15, 23, 42))
            x += col_widths
        
        draw.line([(30, 95), (width - 30, 95)], fill=(148, 163, 184), width=2)

        # Render rows
        y = 105
        for _, row in df.iterrows():
            x = 30
            for val in row:
                draw.text((x, y), str(val), fill=(51, 65, 85))
                x += col_widths
            y += row_height
            draw.line([(30, y - 4), (width - 30, y - 4)], fill=(226, 232, 240), width=1)

        out_image_path = os.path.join(self.cache_dir, f"{name}_table.png")
        img.save(out_image_path)

        return {
            "file_path": os.path.abspath(file_path),
            "rendered_image_path": os.path.abspath(out_image_path),
            "direct_text": text_repr,
            "file_type": "csv",
            "metadata": {
                "rows": len(df),
                "columns": list(df.columns),
                "has_invoice_structure": has_items and has_totals
            }
        }
