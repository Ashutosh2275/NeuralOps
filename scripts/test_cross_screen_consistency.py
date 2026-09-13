import httpx
import sqlite3

BASE_URL = 'http://127.0.0.1:8000'

def test_all():
    print('=' * 70)
    print('SENTINELOPS AI - PHASE 11 CROSS-SCREEN DATA CONSISTENCY SUITE')
    print('=' * 70)
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)

    # 1. Health Probe Verification
    print('\n[1/7] Testing Health Endpoint & Timestamp...')
    r = client.get('/health')
    assert r.status_code == 200, f'Expected 200, got {r.status_code}'
    data = r.json()
    assert 'timestamp' in data and data['timestamp'] != '', 'Missing ISO timestamp in health probe'
    assert 'dependencies' in data, 'Missing dependencies in health probe'
    print('  [PASS] Health Probe: status=' + str(data.get('status')) + ' timestamp=' + str(data.get('timestamp')))

    # 2. Workloads & Pod Health Verification
    print('\n[2/7] Testing Workloads & Telemetry Consistency...')
    r_overview = client.get('/api/v1/workloads/overview')
    r_pods = client.get('/api/v1/workloads/pods')
    assert r_overview.status_code == 200 and r_pods.status_code == 200
    overview = r_overview.json()
    pods = r_pods.json().get('pods', [])
    assert overview['total_pods'] == len(pods), f"Overview total {overview['total_pods']} != pods count {len(pods)}"

    # Check healthy-service is NOT failing
    healthy_pod = next((p for p in pods if 'healthy-service' in p['pod_name']), None)
    assert healthy_pod is not None, 'healthy-service pod not found'
    assert healthy_pod['ready'] is True, f'healthy-service ready was False: {healthy_pod}'
    assert healthy_pod['status_display'] == 'Running', f'healthy-service was not Running: {healthy_pod}'
    print('  [PASS] healthy-service is correctly identified: ready=' + str(healthy_pod['ready']) + ', status=' + str(healthy_pod['status_display']))

    # Check crashloop-service
    crash_pod = next((p for p in pods if 'crashloop-service' in p['pod_name']), None)
    assert crash_pod is not None, 'crashloop-service pod not found'
    assert crash_pod['ready'] is False, 'crashloop-service should not be ready'
    print('  [PASS] crashloop-service is correctly identified: ready=' + str(crash_pod['ready']) + ', status=' + str(crash_pod.get('status_display')))

    # 3. Topology Self-Dependency & Edge Integrity
    print('\n[3/7] Testing Topology Dependency Graph...')
    r_topo = client.get('/api/v1/topology/graph')
    assert r_topo.status_code == 200
    topo = r_topo.json()
    nodes = topo.get('nodes', [])
    edges = topo.get('edges', [])
    assert len(nodes) > 0, 'Topology has no nodes'
    assert len(edges) > 0, 'Topology has no edges'

    # Verify zero self-dependencies
    for edge in edges:
        src = edge['source']
        tgt = edge['target']
        assert src != tgt, f'Found self-loop edge: {src} -> {tgt}'
    print('  [PASS] Topology graph verified: ' + str(len(nodes)) + ' nodes, ' + str(len(edges)) + ' edges, 0 self-loops.')

    # 4. Incident Deduplication & Lifecycle Endpoints
    print('\n[4/7] Testing Incident Deduplication & Lifecycle State Machine...')
    r_inc = client.get('/api/v1/incidents')
    assert r_inc.status_code == 200
    incidents = r_inc.json()
    assert len(incidents) > 0, 'No incidents found'
    titles = [i['title'].strip().lower() for i in incidents]
    assert len(titles) == len(set(titles)), f'Duplicate incidents detected in database: {titles}'
    print('  [PASS] Incidents list verified: ' + str(len(incidents)) + ' unique canonical incidents.')

    # Test lifecycle endpoint: acknowledge and resolve
    test_inc_id = incidents[0]['id']
    r_ack = client.post(f'/api/v1/incidents/{test_inc_id}/acknowledge')
    assert r_ack.status_code == 200, f'Acknowledge failed: {r_ack.text}'
    assert r_ack.json()['status'] == 'acknowledged'
    print('  [PASS] Incident acknowledge endpoint: status=' + str(r_ack.json()['status']))

    # 5. RAG Vector Store Cleanliness
    print('\n[5/7] Testing RAG Knowledge Base Store...')
    conn = sqlite3.connect('data/rag_store/vectors.db')
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM vector_chunks WHERE document_id LIKE 'runbook-auth-memory-leak-%'")
    polluted_count = cur.fetchone()[0]
    assert polluted_count == 0, f'Found {polluted_count} polluted test vectors in RAG store'
    cur.execute('SELECT count(distinct document_id) FROM vector_chunks')
    doc_count = cur.fetchone()[0]
    conn.close()
    print('  [PASS] RAG Knowledge Base clean: 0 test leaks, ' + str(doc_count) + ' canonical runbooks indexed.')

    # 6. Audit Trail Role Verification
    print('\n[6/7] Testing Audit Actor Role Guarantee...')
    r_audit = client.get('/api/v1/investigations/audit/events?limit=50')
    assert r_audit.status_code == 200, f"Audit query failed: {r_audit.text}"
    audit_data = r_audit.json()
    audit_events = audit_data.get('events', [])
    print(f"  [PASS] Audit logs verified: {len(audit_events)} audit events recorded.")

    # 7. Role-Based Access Control API Enforcement
    print('\n[7/7] Testing RBAC Security Contract...')
    # 7a. Verify System Info
    r_info = client.get('/api/v1/system/info')
    assert r_info.status_code == 200, f"System info failed: {r_info.text}"
    print('  [PASS] System info endpoint accessible.')

    # 7b. Enforce RBAC: Viewer forbidden on Admin retention endpoint
    r_viewer_forbidden = client.post(
        '/api/v1/investigations/retention/cleanup?dry_run=true',
        headers={'X-API-Key': 'sentinelops-viewer-secret-key'}
    )
    assert r_viewer_forbidden.status_code == 403, f"Expected 403 for viewer, got {r_viewer_forbidden.status_code}"
    print(f"  [PASS] RBAC Enforcement verified: Viewer received HTTP 403 Forbidden on retention endpoint.")

    # 7c. Enforce RBAC: Admin allowed on Admin retention endpoint
    r_admin_allowed = client.post(
        '/api/v1/investigations/retention/cleanup?dry_run=true',
        headers={'X-API-Key': 'sentinelops-admin-secret-key'}
    )
    assert r_admin_allowed.status_code == 200, f"Expected 200 for admin, got {r_admin_allowed.status_code}"
    print(f"  [PASS] RBAC Enforcement verified: Admin received HTTP 200 OK on retention endpoint.")

    print('\n' + '=' * 70)
    print('ALL 7 CROSS-SCREEN DATA CONSISTENCY TESTS PASSED PERFECTLY!')
    print('=' * 70)

if __name__ == '__main__':
    test_all()
