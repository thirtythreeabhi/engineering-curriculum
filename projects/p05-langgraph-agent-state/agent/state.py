"""State schema with channel reducers for LangGraph agent."""

import operator
from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict


class ToolCall(TypedDict):
    tool_name: str
    args: Dict[str, Any]
    privileged: bool


class Message(TypedDict):
    role: str  # 'user', 'assistant', 'tool', 'system'
    content: str
    tool_calls: Optional[List[ToolCall]]


class AgentState(TypedDict):
    # Channel reducers: updates returned by nodes are reduced via operator.add
    messages: Annotated[List[Message], operator.add]
    scratchpad: Annotated[List[str], operator.add]
    pending_approval: Optional[ToolCall]
    approved_actions: Annotated[List[str], operator.add]
    iteration_count: int
    final_answer: Optional[str]
