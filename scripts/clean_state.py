import asyncio
import sqlite3
from sqlalchemy import text
from sentinelops.core.database import async_session_factory

async def clean():
    # 1. Clean sqlite RAG store
    try:
        conn = sqlite3.connect('data/rag_store/vectors.db')
        cur = conn.cursor()
        cur.execute("DELETE FROM vector_chunks WHERE document_id LIKE 'runbook-auth-memory-leak-%'")
        conn.commit()
        cnt = cur.execute('SELECT count(distinct document_id) FROM vector_chunks').fetchone()[0]
        print(f'RAG vector store cleaned. Distinct documents remaining: {cnt}')
        conn.close()
    except Exception as e:
        print(f'RAG clean err: {e}')

    # 2. Clean postgres duplicate incidents
    async with async_session_factory() as session:
        inc_res = await session.execute(text("SELECT id, title FROM incidents ORDER BY created_at DESC"))
        incidents = inc_res.fetchall()
        seen_titles = set()
        keep_ids = []
        delete_ids = []

        for inc_id, title in incidents:
            norm_title = title.strip().lower()
            if norm_title in seen_titles:
                delete_ids.append(str(inc_id))
            else:
                seen_titles.add(norm_title)
                keep_ids.append(str(inc_id))

        print(f'Total incidents: {len(incidents)}. Keeping {len(keep_ids)}, deleting {len(delete_ids)} duplicates.')

        for d_id in delete_ids:
            # Proper FK dependency order:
            await session.execute(text(f"DELETE FROM replay_events WHERE incident_id = '{d_id}'"))
            await session.execute(text(f"DELETE FROM replay_frames WHERE incident_id = '{d_id}'"))
            await session.execute(text(f"DELETE FROM replay_sessions WHERE incident_id = '{d_id}'"))
            await session.execute(text(f"DELETE FROM incident_ancestry WHERE incident_id = '{d_id}' OR root_incident_id = '{d_id}'"))
            for tbl in [
                'ai_confidence_validations', 'ai_insights', 'ai_reasoning_logs', 'ai_recommendations',
                'incident_events', 'incident_summaries', 'incident_timeline', 'recommendations',
                'remediation_orchestrations', 'simulated_incidents', 'recovery_timelines', 'remediation_actions'
            ]:
                await session.execute(text(f"DELETE FROM {tbl} WHERE incident_id = '{d_id}'"))
            await session.execute(text(f"DELETE FROM incidents WHERE id = '{d_id}'"))

        await session.commit()
        print('PostgreSQL incident deduplication committed successfully!')

if __name__ == '__main__':
    asyncio.run(clean())
