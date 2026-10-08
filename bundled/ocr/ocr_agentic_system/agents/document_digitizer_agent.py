"""
Document Digitizer Agent:
Specialist agent for digitizing paper documents, legal contracts, research notes,
and books for digital archiving, full-text searching, and semantic indexing.
"""
import re
from typing import List, Dict, Any, Tuple
from collections import Counter
import logging

logger = logging.getLogger("DocumentDigitizerAgent")

class DocumentDigitizerAgent:
    def __init__(self):
        # Stopwords for simple keyword indexing
        self.stopwords = {
            "the", "a", "an", "and", "or", "in", "on", "at", "to", "for",
            "of", "with", "by", "is", "are", "was", "were", "this", "that"
        }

    def process_document(self, raw_boxes: List[Dict[str, Any]], full_text: str) -> Tuple[Dict[str, Any], List[str]]:
        """
        Parses multi-line OCR results into structured document sections,
        calculates reading order, extracts search index keywords, and validates quality.
        Returns:
            (extracted_data_dict, validation_errors_list)
        """
        validation_errors: List[str] = []

        if not raw_boxes and not full_text.strip():
            validation_errors.append("Empty OCR output: No readable text detected on document page.")
            return {"raw_text": "", "paragraphs": [], "search_keywords": []}, validation_errors

        # 1. Sort boxes top-to-bottom, left-to-right (Reading Order)
        sorted_boxes = sorted(
            raw_boxes, 
            key=lambda b: (
                b.get("box", [[0, 0]])[0][1] // 25,  # group by ~25px vertical line buckets
                b.get("box", [[0, 0]])[0][0]        # sort left to right within line
            )
        ) if raw_boxes else []

        lines = [b.get("text", "").strip() for b in sorted_boxes if b.get("text", "").strip()]
        if not lines and full_text.strip():
            lines = [l.strip() for l in full_text.splitlines() if l.strip()]

        # 2. Layout Structure Extraction (Title, Headings, Paragraphs)
        title = lines[0] if lines else "Untitled Document"
        paragraphs = []
        current_para = []

        for line in lines[1:] if len(lines) > 1 else []:
            # Short lines in all caps or starting with numbers often represent headings
            if len(line) < 60 and (line.isupper() or re.match(r'^\d+(\.\d+)*\s+', line)):
                if current_para:
                    paragraphs.append(" ".join(current_para))
                    current_para = []
                paragraphs.append(f"### {line}")
            else:
                current_para.append(line)
        if current_para:
            paragraphs.append(" ".join(current_para))

        # 3. Extract Full-Text Search Keywords (Indexing for Archival Search)
        all_words = re.findall(r'[a-zA-Z]{3,}', full_text.lower())
        filtered_words = [w for w in all_words if w not in self.stopwords]
        word_freq = Counter(filtered_words)
        top_keywords = [{"keyword": kw, "count": count} for kw, count in word_freq.most_common(12)]

        # 4. Compute Metadata
        total_word_count = len(re.findall(r'\b\w+\b', full_text))
        reading_time_mins = round(total_word_count / 200, 2)  # Avg 200 wpm reading speed

        extracted_data = {
            "document_type": "archive_document",
            "title": title,
            "paragraphs": paragraphs,
            "raw_text": full_text,
            "reading_order_lines": lines,
            "total_word_count": total_word_count,
            "estimated_reading_time_minutes": reading_time_mins,
            "search_index": {
                "top_keywords": top_keywords,
                "token_count": len(all_words)
            },
            "markdown_representation": self._generate_markdown(title, paragraphs, top_keywords)
        }

        # 5. Validation Check
        # Check minimum word count
        if total_word_count < 8:
            validation_errors.append(f"Document contains insufficient readable text ({total_word_count} words). Possible low contrast or severe blur.")

        # Check noise / gibberish ratio (e.g. random unprintable or weird punctuation chars)
        symbols_count = len(re.findall(r'[^a-zA-Z0-9\s.,?!:;\'"()-]', full_text))
        if total_word_count > 0:
            symbol_ratio = symbols_count / max(len(full_text), 1)
            if symbol_ratio > 0.22:
                validation_errors.append(f"High OCR noise/gibberish ratio ({symbol_ratio:.1%}). Image thresholding or noise cleanup required.")

        return extracted_data, validation_errors

    def _generate_markdown(self, title: str, paragraphs: List[str], keywords: List[Dict[str, Any]]) -> str:
        md = [f"# {title}\n"]
        for p in paragraphs:
            md.append(f"{p}\n")
        md.append("\n---\n**Archival Search Tags:** " + ", ".join([f"`{k['keyword']}`" for k in keywords[:6]]))
        return "\n".join(md)
