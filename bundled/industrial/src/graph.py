from typing import Dict, Any
from langgraph.graph import StateGraph, END
from src.state import AgenticState
from src.tools.vector_store import VectorStore
from src.agents import (
    OrchestratorAgent,
    VisionAgent,
    DiagnosticAgent,
    MaintenanceRAGAgent,
    SelfHealingAgent,
    QualityGateAgent
)

def build_multiagent_graph(vector_store: VectorStore = None) -> StateGraph:
    """
    Constructs the LangGraph Multi-Agent Architecture with dynamic Supervisor Orchestration
    and Autonomous Self-Healing Error Recovery loops.
    """
    if vector_store is None:
        vector_store = VectorStore()

    # 1. Instantiate Agents
    orchestrator = OrchestratorAgent()
    vision_agent = VisionAgent()
    diagnostic_agent = DiagnosticAgent()
    rag_agent = MaintenanceRAGAgent(vector_store)
    self_healing_agent = SelfHealingAgent(vector_store)
    quality_gate_agent = QualityGateAgent()

    # 2. Initialize StateGraph
    workflow = StateGraph(AgenticState)

    # 3. Add Agent Nodes
    workflow.add_node("orchestrator", orchestrator)
    workflow.add_node("vision_agent", vision_agent)
    workflow.add_node("diagnostic_agent", diagnostic_agent)
    workflow.add_node("maintenance_rag_agent", rag_agent)
    workflow.add_node("self_healing_agent", self_healing_agent)
    workflow.add_node("quality_gate_agent", quality_gate_agent)

    # 4. Entry Point: Always starts at the Master Orchestrator
    workflow.set_entry_point("orchestrator")

    # 5. Conditional Dispatch from Orchestrator
    def route_from_orchestrator(state: AgenticState) -> str:
        return state.get("next_agent", "END")

    workflow.add_conditional_edges(
        "orchestrator",
        route_from_orchestrator,
        {
            "vision_agent": "vision_agent",
            "diagnostic_agent": "diagnostic_agent",
            "maintenance_rag_agent": "maintenance_rag_agent",
            "quality_gate_agent": "quality_gate_agent",
            "self_healing_agent": "self_healing_agent",
            "END": END
        }
    )

    # 6. Worker Loops: All specialized agents report back to Orchestrator for evaluation
    workflow.add_edge("vision_agent", "orchestrator")
    workflow.add_edge("diagnostic_agent", "orchestrator")
    workflow.add_edge("maintenance_rag_agent", "orchestrator")
    workflow.add_edge("quality_gate_agent", "orchestrator")
    workflow.add_edge("self_healing_agent", "orchestrator")

    # 7. Compile Graph
    compiled_app = workflow.compile()
    return compiled_app
