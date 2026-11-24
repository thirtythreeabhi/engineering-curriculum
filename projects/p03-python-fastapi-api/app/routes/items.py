"""Item catalog endpoints demonstrating scope-based authorization."""

from typing import Dict, List
from fastapi import APIRouter, HTTPException, Security, status
from app.auth import get_current_user
from app.schemas import ItemCreate, ItemResponse, ItemUpdate, UserResponse

router = APIRouter(prefix="/items", tags=["Catalog"])

ITEMS_DB: Dict[int, dict] = {
    1: {"id": 1, "title": "Ergonomic Mechanical Keyboard", "description": "Split wireless keyboard", "price": 189.99, "stock": 15},
    2: {"id": 2, "title": "Ultra-Wide 4K Monitor", "description": "34-inch curved IPS display", "price": 649.00, "stock": 8},
}
_id_seq = 2


@router.get("", response_model=List[ItemResponse])
async def list_items(
    current_user: UserResponse = Security(get_current_user, scopes=["read:items"])
):
    """Retrieve all catalog items. Requires 'read:items' scope."""
    return list(ITEMS_DB.values())


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    item_in: ItemCreate,
    current_user: UserResponse = Security(get_current_user, scopes=["write:items"])
):
    """Create a new catalog item. Requires 'write:items' scope."""
    global _id_seq
    _id_seq += 1
    new_item = {
        "id": _id_seq,
        "title": item_in.title,
        "description": item_in.description,
        "price": item_in.price,
        "stock": item_in.stock,
    }
    ITEMS_DB[_id_seq] = new_item
    return new_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    current_user: UserResponse = Security(get_current_user, scopes=["admin"])
):
    """Delete a catalog item. Requires 'admin' scope."""
    if item_id not in ITEMS_DB:
        raise HTTPException(status_code=404, detail="Item not found")
    del ITEMS_DB[item_id]
    return None
