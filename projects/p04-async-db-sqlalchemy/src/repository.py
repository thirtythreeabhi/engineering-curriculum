"""Repository layer implementing batched upserts and query operations."""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import ProductInventory, InventoryAudit


class InventoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def batched_upsert(self, items: List[dict]) -> int:
        """
        Executes an atomic batched upsert (ON CONFLICT DO UPDATE) on the inventory table.
        Adapts dynamically between PostgreSQL and SQLite dialects.
        """
        if not items:
            return 0

        dialect_name = self.session.bind.dialect.name
        now = datetime.now(timezone.utc)

        if dialect_name == "postgresql":
            stmt = pg_insert(ProductInventory).values(items)
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=["sku"],
                set_={
                    "name": stmt.excluded.name,
                    "quantity": stmt.excluded.quantity,
                    "unit_price": stmt.excluded.unit_price,
                    "updated_at": now,
                },
            )
        else:
            # Default to SQLite ON CONFLICT DO UPDATE
            stmt = sqlite_insert(ProductInventory).values(items)
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=["sku"],
                set_={
                    "name": stmt.excluded.name,
                    "quantity": stmt.excluded.quantity,
                    "unit_price": stmt.excluded.unit_price,
                    "updated_at": now,
                },
            )

        result = await self.session.execute(upsert_stmt)
        return len(items)

    async def get_by_sku(self, sku: str) -> Optional[ProductInventory]:
        stmt = select(ProductInventory).where(ProductInventory.sku == sku)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> List[ProductInventory]:
        stmt = select(ProductInventory).order_by(ProductInventory.sku)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def log_audit(self, sku: str, delta: int, reason: str) -> None:
        audit = InventoryAudit(sku=sku, delta=delta, reason=reason)
        self.session.add(audit)
