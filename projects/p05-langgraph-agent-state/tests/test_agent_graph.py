"""Pytest test suite for LangGraph state machine, HITL, and time-travel."""

import pytest
from agent.graph import StateGraph
from agent.research_agent import build_research_graph, resume_with_approval
from agent.state import AgentState


def test_agent_interrupts_at_privileged_tool():
    graph = build_research_graph()

    initial_state: AgentState = {
        "messages": [{
            "role": "user",
            "content": "Please analyze our investment portfolio and rebalance to 70% equities.",
            "tool_calls": None,
        }],
        "scratchpad": [],
        "pending_approval": None,
        "approved_actions": [],
        "iteration_count": 0,
        "final_answer": None,
    }

    result = graph.run_until_interrupt_or_end(initial_state)

    # Must be interrupted at human approval gate
    assert result["status"] == "interrupted"
    assert result["interrupted_node"] == "human_approval_gate"
    assert "checkpoint_id" in result

    interrupted_state = result["state"]
    assert interrupted_state["pending_approval"] is not None
    assert interrupted_state["pending_approval"]["tool_name"] == "execute_portfolio_rebalance"
    assert interrupted_state["pending_approval"]["privileged"] is True

    # Checkpoint timeline exists
    assert len(graph.checkpoints) >= 3


def test_agent_approval_resumes_and_finishes():
    graph = build_research_graph()

    initial_state: AgentState = {
        "messages": [{
            "role": "user",
            "content": "Rebalance portfolio to 70% equities.",
            "tool_calls": None,
        }],
        "scratchpad": [],
        "pending_approval": None,
        "approved_actions": [],
        "iteration_count": 0,
        "final_answer": None,
    }

    # Step 1: Run to interrupt
    interrupted = graph.run_until_interrupt_or_end(initial_state)
    chk_id = interrupted["checkpoint_id"]

    # Step 2: Grant human approval and resume execution
    completed = resume_with_approval(graph, chk_id, approve=True)

    assert completed["status"] == "completed"
    final_state = completed["state"]
    assert final_state["final_answer"] is not None
    assert "execute_portfolio_rebalance" in final_state["approved_actions"]

    # Verify privileged trade output appears in scratchpad
    assert any("EXECUTED TRADE" in s for s in final_state["scratchpad"])


def test_agent_human_rejection():
    graph = build_research_graph()

    initial_state: AgentState = {
        "messages": [{"role": "user", "content": "Rebalance portfolio", "tool_calls": None}],
        "scratchpad": [],
        "pending_approval": None,
        "approved_actions": [],
        "iteration_count": 0,
        "final_answer": None,
    }

    interrupted = graph.run_until_interrupt_or_end(initial_state)
    chk_id = interrupted["checkpoint_id"]

    # Reject privileged execution
    resumed = resume_with_approval(graph, chk_id, approve=False)

    # Privileged action should NOT have been approved or executed
    final_state = resumed["state"]
    assert "execute_portfolio_rebalance" not in final_state.get("approved_actions", [])
    assert any("REJECTED by human" in m["content"] for m in final_state["messages"])


def test_channel_reducers_accumulation():
    graph = build_research_graph()

    initial_state: AgentState = {
        "messages": [{"role": "user", "content": "Start research", "tool_calls": None}],
        "scratchpad": ["Initial entry"],
        "pending_approval": None,
        "approved_actions": [],
        "iteration_count": 0,
        "final_answer": None,
    }

    interrupted = graph.run_until_interrupt_or_end(initial_state)
    state = interrupted["state"]

    # Messages and scratchpad should have accumulated via channel reducers (operator.add)
    assert len(state["messages"]) > 1
    assert len(state["scratchpad"]) > 1
    assert state["scratchpad"][0] == "Initial entry"


def test_time_travel_checkpoint_rollback():
    graph = build_research_graph()

    initial_state: AgentState = {
        "messages": [{"role": "user", "content": "Start research", "tool_calls": None}],
        "scratchpad": [],
        "pending_approval": None,
        "approved_actions": [],
        "iteration_count": 0,
        "final_answer": None,
    }

    interrupted = graph.run_until_interrupt_or_end(initial_state)

    # Inspect first checkpoint (step 0)
    first_checkpoint = graph.checkpoints[0]
    assert first_checkpoint["state"]["iteration_count"] == 1

    # Time-travel rollback: fetch earlier state snapshot
    saved_state = graph.get_checkpoint(first_checkpoint["id"])
    assert saved_state is not None
    assert len(saved_state["state"]["messages"]) < len(interrupted["state"]["messages"])
