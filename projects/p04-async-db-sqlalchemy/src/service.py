"""Service layer orchestrating transactions with async context managers."""

from typing import List, Optional
from src.database import DatabaseManager
from src.models import ProductInventory
from src.repository import InventoryRepository


class InventoryService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def sync_catalog_batch(self, items: List[dict], batch_size: int = 50) -> int:
        """
        Processes catalog updates in atomic transaction batches.
        Uses `async with session.begin():` context manager.
        """
        total_upserted = 0
        for i in range(0, len(items), batch_size):
            chunk = items[i : i + batch_size]
            # On SQLite, serialize writes across concurrent coroutines to prevent busy locks
            if "sqlite" in self.db.db_url:
                async with self.db._write_lock:
                    async with self.db.session() as session:
                        async with session.begin():
                            repo = InventoryRepository(session)
                            count = await repo.batched_upsert(chunk)
                            for item in chunk:
                                await repo.log_audit(
                                    sku=item["sku"],
                                    delta=item["quantity"],
                                    reason="catalog_sync_upsert",
                                )
                            total_upserted += count
            else:
                async with self.db.session() as session:
                    async with session.begin():
                        repo = InventoryRepository(session)
                        count = await repo.batched_upsert(chunk)
                        for item in chunk:
                            await repo.log_audit(
                                sku=item["sku"],
                                delta=item["quantity"],
                                reason="catalog_sync_upsert",
                            )
                        total_upserted += count
        return total_upserted

    async def get_inventory(self, sku: str) -> Optional[ProductInventory]:
        async with self.db.session() as session:
            repo = InventoryRepository(session)
            return await repo.get_by_sku(sku)

    async def get_all_inventory(self) -> List[ProductInventory]:
        async with self.db.session() as session:
            repo = InventoryRepository(session)
            return await repo.list_all()
