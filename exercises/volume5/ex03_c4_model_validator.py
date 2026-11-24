"""
Exercise 5.3: C4 Architecture Model Validator

Problem:
The C4 model structures architecture into four hierarchical abstractions:
Context (1) -> Container (2) -> Component (3) -> Code (4).

Implement a C4ModelValidator:
1. Validates element definitions (Person, System, Container, Component).
2. Enforces hierarchical containment (Components must belong to a Container; Containers belong to a System).
3. Enforces boundary rules (e.g. an external Person cannot connect directly to internal Code).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class C4Element:
    id: str
    name: str
    type: str  # 'Person', 'System', 'Container', 'Component'
    parent_id: Optional[str] = None


@dataclass
class C4Relationship:
    source_id: str
    target_id: str
    description: str


class C4ModelValidator:
    def __init__(self):
        self.elements: Dict[str, C4Element] = {}
        self.relationships: List[C4Relationship] = []

    def add_element(self, element: C4Element) -> None:
        self.elements[element.id] = element

    def add_relationship(self, rel: C4Relationship) -> None:
        self.relationships.append(rel)

    def validate(self) -> List[str]:
        errors = []

        for elem in self.elements.values():
            # Hierarchy validation
            if elem.type == "Container" and elem.parent_id:
                parent = self.elements.get(elem.parent_id)
                if not parent or parent.type != "System":
                    errors.append(f"Container '{elem.name}' must have a parent System.")

            if elem.type == "Component" and elem.parent_id:
                parent = self.elements.get(elem.parent_id)
                if not parent or parent.type != "Container":
                    errors.append(f"Component '{elem.name}' must have a parent Container.")

        # Relationship boundary validation
        for rel in self.relationships:
            src = self.elements.get(rel.source_id)
            tgt = self.elements.get(rel.target_id)
            if not src or not tgt:
                errors.append(f"Relationship references nonexistent element: {rel.source_id} -> {rel.target_id}")
                continue

            # External person cannot directly call private Component (must interact via Container / System API boundary)
            if src.type == "Person" and tgt.type == "Component":
                errors.append(f"Boundary Violation: Person '{src.name}' cannot directly call internal Component '{tgt.name}'.")

        return errors


if __name__ == "__main__":
    print("==> Running Exercise 5.3: C4 Architecture Model Validator...")
    validator = C4ModelValidator()

    # Valid hierarchy
    validator.add_element(C4Element("user", "Customer", "Person"))
    validator.add_element(C4Element("sys_ecommerce", "E-Commerce System", "System"))
    validator.add_element(C4Element("cont_api", "Storefront API", "Container", parent_id="sys_ecommerce"))
    validator.add_element(C4Element("comp_auth", "Auth Controller", "Component", parent_id="cont_api"))

    # Valid relationship: Person -> Container
    validator.add_relationship(C4Relationship("user", "cont_api", "Submits checkout over HTTPS"))

    errors = validator.validate()
    assert len(errors) == 0, f"Expected 0 errors, got: {errors}"

    # Invalid boundary: Person directly calls internal Component
    validator.add_relationship(C4Relationship("user", "comp_auth", "Calls internal method"))
    errors_with_violation = validator.validate()
    assert len(errors_with_violation) == 1
    assert "Boundary Violation" in errors_with_violation[0]

    print("[PASS] Exercise 5.3 verified (C4 hierarchy and boundary validation passed).")
