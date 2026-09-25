from typing import Any, Dict, List, TypedDict

from langgraph.graph import END, StateGraph

from nodes import allocate_node, diagnose_node, execute_node, habits_node, rewire_node


class DreamState(TypedDict, total=False):
    user_id: str
    stage: str
    last_message: str
    last_reply: str
    financials: Dict[str, Any]
    dreams: List[Dict[str, Any]]
    beliefs: List[Dict[str, Any]]
    budget: Dict[str, Any]
    goal_gaps: List[Dict[str, Any]]
    habits: List[str]
    conversation_history: List[Dict[str, str]]


def route_stage(state: DreamState) -> str:
    """Send this turn's message to whichever stage the session is currently in."""
    return state.get("stage", "diagnose")


def build_graph():
    workflow = StateGraph(DreamState)

    workflow.add_node("diagnose", diagnose_node)
    workflow.add_node("rewire", rewire_node)
    workflow.add_node("execute", execute_node)
    workflow.add_node("allocate", allocate_node)
    workflow.add_node("habits", habits_node)

    workflow.set_conditional_entry_point(
        route_stage,
        {
            "diagnose": "diagnose",
            "rewire": "rewire",
            "execute": "execute",
            "allocate": "allocate",
            "habits": "habits",
            "done": END,
        },
    )

    # Diagnose always waits for the user's next answer.
    workflow.add_edge("diagnose", END)

    # Rewire waits for more conversation UNLESS it just completed (belief +
    # reframe captured) — in that case, cascade straight into the remaining
    # stages, since Execute/Allocate/Habits are deterministic and need no
    # further user input to produce their first output.
    def after_rewire(state: DreamState) -> str:
        return "execute" if state.get("stage") == "execute" else END

    workflow.add_conditional_edges("rewire", after_rewire, {"execute": "execute", END: END})

    workflow.add_edge("execute", "allocate")
    workflow.add_edge("allocate", "habits")
    workflow.add_edge("habits", END)

    return workflow.compile()
