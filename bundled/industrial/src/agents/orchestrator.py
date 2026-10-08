from typing import Dict, Any
from src.state import AgenticState

class OrchestratorAgent:
    """
    Supervisor / Master Orchestrator Agent:
    Monitors execution state, evaluates worker outputs, checks error triggers,
    and dynamically dispatches work to the appropriate specialized agent.
    """

    def __init__(self):
        self.name = "OrchestratorAgent"

    def determine_next_step(self, state: AgenticState) -> str:
        """Evaluates current state conditions to route to the next agent node."""
        errors = state.get("errors", [])
        unresolved_errors = [e for e in errors if not e.get("resolved", False)]
        status = state.get("status", "")

        # Rule 1: Priority Route to SelfHealingAgent if any unresolved error exists
        if unresolved_errors:
            return "self_healing_agent"

        # Rule 2: If status is FAILED (max retries reached), stop pipeline
        if status == "FAILED":
            return "END"

        # Rule 3: If features are missing, route to VisionAgent
        features = state.get("features")
        if not features:
            return "vision_agent"

        # Rule 4: If features exist but no defect alert diagnosed, route to DiagnosticAgent
        alert = state.get("alert")
        if not alert:
            return "diagnostic_agent"

        # Rule 5: If alert is diagnosed:
        severity_level = alert.get("severity_level", "PASS")
        work_order = state.get("work_order")

        if severity_level in ["MEDIUM", "CRITICAL"]:
            if not work_order:
                if state.get("retry_count", 0) >= 2:
                    return "quality_gate_agent"
                return "maintenance_rag_agent"

        # Rule 6: If work order synthesized or alert exists, route to QualityGateAgent for signoff
        if not state.get("human_approved", False):
            return "quality_gate_agent"

        # Rule 7: Workflow finished
        return "END"

    def __call__(self, state: AgenticState) -> AgenticState:
        new_state = dict(state)
        new_state.setdefault("execution_log", [])
        
        next_agent = self.determine_next_step(new_state)
        new_state["next_agent"] = next_agent
        new_state["execution_log"].append(
            f"[{self.name}] State evaluation complete. Next routed agent: -> {next_agent.upper()}"
        )
        return new_state
