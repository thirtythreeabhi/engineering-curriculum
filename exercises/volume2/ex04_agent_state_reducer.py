"""
Exercise 2.4: Agent State Channels and Channel Reducers

Problem:
In LangGraph multi-agent architectures, independent nodes emit partial state updates,
and multiple parallel branches can finish in arbitrary order within a single superstep.
Instead of overwriting the entire state dictionary, each channel specifies a reducer
function (e.g. operator.add for lists, set union, or custom merge).

Implement an AgentStateEngine:
1. Registers channels with specific reducer functions (and optional defaults).
2. Applies reducers consistently even when a channel key is absent from initial state.
3. Supports deterministic merging across concurrent parallel branch updates.
4. Maintains an immutable history of state checkpoints.
"""

import copy
import operator
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple


class AgentStateEngine:
    def __init__(
        self,
        channel_reducers: Dict[str, Callable[[Any, Any], Any]],
        channel_defaults: Optional[Dict[str, Any]] = None,
    ):
        self.reducers = channel_reducers
        self.defaults = channel_defaults or {}
        self.current_state: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []

    def set_initial_state(self, initial: Dict[str, Any]) -> None:
        self.current_state = copy.deepcopy(initial)
        self.history.append(copy.deepcopy(self.current_state))

    def _reduce_field(self, state: Dict[str, Any], key: str, val: Any) -> Any:
        if key not in self.reducers:
            return copy.deepcopy(val)

        reducer = self.reducers[key]
        if key in state:
            return reducer(state[key], copy.deepcopy(val))
        if key in self.defaults:
            return reducer(copy.deepcopy(self.defaults[key]), copy.deepcopy(val))
        # Key absent from both initial state and explicit defaults:
        # For additive/collection types, reduce against empty identity so custom
        # reducers (e.g. deduplication/transformation) still run on the first write.
        if isinstance(val, (list, tuple, str, int, float)):
            return reducer(type(val)(), copy.deepcopy(val))
        return copy.deepcopy(val)

    def dispatch_update(self, update: Dict[str, Any]) -> Dict[str, Any]:
        new_state = copy.deepcopy(self.current_state)
        for key, val in update.items():
            new_state[key] = self._reduce_field(new_state, key, val)

        self.current_state = new_state
        self.history.append(copy.deepcopy(new_state))
        return self.current_state

    def dispatch_parallel_updates(
        self, branch_updates: Sequence[Tuple[str, Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Deterministically merges updates emitted concurrently by parallel branches
        within the same graph superstep. Sorting by branch_id ensures identical
        output regardless of thread/async completion order.
        """
        new_state = copy.deepcopy(self.current_state)
        for _branch_id, update in sorted(branch_updates, key=lambda item: item[0]):
            for key, val in update.items():
                new_state[key] = self._reduce_field(new_state, key, val)

        self.current_state = new_state
        self.history.append(copy.deepcopy(new_state))
        return self.current_state


if __name__ == "__main__":
    print("==> Running Exercise 2.4: Agent State Reducers...")
    reducers = {
        "messages": operator.add,
        "scratchpad": operator.add,
        "step_count": lambda a, b: a + b,
        "sources": lambda existing, incoming: sorted(set(existing) | set(incoming)),
    }

    engine = AgentStateEngine(reducers, channel_defaults={"sources": []})
    # Note: "sources" and "step_count" are intentionally omitted from initial state
    engine.set_initial_state({
        "messages": ["User: Search papers on RAG."],
        "scratchpad": ["Init"],
        "status": "IDLE",
    })

    # Superstep 1: Two concurrent parallel branches complete out of order (branch_b before branch_a)
    state_after_parallel = engine.dispatch_parallel_updates([
        (
            "branch_b_sparse",
            {
                "messages": ["Sparse: BM25 matched 3 docs."],
                "scratchpad": ["BM25 done."],
                "step_count": 1,
                "sources": ["bm25", "shared_doc"],
            },
        ),
        (
            "branch_a_dense",
            {
                "messages": ["Dense: Vector search matched 5 docs."],
                "scratchpad": ["Dense done."],
                "step_count": 1,
                "sources": ["qdrant", "shared_doc"],
            },
        ),
    ])

    # Regardless of arrival order, branch_a is reduced before branch_b deterministically
    assert state_after_parallel["messages"] == [
        "User: Search papers on RAG.",
        "Dense: Vector search matched 5 docs.",
        "Sparse: BM25 matched 3 docs.",
    ]
    assert state_after_parallel["step_count"] == 2
    assert state_after_parallel["sources"] == ["bm25", "qdrant", "shared_doc"]

    # Superstep 2: Synthesis node
    final_state = engine.dispatch_update({
        "messages": ["Assistant: Synthesized answer."],
        "scratchpad": ["Synthesis complete."],
        "step_count": 1,
        "status": "COMPLETED",
    })

    assert len(final_state["messages"]) == 4
    assert len(final_state["scratchpad"]) == 4
    assert final_state["step_count"] == 3
    assert final_state["status"] == "COMPLETED"
    assert len(engine.history) == 3

    print("[PASS] Exercise 2.4 verified (Absent-key reducers & deterministic parallel branch merge).")
