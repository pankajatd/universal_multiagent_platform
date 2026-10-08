import os
import re
import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.config import MANUALS_DIR

SOP_TEMPLATES = {
    "SOP-001-CRACK.md": """# SOP-001: Structural Crack Remediation and Metallurgical Repair Procedure

## 1. Safety Directives & Regulatory Compliance
- Mandatory OSHA Lockout/Tagout (LOTO) per 29 CFR 1910.147 prior to fixture approach.
- Personal Protective Equipment (PPE): Level 3 welding shield (Shade 10-12), Kevlar flame-retardant gauntlets, respirator with particulate P100 filter.
- Structural integrity warning: Any crack exceeding 15mm propagation requires immediate supervisor sign-off and pressure isolation.

## 2. Diagnostics & Defect Verification
- Inspect crack bifurcation with liquid dye penetrant inspection (PT) or eddy-current testing (ET).
- Confirm defect depth profile using ultrasonic thickness gauge (UT).

## 3. Repair Protocol
1. Drill crack arrestor holes (Ø 3.2mm) at both crack extremities to halt stress concentration.
2. Machine a 60-degree V-groove along crack fissure using pneumatic carbide die grinder.
3. Pre-heat substrate to 150°C using induction heating blanket.
4. Execute Gas Tungsten Arc Welding (GTAW / TIG) root pass with ER308L filler wire, current 90-110A DCEN.
5. Apply post-weld heat treatment (PWHT) at 350°C for 45 minutes to relieve residual stress.
6. Grind weld crown flush with base metal contour and repeat dye penetrant test.
""",
    "SOP-002-CORROSION.md": """# SOP-002: Surface Oxidation & Corrosion Remediation Procedure

## 1. Safety Directives & PPE Compliance
- Hazard notice: Acidic passivation chemicals present severe chemical burn hazards.
- PPE Required: Nitrile heavy-duty chemical apron, face shield, neoprene chemical gloves (EN 374), acid gas dual cartridge respirator.
- Emergency eye-wash station verification required before handling chemical baths.

## 2. Substrate Assessment
- Measure pit depth with optical micrometer. Pitting deeper than 0.8mm requires engineering concession review.
- Confirm alloy compatibility with nitric-hydrofluoric pickling agents.

## 3. Remediation & Passivation Steps
1. Mechanically abrade oxidized crust using aluminum oxide abrasive blast (grit size 120 mesh) at 60 psi.
2. Degrease surface with isopropyl alcohol (IPA) or aqueous alkaline cleaner (pH 11.5).
3. Apply chemical pickling gel (ASTM A380 compliant) for 25 minutes dwell time.
4. Flush thoroughly with demineralized water until effluent pH measures neutral (6.5 - 7.5).
5. Apply citric acid passivation solution (ASTM A967 Type 4) at 55°C for 20 minutes to restore passive chromium oxide layer.
6. Apply MIL-PRF-16173 Grade 2 corrosion preventive coating.
""",
    "SOP-003-DIMENSIONAL.md": """# SOP-003: Dimensional Tolerance Rectification & CNC Remachining

## 1. Safety Directives
- Ensure spindle power interlock and safety light curtains are active.
- PPE: ANSI Z87.1 approved safety glasses with side shields, steel-toe metatarsal boots, hearing protection (NRR 28dB).
- Never reach into machine envelope while 5-axis servo drives are energized.

## 2. Metrology & Coordinate Verification
- Mount component onto Coordinate Measuring Machine (CMM) table.
- Probe datum surfaces A, B, and C to verify runout, perpendicularity, and profile deviation against CAD model tolerances (ISO 2768-mK).

## 3. CNC Remachining & Deburring Procedure
1. Load component into hydraulic zero-point clamping fixture; torque to 45 Nm.
2. Touch-off tool setter using carbide face mill (Ø 50mm, 4 flutes).
3. Execute skim pass remachining (cutting speed Vc=220 m/min, feed fz=0.08 mm/tooth, depth ap=0.25mm) using high-pressure flood coolant.
4. Deburr peripheral edges with ceramic abrasive brush at 3000 RPM.
5. Re-measure critical dimensions on CMM and log inspection certificate into ERP database.
""",
    "SOP-004-SCRATCH.md": """# SOP-004: Surface Micro-Fissure & Scratch Blending Protocol

## 1. Safety Guidelines
- Verify dust extraction suction is functioning on rotary hand tools.
- PPE: Safety glasses, nitrile comfort gloves, N95 dust mask.

## 2. Surface Profilometry
- Measure surface roughness Ra with contact stylus profilometer. Baseline requirement: Ra < 0.8 µm.

## 3. Blending & Polishing Procedure
1. Mask adjacent critical reference zones with polyimide high-adhesion tape.
2. Perform localized orbital feathering using silicon carbide abrasive disc (grit 400), applying light oscillating pressure.
3. Step polish through 800-grit and 1200-grit diamond paste with felt polishing bob.
4. Clean polished zone with solvent wipe and verify absence of residual step edges.
5. Measure final surface roughness to confirm Ra <= 0.4 µm.
""",
    "SOP-000-GENERAL.md": """# SOP-000: General Industrial Plant Safety & Maintenance Protocol

## 1. Universal Safety Rules
- All plant maintenance operations must comply with ISO 45001 occupational safety standards.
- Every intervention requires an active Work Permit issued by the Shift Operations Lead.
- Zero-energy state verification is mandatory before maintenance intervention.

## 2. Tool & Equipment Maintenance
- Torque wrenches, micrometers, and measuring gauges must carry active calibration stickers (< 12 months).
- Defective electrical tools must be immediately tagged out of service.
"""
}

