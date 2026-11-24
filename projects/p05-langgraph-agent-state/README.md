# Project 05: LangGraph Multi-Tool Agent with Typed State & Human-in-the-Loop Interruption

Production-grade agent state machine architecture modeled after LangGraph, featuring typed state schemas, channel reducers (`operator.add`), dynamic conditional branching, human-in-the-loop (HITL) authorization gates for privileged actions, and state time-travel resumes.

## Core Architectural Concepts

1. **Typed State & Channel Reducers**:
   - Uses `Annotated[List[T], operator.add]` to specify how partial node updates are merged into the global state without destructive overwriting.

2. **Privileged Tool Boundaries & HITL Interruptions**:
   - Distinguishes read-only research tools from privileged side-effect actions (`execute_portfolio_rebalance`).
   - Dynamic conditional routing halts execution when a privileged tool is proposed, persisting an interrupted checkpoint until human approval is delivered.

3. **State Checkpointing & Time-Travel**:
   - Captures an immutable snapshot of state before and after every node transition.
   - Enables time-travel debugging: reverting execution to an arbitrary past checkpoint, inspecting state drift, or branching alternative execution paths.

## Directory Structure

```
p05-langgraph-agent-state/
├── agent/
│   ├── graph.py
│   ├── research_agent.py
│   ├── state.py
│   └── tools.py
├── README.md
├── requirements.txt
└── tests/
    └── test_agent_graph.py
```

## Running Tests

```bash
PYTHONPATH=. pytest tests/ -v
```
