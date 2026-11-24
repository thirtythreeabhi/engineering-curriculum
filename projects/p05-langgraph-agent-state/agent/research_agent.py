"""Multi-tool research agent workflow with HITL approval and time-travel."""

from typing import Any, Dict
from agent.graph import END, StateGraph
from agent.state import AgentState, Message, ToolCall
from agent.tools import registry


def planner_node(state: AgentState) -> Dict[str, Any]:
    """Agent planner: determines next action based on message history and scratchpad."""
    iteration = state.get("iteration_count", 0) + 1
    scratchpad = state.get("scratchpad", [])
    approved = state.get("approved_actions", [])

    # Step 1: Research current portfolio
    if not any("KnowledgeBase" in s for s in scratchpad):
        return {
            "iteration_count": iteration,
            "scratchpad": ["Planned step: search knowledge base for current allocation."],
            "messages": [{
                "role": "assistant",
                "content": "Searching knowledge base for current asset allocation.",
                "tool_calls": [{
                    "tool_name": "search_knowledge_base",
                    "args": {"query": "current asset allocation"},
                    "privileged": False,
                }],
            }],
        }

    # Step 2: Compute delta
    if not any("Adjustment required" in s for s in scratchpad):
        return {
            "iteration_count": iteration,
            "scratchpad": ["Planned step: calculate rebalance delta."],
            "messages": [{
                "role": "assistant",
                "content": "Calculating required portfolio adjustment.",
                "tool_calls": [{
                    "tool_name": "calculate_allocation_delta",
                    "args": {"current_equity": 60.0, "target_equity": 70.0},
                    "privileged": False,
                }],
            }],
        }

    # Step 3: Propose privileged execution if not yet approved or executed
    if "execute_portfolio_rebalance" not in approved and not any("EXECUTED TRADE" in s for s in scratchpad):
        privileged_call: ToolCall = {
            "tool_name": "execute_portfolio_rebalance",
            "args": {"asset": "S&P 500 Index Fund", "amount_usd": 150000.00},
            "privileged": True,
        }
        return {
            "iteration_count": iteration,
            "pending_approval": privileged_call,
            "scratchpad": ["Proposing privileged trade rebalance of $150,000."],
            "messages": [{
                "role": "assistant",
                "content": "Requires human authorization to execute live trade of $150,000.",
                "tool_calls": [privileged_call],
            }],
        }

    # Step 4: Final synthesis
    return {
        "iteration_count": iteration,
        "final_answer": "Portfolio rebalance analysis and execution completed successfully.",
        "scratchpad": ["Synthesis complete."],
        "messages": [{
            "role": "assistant",
            "content": "Portfolio rebalance is complete. Target 70/30 allocation achieved.",
            "tool_calls": None,
        }],
    }


def tool_node(state: AgentState) -> Dict[str, Any]:
    """Executes standard, non-privileged tools."""
    last_msg = state["messages"][-1]
    tool_calls = last_msg.get("tool_calls") or []
    results = []

    for call in tool_calls:
        name = call["tool_name"]
        args = call["args"]
        output = registry.execute(name, **args)
        results.append(output)

    return {
        "scratchpad": results,
        "messages": [{
            "role": "tool",
            "content": "\n".join(results),
            "tool_calls": None,
        }],
    }


def human_approval_gate(state: AgentState) -> Dict[str, Any]:
    """Human approval gate: node reached during HITL evaluation."""
    # When resume occurs, state will have either approved_actions or rejected
    pending = state.get("pending_approval")
    return {"pending_approval": pending}


def privileged_tool_node(state: AgentState) -> Dict[str, Any]:
    """Executes privileged tool after human gate approval."""
    pending = state.get("pending_approval")
    if not pending:
        return {}

    output = registry.execute(pending["tool_name"], **pending["args"])
    return {
        "pending_approval": None,
        "approved_actions": [pending["tool_name"]],
        "scratchpad": [output],
        "messages": [{
            "role": "tool",
            "content": f"[PRIVILEGED] {output}",
            "tool_calls": None,
        }],
    }


def route_after_planner(state: AgentState) -> str:
    """Dynamic conditional edge routing."""
    if state.get("final_answer") is not None:
        return END

    if state.get("pending_approval") is not None:
        return "human_approval_gate"

    last_msg = state["messages"][-1]
    if last_msg.get("tool_calls"):
        return "tool_node"

    return END


def build_research_graph() -> StateGraph:
    """Constructs the compiled state graph."""
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("tool_node", tool_node)
    graph.add_node("human_approval_gate", human_approval_gate)
    graph.add_node("privileged_tool_node", privileged_tool_node)

    graph.set_entry_point("planner")

    graph.add_conditional_edges("planner", route_after_planner)
    graph.add_edge("tool_node", "planner")
    graph.add_edge("privileged_tool_node", "planner")

    return graph


def resume_with_approval(graph: StateGraph, checkpoint_id: str, approve: bool) -> Dict[str, Any]:
    """Resumes graph execution from a specific checkpoint with human authorization decision."""
    checkpoint = graph.get_checkpoint(checkpoint_id)
    if not checkpoint:
        raise ValueError(f"Checkpoint {checkpoint_id} not found")

    state = copy_state = dict(checkpoint["state"])

    if approve:
        # Route directly to privileged execution
        state["approved_actions"] = state.get("approved_actions", []) + [state["pending_approval"]["tool_name"]]
        return graph.run_until_interrupt_or_end(state, start_node="privileged_tool_node")
    else:
        # Reject: clear pending and return to planner with rejection note
        rejected_tool = state["pending_approval"]["tool_name"]
        state["pending_approval"] = None
        state["scratchpad"] = state.get("scratchpad", []) + [f"Human rejected execution of {rejected_tool}."]
        state["messages"] = state.get("messages", []) + [{
            "role": "system",
            "content": f"Action {rejected_tool} was explicitly REJECTED by human supervisor.",
            "tool_calls": None,
        }]
        return graph.run_until_interrupt_or_end(state, start_node="planner")
