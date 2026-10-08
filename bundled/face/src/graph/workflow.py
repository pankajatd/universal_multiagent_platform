from typing import Dict, Any
from .state import AgentState

from src.detection.face_detector import FaceDetectorAgent
from src.quality.quality_inspector import QualityInspectorAgent
from src.enhancement.image_enhancer import ImageEnhancerAgent
from src.audit.test_auditor import TestAuditorAgent

# Native Fallback State Graph Engine
class FallbackStateGraph:
    def __init__(self, state_schema):
        self.nodes = {}
        self.edges = {}
        self.conditional_edges = {}
        self.entry_point = None

    def add_node(self, name, func):
        self.nodes[name] = func

    def add_edge(self, from_node, to_node):
        self.edges[from_node] = to_node

    def add_conditional_edges(self, from_node, condition_func, route_map):
        self.conditional_edges[from_node] = (condition_func, route_map)

    def set_entry_point(self, node):
        self.entry_point = node

    def compile(self):
        return CompiledGraph(self)

class CompiledGraph:
    def __init__(self, graph):
        self.graph = graph

    def invoke(self, state: dict) -> dict:
        current_node = self.graph.entry_point
        visited_count = 0
        while current_node != "END" and visited_count < 25:
            state = self.graph.nodes[current_node](state)
            visited_count += 1
            
            if current_node in self.graph.conditional_edges:
                cond_func, route_map = self.graph.conditional_edges[current_node]
                route_key = cond_func(state)
                current_node = route_map.get(route_key, "END")
            elif current_node in self.graph.edges:
                current_node = self.graph.edges[current_node]
            else:
                break
        return state

try:
    from langgraph.graph import StateGraph as LGStateGraph, END
    GraphClass = LGStateGraph
    END_NODE = END
except ImportError:
    GraphClass = FallbackStateGraph
    END_NODE = "END"


class MultiAgentFaceOrchestrator:
    """
    Master Orchestrator Graph: Connects Detector, Quality Inspector, Auto-Fix Enhancer,
    and Test Auditor into a self-healing diagnostic state machine.
    """

    def __init__(self):
        self.detector_agent = FaceDetectorAgent()
        self.quality_agent = QualityInspectorAgent()
        self.enhancer_agent = ImageEnhancerAgent()
        self.auditor_agent = TestAuditorAgent()
        
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = GraphClass(AgentState)

        # 1. Register Agents as Graph Nodes
        workflow.add_node("detector_node", self.node_detector)
        workflow.add_node("quality_node", self.node_quality_inspector)
        workflow.add_node("enhancer_node", self.node_enhancer)
        workflow.add_node("auditor_node", self.node_auditor)

        # 2. Wire Linear & Conditional Edges
        workflow.set_entry_point("detector_node")
        workflow.add_edge("detector_node", "quality_node")

        # Conditional Self-Healing Routing Loop
        workflow.add_conditional_edges(
            "quality_node",
            self.route_quality_decision,
            {
                "retry_enhancement": "enhancer_node",
                "proceed_to_audit": "auditor_node"
            }
        )

        # Loop back from Enhancer Agent to Detector Agent
        workflow.add_edge("enhancer_node", "detector_node")
        
        # Terminal edge
        workflow.add_edge("auditor_node", END_NODE)

        return workflow.compile()

    # --- NODE FUNCTIONS ---

    def node_detector(self, state: AgentState) -> AgentState:
        image = state["current_image"]
        detections = self.detector_agent.detect_faces(image)
        state["detections"] = detections
        return state

    def node_quality_inspector(self, state: AgentState) -> AgentState:
        image = state["current_image"]
        detections = state["detections"]
        quality_report = self.quality_agent.inspect_quality(image, detections)
        state["quality_report"] = quality_report
        return state

    def route_quality_decision(self, state: AgentState) -> str:
        quality_status = state["quality_report"].get("status", "ACCEPTABLE")
        iterations = state.get("iteration_count", 1)
        max_iters = state.get("max_iterations", 3)

        # Proceed to audit if quality is good or max retries reached
        if quality_status in ["EXCELLENT", "ACCEPTABLE"] or iterations >= max_iters:
            return "proceed_to_audit"
        else:
            return "retry_enhancement"

    def node_enhancer(self, state: AgentState) -> AgentState:
        image = state["current_image"]
        quality_report = state["quality_report"]
        
        enhanced_image, fix_action = self.enhancer_agent.enhance_image(image, quality_report)
        
        state["current_image"] = enhanced_image
        state["iteration_count"] = state.get("iteration_count", 1) + 1
        
        history = state.get("enhancement_history", [])
        history.append(fix_action)
        state["enhancement_history"] = history
        
        return state

    def node_auditor(self, state: AgentState) -> AgentState:
        audit_report = self.auditor_agent.generate_audit_report(state)
        state["audit_report"] = audit_report
        return state

    def run(self, input_image, metadata=None, max_iterations=3) -> Dict[str, Any]:
        """
        Executes the multi-agent graph for an input image frame.
        """
        initial_state = AgentState(
            current_image=input_image.copy(),
            original_image=input_image.copy(),
            metadata=metadata or {},
            detections=[],
            quality_report={},
            iteration_count=1,
            max_iterations=max_iterations,
            enhancement_history=[],
            audit_report={}
        )

        final_state = self.graph.invoke(initial_state)
        return final_state
