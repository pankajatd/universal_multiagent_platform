import os
import json
import traceback
from typing import Dict, Any, List
from src.state import AgenticState
from src.config import MIN_RAG_RELEVANCE, OPENAI_API_KEY, OPENAI_MODEL_NAME
from src.tools.vector_store import VectorStore

class MaintenanceRAGAgent:
    """RAG & Maintenance Agent: Formulates technical search queries, queries SOP manuals, and generates work orders."""

    def __init__(self, vector_store: VectorStore):
        self.name = "MaintenanceRAGAgent"
        self.vector_store = vector_store
        self.llm = None
        self._init_llm()

    def _init_llm(self):
        """Initializes LangChain ChatOpenAI if API key is present."""
        if OPENAI_API_KEY:
            try:
                from langchain_openai import ChatOpenAI
                self.llm = ChatOpenAI(
                    model=OPENAI_MODEL_NAME, 
                    api_key=OPENAI_API_KEY,
                    temperature=0.1
                )
            except Exception as e:
                print(f"[{self.name}] Notice: ChatOpenAI initialization skipped ({e}). Using local synthesis.")

    def formulate_queries(self, alert: Dict[str, Any]) -> List[str]:
        """Formulates targeted technical search queries based on defect diagnosis."""
        defect = alert.get("defect_type", "normal")
        severity = alert.get("severity_level", "LOW")
        
        query_map = {
            "crack": [
                "structural crack repair GTAW TIG welding procedure PWHT",
                "crack arrestor hole drilling dye penetrant inspection"
            ],
            "corrosion": [
                "surface oxidation chemical pickling passivation ASTM A380",
                "abrasive blasting pit depth remediation MIL-PRF"
            ],
            "dimensional": [
                "dimensional tolerance CNC remachining CMM coordinate metrology",
                "carbide face mill skim pass deburring ISO 2768"
            ],
            "scratch": [
                "surface micro-fissure polishing abrasive orbital blending Ra",
                "diamond paste felt polishing profilometry"
            ]
        }
        return query_map.get(defect, ["general plant safety maintenance procedure"])

    def synthesize_work_order(
        self, 
        alert: Dict[str, Any], 
        docs: List[Dict[str, Any]], 
        queries: List[str]
    ) -> Dict[str, Any]:
        """Synthesizes structured ISO/OSHA compliant Work Order using LLM or local industrial engine."""
        frame_idx = alert.get("frame_index", 0)
        wo_id = f"WO-M{frame_idx:04d}-{alert.get('defect_type', 'DEF').upper()}"
        defect = alert.get("defect_type", "unspecified")
        score = alert.get("severity_score", 0.0)
        level = alert.get("severity_level", "LOW")

        context_text = "\n\n".join([f"[{d.get('source', 'MANUAL')}]: {d.get('content', '')}" for d in docs])

        # If LangChain LLM is active, use it for prompt synthesis
        if self.llm:
            try:
                prompt = (
                    f"You are a Senior Industrial Plant Reliability Engineer.\n"
                    f"Synthesize an official Maintenance Work Order for an automated inspection alert.\n\n"
                    f"Alert Details:\n"
                    f"- Defect: {defect}\n"
                    f"- Severity Score: {score}/10.0 ({level})\n\n"
                    f"Relevant Standard Operating Procedures (SOP):\n"
                    f"{context_text}\n\n"
                    f"Return ONLY valid JSON matching this schema:\n"
                    f"{{\n"
                    f'  "work_order_id": "{wo_id}",\n'
                    f'  "defect_type": "{defect}",\n'
                    f'  "severity_level": "{level}",\n'
                    f'  "safety_directives": ["bullet 1", "bullet 2"],\n'
                    f'  "repair_procedure": ["step 1", "step 2", "step 3"],\n'
                    f'  "source_manuals": ["manual names"],\n'
                    f'  "technician_signoff_required": true\n'
                    f"}}"
                )
                response = self.llm.invoke(prompt)
                content = response.content if hasattr(response, "content") else str(response)
                
                # Parse JSON safely
                json_str = content
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            except Exception as e:
                print(f"[{self.name}] LLM invocation failed ({e}), falling back to deterministic local synthesis.")

        # High-Fidelity Local Synthesis Engine
        safety_directives = [
            "Mandatory OSHA Lockout/Tagout (LOTO) per 29 CFR 1910.147 prior to approaching fixture.",
            "Verify zero-energy state on hydraulic and electrical lines.",
            "Personal Protective Equipment (PPE): Full face shield, chemical/welding gauntlets, steel-toe boots."
        ]
        
        procedure = []
        sources = list(set([d.get("source", "SOP-000-GENERAL.md") for d in docs]))

        if defect == "crack":
            procedure = [
                "Drill crack arrestor holes (Ø 3.2mm) at both extremities to halt stress propagation.",
                "Pneumatically grind 60-degree V-groove along fissure.",
                "Pre-heat substrate to 150°C using induction blanket.",
                "Execute GTAW / TIG root weld with ER308L filler wire (current 90-110A DCEN).",
                "Perform post-weld heat treatment at 350°C for 45 minutes; verify with dye penetrant."
            ]
        elif defect == "corrosion":
            procedure = [
                "Abrade oxidized crust with aluminum oxide blast (120 mesh at 60 psi).",
                "Apply chemical pickling gel (ASTM A380 compliant) for 25 minutes dwell time.",
                "Rinse with demineralized water until effluent reaches neutral pH (6.5 - 7.5).",
                "Apply citric acid passivation bath (ASTM A967 Type 4) at 55°C for 20 min to restore chrome layer.",
                "Apply MIL-PRF-16173 Grade 2 corrosion preventive coat."
            ]
        elif defect == "dimensional":
            procedure = [
                "Mount component onto Coordinate Measuring Machine (CMM) table; probe datums A, B, C.",
                "Load part into hydraulic zero-point clamping fixture; torque to 45 Nm.",
                "Perform CNC skim pass remachining (carbide face mill, Vc=220 m/min, ap=0.25mm).",
                "Deburr peripheral edges with ceramic rotary brush at 3000 RPM.",
                "Perform final CMM coordinate verification per ISO 2768-mK."
            ]
        elif defect == "scratch":
            procedure = [
                "Perform profilometry scan to establish baseline roughness.",
                "Mask adjacent reference zones with polyimide tape.",
                "Orbital feathering with silicon carbide disc (400 grit).",
                "Step-polish using 800-grit and 1200-grit diamond paste with felt bob.",
                "Verify final surface roughness Ra <= 0.4 µm."
            ]
        else:
            procedure = ["Inspect component visually. Confirm baseline clearance."]

        return {
            "work_order_id": wo_id,
            "defect_type": defect,
            "severity_score": score,
            "severity_level": level,
            "safety_directives": safety_directives,
            "repair_procedure": procedure,
            "source_manuals": sources,
            "technician_signoff_required": (level == "CRITICAL")
        }

    def __call__(self, state: AgenticState) -> AgenticState:
        new_state = dict(state)
        new_state.setdefault("execution_log", [])
        new_state.setdefault("errors", [])
        new_state["execution_log"].append(f"[{self.name}] Initiating SOP manual retrieval and work order formulation...")

        alert = state.get("alert", {})
        queries = state.get("search_queries") or self.formulate_queries(alert)
        new_state["search_queries"] = queries

        try:
            # 1. Vector Search
            retrieved_docs = []
            max_score = 0.0
            for q in queries:
                matches = self.vector_store.search(q, top_k=2)
                for m in matches:
                    retrieved_docs.append(m)
                    if m.get("score", 0.0) > max_score:
                        max_score = m.get("score", 0.0)

            new_state["retrieved_docs"] = retrieved_docs
            new_state["retrieval_relevance_score"] = round(max_score, 4)

            # 2. Check Retrieval Quality
            if max_score < MIN_RAG_RELEVANCE:
                new_state["execution_log"].append(
                    f"[{self.name}] WARNING: Retrieval relevance score ({max_score}) below threshold ({MIN_RAG_RELEVANCE})"
                )
                new_state["errors"].append({
                    "component": "maintenance_rag_agent",
                    "error_type": "rag_low_relevance",
                    "message": f"SOP retrieval relevance score {max_score} < {MIN_RAG_RELEVANCE}. Queries may lack domain specificity.",
                    "resolved": False
                })
                new_state["status"] = "NEEDS_HEALING"
                return new_state

            # 3. Work Order Synthesis
            work_order = self.synthesize_work_order(alert, retrieved_docs, queries)
            new_state["work_order"] = work_order
            new_state["execution_log"].append(
                f"[{self.name}] Synthesized Work Order {work_order['work_order_id']} from {len(retrieved_docs)} SOP citations (Relevance: {max_score})."
            )

        except Exception as e:
            tb = traceback.format_exc()
            new_state["execution_log"].append(f"[{self.name}] ERROR: Exception in RAG pipeline: {str(e)}")
            new_state["errors"].append({
                "component": "maintenance_rag_agent",
                "error_type": "runtime_exception",
                "message": f"RAG Agent execution failure: {str(e)}",
                "traceback": tb,
                "resolved": False
            })
            new_state["status"] = "NEEDS_HEALING"

        return new_state
