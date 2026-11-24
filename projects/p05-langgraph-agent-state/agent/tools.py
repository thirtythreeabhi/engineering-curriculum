"""Tool registry with privileged execution boundaries."""

from typing import Any, Callable, Dict


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable[..., Any]] = {}
        self._privileged: Dict[str, bool] = {}

    def register(self, name: str, privileged: bool = False):
        def decorator(func: Callable[..., Any]):
            self._tools[name] = func
            self._privileged[name] = privileged
            return func
        return decorator

    def is_privileged(self, name: str) -> bool:
        return self._privileged.get(name, False)

    def execute(self, name: str, **kwargs) -> Any:
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")
        return self._tools[name](**kwargs)


registry = ToolRegistry()


@registry.register("search_knowledge_base", privileged=False)
def search_knowledge_base(query: str) -> str:
    """Read-only research tool to search knowledge base."""
    return f"KnowledgeBase results for '{query}': Portfolio contains 60% Equities, 40% Bonds. Target is 70/30."


@registry.register("calculate_allocation_delta", privileged=False)
def calculate_allocation_delta(current_equity: float, target_equity: float) -> str:
    """Calculates allocation adjustment percentage."""
    delta = target_equity - current_equity
    return f"Adjustment required: {delta:+.2f}% equities shift."


@registry.register("execute_portfolio_rebalance", privileged=True)
def execute_portfolio_rebalance(asset: str, amount_usd: float) -> str:
    """Privileged action that executes live trade and rebalances assets."""
    return f"EXECUTED TRADE: Purchased ${amount_usd:,.2f} of {asset}. Transaction ID: TX-99482."