class VectorStore:
    """TF-IDF Semantic Vector Store for Industrial SOP Manuals."""

    def __init__(self, manuals_dir: str = MANUALS_DIR):
        self.manuals_dir = manuals_dir
        self.documents: List[Dict[str, Any]] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.doc_vectors = None
        self._initialize_manuals()

    def _initialize_manuals(self):
        """Ensures SOP manuals exist on disk and ingests them."""
        os.makedirs(self.manuals_dir, exist_ok=True)
        for fname, content in SOP_TEMPLATES.items():
            filepath = os.path.join(self.manuals_dir, fname)
            if not os.path.exists(filepath):
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)

        self._build_index()

    def _build_index(self):
        """Chunks documents and constructs the TF-IDF search index."""
        self.documents = []
        texts = []

        for fname in os.listdir(self.manuals_dir):
            if fname.endswith(".md"):
                fpath = os.path.join(self.manuals_dir, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()

                # Split by markdown headers
                sections = re.split(r'\n(?=##?\s)', content)
                for i, sec in enumerate(sections):
                    clean_text = sec.strip()
                    if len(clean_text) > 30:
                        doc_entry = {
                            "id": f"{fname}#sec-{i}",
                            "source": fname,
                            "content": clean_text
                        }
                        self.documents.append(doc_entry)
                        texts.append(clean_text)

        if texts:
            self.vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
            self.doc_vectors = self.vectorizer.fit_transform(texts)

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Searches vector index with cosine similarity ranking."""
        if not self.documents or self.vectorizer is None or self.doc_vectors is None:
            return []

        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.doc_vectors).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(scores[idx])
            doc = self.documents[idx].copy()
            doc["score"] = round(score, 4)
            results.append(doc)

        return results

    def fallback_broad_search(self, defect_type: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Broad retrieval fallback using canonical technical keywords when query expansion fails."""
        keyword_map = {
            "crack": "crack welding GTAW TIG repair PWHT arrestor stress fracture",
            "corrosion": "corrosion oxidation passivation acid pickling abrasive blast rust",
            "dimensional": "dimensional CNC remachining CMM tolerance milling face mill",
            "scratch": "scratch polishing abrasive surface roughness Ra micro-fissure",
            "normal": "plant safety general maintenance inspection"
        }
        broad_query = keyword_map.get(defect_type, "safety maintenance protocol repair")
        return self.search(broad_query, top_k=top_k)
