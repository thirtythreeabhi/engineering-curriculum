"""
Exercise 3.2: Terraform Directed Acyclic Graph (DAG) Execution Planner

Problem:
Terraform constructs a DAG of infrastructure resources to determine the exact
evaluation walk order. Independent resources execute concurrently in waves, while
dependent resources await completion of upstream nodes.
"""

from collections import defaultdict, deque
from typing import Dict, List, Set


class TerraformDagPlanner:
    def __init__(self):
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.nodes: Set[str] = set()

    def add_resource(self, resource_id: str, depends_on: List[str] = None) -> None:
        self.nodes.add(resource_id)
        if depends_on:
            for dep in depends_on:
                self.nodes.add(dep)
                self.dependencies[resource_id].add(dep)

    def plan_execution_waves(self) -> List[List[str]]:
        """
        Computes parallel execution waves using topological sorting (Kahn's algorithm variant).
        Returns a list of waves, where all resources in a wave can be provisioned in parallel.
        """
        in_degree = {node: len(self.dependencies[node]) for node in self.nodes}
        reverse_graph = defaultdict(set)
        for node, deps in self.dependencies.items():
            for dep in deps:
                reverse_graph[dep].add(node)

        waves: List[List[str]] = []
        ready = [node for node, deg in in_degree.items() if deg == 0]

        while ready:
            ready.sort()
            current_wave = list(ready)
            waves.append(current_wave)
            next_ready = []

            for node in current_wave:
                for downstream in reverse_graph[node]:
                    in_degree[downstream] -= 1
                    if in_degree[downstream] == 0:
                        next_ready.append(downstream)

            ready = next_ready

        total_processed = sum(len(w) for w in waves)
        if total_processed != len(self.nodes):
            raise ValueError("Cycle detected in Terraform resource dependency graph!")

        return waves


if __name__ == "__main__":
    print("==> Running Exercise 3.2: Terraform DAG Execution Planner...")
    planner = TerraformDagPlanner()

    # Define infrastructure resources and dependencies
    planner.add_resource("azurerm_resource_group.rg")
    planner.add_resource("azurerm_virtual_network.vnet", depends_on=["azurerm_resource_group.rg"])
    planner.add_resource("azurerm_subnet.aks_subnet", depends_on=["azurerm_virtual_network.vnet"])
    planner.add_resource("azurerm_subnet.db_subnet", depends_on=["azurerm_virtual_network.vnet"])
    planner.add_resource("azurerm_kubernetes_cluster.aks", depends_on=["azurerm_subnet.aks_subnet"])
    planner.add_resource("azurerm_postgresql_server.db", depends_on=["azurerm_subnet.db_subnet"])

    waves = planner.plan_execution_waves()

    # Wave 0: Resource group
    assert waves[0] == ["azurerm_resource_group.rg"]
    # Wave 1: VNet
    assert waves[1] == ["azurerm_virtual_network.vnet"]
    # Wave 2: Subnets (aks_subnet and db_subnet can provision concurrently)
    assert set(waves[2]) == {"azurerm_subnet.aks_subnet", "azurerm_subnet.db_subnet"}
    # Wave 3: AKS cluster and Postgres DB (provision concurrently)
    assert set(waves[3]) == {"azurerm_kubernetes_cluster.aks", "azurerm_postgresql_server.db"}

    print(f"[PASS] Exercise 3.2 verified (Planned 4 parallel execution waves).")
