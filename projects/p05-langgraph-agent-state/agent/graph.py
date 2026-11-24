"""LangGraph state machine engine with reducers, HITL interruption, and time-travel."""

import copy
import uuid
from typing import Any, Callable, Dict, List, Optional
from agent.state import AgentState, Message, ToolCall
from agent.tools import registry

END = "__END__"


class StateGraph:
    def __init__(self, state_schema=AgentState):
        self.state_schema = state_schema
        self.nodes: Dict[str, Callable[[AgentState], Dict[str, Any]]] = {}
        self.conditional_edges: Dict[str, Callable[[AgentState], str]] = {}
        self.standard_edges: Dict[str, str] = {}
        self.entry_point: Optional[str] = None
        self.checkpoints: List[Dict[str, Any]] = []

    def add_node(self, name: str, fn: Callable[[AgentState], Dict[str, Any]]) -> None:
        self.nodes[name] = fn

    def set_entry_point(self, name: str) -> None:
        self.entry_point = name

    def add_edge(self, from_node: str, to_node: str) -> None:
        self.standard_edges[from_node] = to_node

    def add_conditional_edges(self, from_node: str, routing_fn: Callable[[AgentState], str]) -> None:
        self.conditional_edges[from_node] = routing_fn

    def _apply_reducers(self, current_state: AgentState, updates: Dict[str, Any]) -> AgentState:
        """Applies channel reducers (e.g., operator.add for lists, overwrite for scalars)."""
        new_state = copy.deepcopy(current_state)
        for key, value in updates.items():
            if key in ["messages", "scratchpad", "approved_actions"]:
                current_list = new_state.get(key, [])
                new_state[key] = current_list + (value if isinstance(value, list) else [value])
            else:
                new_state[key] = value
        return new_state

    def save_checkpoint(self, state: AgentState, current_node: str) -> str:
        checkpoint_id = f"chk_{len(self.checkpoints)}_{uuid.uuid4().hex[:6]}"
        self.checkpoints.append({
            "id": checkpoint_id,
            "node": current_node,
            "state": copy.deepcopy(state),
        })
        return checkpoint_id

    def get_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        for chk in self.checkpoints:
            if chk["id"] == checkpoint_id:
                return chk
        return None

    def run_until_interrupt_or_end(
        self,
        initial_state: AgentState,
        start_node: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes the graph step-by-step.
        Interrupts if state enters a node requiring human approval.
        """
        state = copy.deepcopy(initial_state)
        current_node = start_node or self.entry_point
        assert current_node is not None, "Entry point not set"

        while current_node != END:
            # Check for HITL Interruption gate
            if current_node == "human_approval_gate" and state.get("pending_approval") is not None:
                chk_id = self.save_checkpoint(state, current_node)
                return {
                    "status": "interrupted",
                    "interrupted_node": current_node,
                    "checkpoint_id": chk_id,
                    "state": state,
                }

            # Execute node function
            node_fn = self.nodes[current_node]
            updates = node_fn(state)
            state = self._apply_reducers(state, updates)

            # Checkpoint after node execution
            self.save_checkpoint(state, current_node)

            # Determine next node via conditional or standard edge
            if current_node in self.conditional_edges:
                current_node = self.conditional_edges[current_node](state)
            elif current_node in self.standard_edges:
                current_node = self.standard_edges[current_node]
            else:
                current_node = END

        return {
            "status": "completed",
            "checkpoint_id": self.checkpoints[-1]["id"],
            "state": state,
        }
