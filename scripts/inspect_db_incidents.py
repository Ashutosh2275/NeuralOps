import asyncio
import sys
from pathlib import Path

# Add backend/src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "src"))

from sentinelops.core.database import async_session_factory
from sentinelops.models.incident import Incident
from sqlalchemy import select

async def main():
    async with async_session_factory() as s:
        res = await s.execute(select(Incident).order_by(Incident.started_at.desc()))
        incs = res.scalars().all()
        print(f"Total incidents in DB: {len(incs)}")
        for inc in incs[:25]:
            print(f"[{inc.status.upper()}] {inc.title} | Svc: {inc.root_service} | ID: {inc.id} | Started: {inc.started_at}")

if __name__ == "__main__":
    asyncio.run(main())
