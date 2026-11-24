"""
Exercise 2.4: Agent State Channels and Channel Reducers

Problem:
In LangGraph multi-agent architectures, independent nodes emit partial state updates.
Instead of overwriting the entire state dictionary, each channel specifies a reducer
function (e.g. operator.add for lists, union for sets, or custom merge).

Implement an AgentStateEngine:
1. Registers channels with specific reducer functions.
2. Applies node deltas atomically to produce the next state iteration.
3. Maintains an immutable history of state checkpoints.
"""

import copy
import operator
from typing import Any, Callable, Dict, List


class AgentStateEngine:
    def __init__(self, channel_reducers: Dict[str, Callable[[Any, Any], Any]]):
        self.reducers = channel_reducers
        self.current_state: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []

    def set_initial_state(self, initial: Dict[str, Any]) -> None:
        self.current_state = copy.deepcopy(initial)
        self.history.append(copy.deepcopy(self.current_state))

    def dispatch_update(self, update: Dict[str, Any]) -> Dict[str, Any]:
        new_state = copy.deepcopy(self.current_state)
        for key, val in update.items():
            if key in self.reducers and key in new_state:
                new_state[key] = self.reducers[key](new_state[key], val)
            else:
                new_state[key] = val

        self.current_state = new_state
        self.history.append(copy.deepcopy(new_state))
        return self.current_state


if __name__ == "__main__":
    print("==> Running Exercise 2.4: Agent State Reducers...")
    reducers = {
        "messages": operator.add,
        "scratchpad": operator.add,
        "step_count": lambda a, b: a + b,
    }

    engine = AgentStateEngine(reducers)
    engine.set_initial_state({
        "messages": ["User: Search papers on RAG."],
        "scratchpad": ["Init"],
        "step_count": 0,
        "status": "IDLE",
    })

    # Node 1 executes and emits partial state delta
    engine.dispatch_update({
        "messages": ["Assistant: Querying dense index."],
        "scratchpad": ["Dense search returned 5 docs."],
        "step_count": 1,
        "status": "RETRIEVING",
    })

    # Node 2 executes
    final_state = engine.dispatch_update({
        "messages": ["Assistant: Synthesized answer."],
        "scratchpad": ["Synthesis complete."],
        "step_count": 1,
        "status": "COMPLETED",
    })

    assert len(final_state["messages"]) == 3
    assert len(final_state["scratchpad"]) == 3
    assert final_state["step_count"] == 2
    assert final_state["status"] == "COMPLETED"
    assert len(engine.history) == 3

    print("[PASS] Exercise 2.4 verified (Accumulated 3 messages, total steps=2).")
