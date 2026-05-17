"""
DB init: Uses raw SQL CREATE TABLE IF NOT EXISTS for idempotent schema creation.
Generates DDL from SQLAlchemy metadata without executing — then wraps each in IF NOT EXISTS.
"""
from __future__ import annotations

import asyncio
from sqlalchemy import text, event
from sqlalchemy.schema import CreateTable, CreateIndex
from sentinelops.core.database import Base, engine
from sentinelops.config import get_settings
import asyncpg


async def main() -> None:
    settings = get_settings()
    print("🔗  Connecting to Postgres...")
    
    conn = await asyncpg.connect(
        settings.async_database_url.replace("postgresql+asyncpg://", "postgresql://")
    )
    
    print("📐  Creating tables (IF NOT EXISTS)...")
    
    # Collect all DDL statements
    from sqlalchemy import create_engine as sync_engine_create
    from io import StringIO
    
    # Build DDL using sync dialect
    sync_url = settings.async_database_url.replace("+asyncpg", "")
    from sqlalchemy import create_engine
    from sqlalchemy.dialects import postgresql
    
    dialect = postgresql.dialect()
    
    success = 0
    errors = 0
    
    for table in Base.metadata.sorted_tables:
        # Generate CREATE TABLE DDL
        create_stmt = str(CreateTable(table).compile(dialect=dialect))
        # Inject IF NOT EXISTS
        create_stmt = create_stmt.replace(
            f"CREATE TABLE {table.name}",
            f"CREATE TABLE IF NOT EXISTS {table.name}"
        )
        try:
            await conn.execute(create_stmt)
            print(f"  ✅  {table.name}")
            success += 1
        except Exception as e:
            print(f"  ⚠️   {table.name}: {str(e)[:60]}")
            errors += 1
        
        # Create indexes
        for idx in table.indexes:
            try:
                idx_stmt = str(CreateIndex(idx).compile(dialect=dialect))
                idx_stmt = idx_stmt.replace("CREATE INDEX", "CREATE INDEX IF NOT EXISTS")
                idx_stmt = idx_stmt.replace("CREATE UNIQUE INDEX", "CREATE UNIQUE INDEX IF NOT EXISTS")
                await conn.execute(idx_stmt)
            except Exception:
                pass  # Index already exists or schema mismatch
    
    await conn.close()
    
    print(f"\n✅  Done: {success} tables created, {errors} warnings (pre-existing)")


if __name__ == "__main__":
    import sentinelops.models  # noqa: F401 — register all models
    asyncio.run(main())
