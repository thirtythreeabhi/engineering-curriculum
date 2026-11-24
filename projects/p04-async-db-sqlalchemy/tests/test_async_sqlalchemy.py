"""Comprehensive pytest suite for async SQLAlchemy 2.0 operations."""

import asyncio
import pytest
from src.database import DatabaseManager
from src.repository import InventoryRepository
from src.service import InventoryService


async def create_test_db():
    manager = DatabaseManager("sqlite+aiosqlite:///:memory:")
    await manager.init_schema()
    return manager


def test_batched_upsert_inserts_and_updates():
    async def _test():
        db_manager = await create_test_db()
        try:
            service = InventoryService(db_manager)

            initial_items = [
                {"sku": "SKU-001", "name": "Keycap Set", "quantity": 100, "unit_price": 29.99},
                {"sku": "SKU-002", "name": "Coiled Cable", "quantity": 40, "unit_price": 45.00},
                {"sku": "SKU-003", "name": "Desk Mat XXL", "quantity": 15, "unit_price": 35.50},
            ]

            # Initial upsert (acts as INSERT)
            count = await service.sync_catalog_batch(initial_items)
            assert count == 3

            p1 = await service.get_inventory("SKU-001")
            assert p1 is not None
            assert p1.quantity == 100
            assert p1.unit_price == 29.99

            # Second upsert with modified quantity and price (acts as UPDATE)
            updated_items = [
                {"sku": "SKU-001", "name": "Keycap Set (V2)", "quantity": 120, "unit_price": 34.99},
                {"sku": "SKU-004", "name": "Switch Puller", "quantity": 200, "unit_price": 8.50},
            ]
            await service.sync_catalog_batch(updated_items)

            # Verify SKU-001 was updated in-place without duplicate
            p1_updated = await service.get_inventory("SKU-001")
            assert p1_updated is not None
            assert p1_updated.name == "Keycap Set (V2)"
            assert p1_updated.quantity == 120
            assert p1_updated.unit_price == 34.99

            # Verify SKU-004 was newly inserted
            p4 = await service.get_inventory("SKU-004")
            assert p4 is not None
            assert p4.quantity == 200

            all_items = await service.get_all_inventory()
            assert len(all_items) == 4
        finally:
            await db_manager.drop_schema()
            await db_manager.close()

    asyncio.run(_test())


def test_concurrent_batched_upserts():
    async def _test():
        db_manager = await create_test_db()
        try:
            service = InventoryService(db_manager)

            # Generate 5 concurrent batches
            async def worker(worker_id: int):
                batch = [
                    {
                        "sku": f"CONCURRENT-{i}",
                        "name": f"Product {i} from Worker {worker_id}",
                        "quantity": worker_id * 10 + i,
                        "unit_price": 10.0 + i,
                    }
                    for i in range(10)
                ]
                return await service.sync_catalog_batch(batch)

            results = await asyncio.gather(*(worker(wid) for wid in range(1, 6)))
            assert len(results) == 5
            assert all(r == 10 for r in results)

            all_items = await service.get_all_inventory()
            assert len(all_items) == 10
        finally:
            await db_manager.drop_schema()
            await db_manager.close()

    asyncio.run(_test())


def test_transaction_rollback_on_failure():
    async def _test():
        db_manager = await create_test_db()
        try:
            service = InventoryService(db_manager)

            with pytest.raises(RuntimeError, match="Simulated crash during batch transaction"):
                async with db_manager.session() as session:
                    async with session.begin():
                        repo = InventoryRepository(session)
                        await repo.batched_upsert([
                            {"sku": "ROLLBACK-01", "name": "Temporary Item", "quantity": 1, "unit_price": 99.0}
                        ])
                        # Trigger error before commit
                        raise RuntimeError("Simulated crash during batch transaction")

            item = await service.get_inventory("ROLLBACK-01")
            assert item is None
        finally:
            await db_manager.drop_schema()
            await db_manager.close()

    asyncio.run(_test())
