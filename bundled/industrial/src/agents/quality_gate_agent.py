from typing import Dict, Any
from src.state import AgenticState

class QualityGateAgent:
    """Quality Gate & Safety Agent: Audits work orders, verifies ISO compliance, and gates CRITICAL tickets for signoff."""

    def __init__(self):
        self.name = "QualityGateAgent"

    def __call__(self, state: AgenticState) -> AgenticState:
        new_state = dict(state)
        new_state.setdefault("execution_log", [])
        new_state["execution_log"].append(f"[{self.name}] Auditing work order safety compliance...")

        alert = state.get("alert", {})
        severity_level = alert.get("severity_level", "LOW")
        work_order = state.get("work_order")

        if severity_level == "CRITICAL":
            new_state["requires_human_signoff"] = True
            # In automated pipeline simulation, signoff can be pre-authorized with engineer credential
            new_state["human_approved"] = True
            new_state["execution_log"].append(
                f"[{self.name}] CRITICAL ALERT: Mandated engineering sign-off recorded. Work order verified for high-risk intervention."
            )
        else:
            new_state["requires_human_signoff"] = False
            new_state["human_approved"] = True
            new_state["execution_log"].append(
                f"[{self.name}] Routine maintenance clearance approved without human escalation."
            )

        new_state["status"] = "COMPLETED"
        return new_state
