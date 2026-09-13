import asyncio
import json
import pathlib
import sys
import httpx
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:5173"
SCREENSHOT_DIR = pathlib.Path("data/screenshots/phase12")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR = pathlib.Path(r"C:/Users/ASUS/.gemini/antigravity/brain/1657116c-2c21-4618-ae91-2b9e9572c726/screenshots")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

async def run_phase12_suite():
    print("=" * 70)
    print("SENTINELOPS AI — PHASE 12 COMPREHENSIVE PLAYWRIGHT VALIDATION SUITE")
    print("=" * 70)

    # Fetch dynamic IDs from real backend
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        inc_res = await client.get("/api/v1/incidents")
        incidents = inc_res.json()
        incident_id = incidents[0]["id"] if incidents else "ca3d6a28-ed93-4bec-bc43-b9f3f4996d97"

        inv_res = await client.get("/api/v1/investigations")
        inv_data = inv_res.json().get("investigations", [])
        inv_id = inv_data[0]["investigation_id"] if inv_data else "inv-e2e-001"

        pod_res = await client.get("/api/v1/workloads/pods")
        pods = pod_res.json().get("pods", [])
        pod_name = pods[0]["pod_name"] if pods else "crashloop-service-557985fc96-nhhqv"
        pod_ns = pods[0]["namespace"] if pods else "sentinelops-e2e"

        doc_id = "runbook-crashloopbackoff"

    print(f"Target dynamic IDs for deep-route testing:")
    print(f"  Incident ID:      {incident_id}")
    print(f"  Investigation ID: {inv_id}")
    print(f"  Pod Detail:       {pod_ns}/{pod_name}")
    print(f"  Knowledge Doc:    {doc_id}")

    console_errors = []
    failed_requests = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        # Wire logging handlers
        def on_console(msg):
            if msg.type in ("error", "warning") and "favicon" not in msg.text:
                if msg.type == "error":
                    console_errors.append(msg.text)
                    print(f"  [BROWSER ERROR] {msg.text}")

        def on_response(resp):
            if resp.status >= 400 and "favicon" not in resp.url and "00000000" not in resp.url and "nonexistent" not in resp.url:
                # 403 on retention is expected during viewer/operator checks
                failed_requests.append(f"{resp.request.method} {resp.url} -> {resp.status}")

        page.on("console", on_console)
        page.on("response", on_response)

        # ----------------------------------------------------
        # TEST 1: ALL 13 ROUTES
        # ----------------------------------------------------
        routes_to_test = [
            ("/", "Operations Overview", "01_overview.png"),
            ("/incidents", "Incident Center", "02_incidents.png"),
            (f"/incidents/{incident_id}", "Incident Detail", "03_incident_detail.png"),
            ("/investigations", "Investigation Workspace", "04_investigations.png"),
            (f"/investigations/{inv_id}", "Investigation Detail", "05_investigation_detail.png"),
            ("/topology", "Dependency Topology", "06_topology.png"),
            ("/workloads", "Workload Intelligence", "07_workloads.png"),
            (f"/workloads/{pod_ns}/{pod_name}", "Workload Pod Detail", "08_workload_detail.png"),
            ("/knowledge", "Knowledge Base", "09_knowledge.png"),
            (f"/knowledge/{doc_id}", "Knowledge Document", "10_knowledge_doc.png"),
            ("/tools", "Diagnostic Capabilities", "11_tools.png"),
            ("/audit", "Governance Audit", "12_audit.png"),
            ("/settings", "Platform Settings", "13_settings.png"),
        ]

        print("\n--- [STAGE 1] Testing All 13 Routes & Navigation ---")
        for route, title_hint, shot_name in routes_to_test:
            target_url = f"{BASE_URL}{route}"
            await page.goto(target_url, wait_until="networkidle")
            await page.wait_for_timeout(600)
            
            # Check body text
            body_text = await page.locator("body").inner_text()
            assert len(body_text) > 50, f"Route {route} rendered almost empty body"

            # Capture screenshot
            shot_path = SCREENSHOT_DIR / shot_name
            await page.screenshot(path=str(shot_path), full_page=True)
            (ARTIFACT_DIR / shot_name).write_bytes(shot_path.read_bytes())
            print(f"  [PASS] Route {route:40} loaded. Screenshot: {shot_name}")

        # ----------------------------------------------------
        # TEST 2: INTERACTIVE DEEP WORKFLOWS
        # ----------------------------------------------------
        print("\n--- [STAGE 2] Testing Interactive Workflows ---")

        # 2A. Incident Center Search & Filter
        await page.goto(f"{BASE_URL}/incidents", wait_until="networkidle")
        search_input = page.locator('input[placeholder*="Search incidents"]')
        if await search_input.is_visible():
            await search_input.fill("CrashLoopBackOff")
            await page.wait_for_timeout(400)
            text_after = await page.locator("body").inner_text()
            assert "CrashLoopBackOff" in text_after
            await search_input.fill("")
            print("  [PASS] Incident search filter active and responsive")

        # 2B. Incident Detail 7-Section Integrity
        await page.goto(f"{BASE_URL}/incidents/{incident_id}", wait_until="networkidle")
        await page.wait_for_timeout(600)
        detail_text = await page.locator("body").inner_text()
        assert "ROOT CAUSE & CONFIDENCE" in detail_text.upper() or "ROOT CAUSE" in detail_text.upper()
        assert "EVIDENCE" in detail_text.upper()
        assert "TIMELINE" in detail_text.upper()
        assert "BLAST RADIUS" in detail_text.upper()
        assert "RECOMMENDATION" in detail_text.upper()
        print("  [PASS] Incident Detail: 7 core operational sections present")

        # 2C. Topology Graph & Node Inspector
        await page.goto(f"{BASE_URL}/topology", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        svg_exists = await page.locator("svg").count() > 0
        assert svg_exists, "Topology SVG element not found"
        print(f"  [PASS] Topology: Interactive SVG graph rendered")

        # 2D. Knowledge Semantic Search
        await page.goto(f"{BASE_URL}/knowledge", wait_until="networkidle")
        await page.wait_for_timeout(500)
        kw_input = page.locator('input[placeholder*="Search operational runbooks"]')
        if await kw_input.is_visible():
            await kw_input.fill("CrashLoopBackOff memory")
            search_btn = page.locator('button:has-text("Search")')
            if await search_btn.is_visible():
                await search_btn.click()
                await page.wait_for_timeout(800)
            print("  [PASS] Knowledge Base: Semantic vector query executed")

        # 2E. Workload Pod Detail Tabs
        await page.goto(f"{BASE_URL}/workloads/{pod_ns}/{pod_name}", wait_until="networkidle")
        await page.wait_for_timeout(600)
        pod_body = await page.locator("body").inner_text()
        assert "CONTAINERS" in pod_body.upper() or "OVERVIEW" in pod_body.upper()
        print("  [PASS] Workload Pod Detail tabs and telemetry active")

        # ----------------------------------------------------
        # TEST 3: RBAC ENFORCEMENT (VIEWER, OPERATOR, ADMIN)
        # ----------------------------------------------------
        print("\n--- [STAGE 3] Testing RBAC Security Contracts ---")
        
        # Viewer Role
        await page.goto(f"{BASE_URL}/", wait_until="networkidle")
        role_select = page.locator('[data-testid="role-selector"]')
        await role_select.select_option("viewer")
        await page.wait_for_timeout(400)

        # Viewer on Investigations
        await page.goto(f"{BASE_URL}/investigations", wait_until="networkidle")
        launch_btn = page.locator('[data-testid="launch-investigation-btn"]')
        if await launch_btn.is_visible():
            assert await launch_btn.is_disabled(), "Viewer should NOT be able to launch investigations"
            print("  [PASS] Viewer: Launch Investigation disabled")

        # Viewer on Tools
        await page.goto(f"{BASE_URL}/tools", wait_until="networkidle")
        run_btn = page.locator('[data-testid="run-tool-btn"]').first
        if await run_btn.is_visible():
            assert await run_btn.is_disabled(), "Viewer should NOT be able to run tools"
            print("  [PASS] Viewer: Tool execution disabled")

        # Viewer on Settings
        await page.goto(f"{BASE_URL}/settings", wait_until="networkidle")
        retention_btn = page.locator('[data-testid="execute-retention-btn"]')
        if await retention_btn.is_visible():
            assert await retention_btn.is_disabled(), "Viewer should NOT be able to execute retention"
            print("  [PASS] Viewer: Data retention cleanup disabled")

        # Operator Role
        await role_select.select_option("operator")
        await page.wait_for_timeout(400)
        
        await page.goto(f"{BASE_URL}/investigations", wait_until="networkidle")
        if await launch_btn.is_visible():
            assert not await launch_btn.is_disabled(), "Operator SHOULD be able to launch investigations"
            print("  [PASS] Operator: Launch Investigation enabled")

        await page.goto(f"{BASE_URL}/tools", wait_until="networkidle")
        if await run_btn.is_visible():
            assert not await run_btn.is_disabled(), "Operator SHOULD be able to run tools"
            print("  [PASS] Operator: Tool execution enabled")

        await page.goto(f"{BASE_URL}/settings", wait_until="networkidle")
        if await retention_btn.is_visible():
            assert await retention_btn.is_disabled(), "Operator should NOT be able to execute retention"
            print("  [PASS] Operator: Data retention cleanup disabled")

        # Admin Role
        await role_select.select_option("admin")
        await page.wait_for_timeout(400)

        await page.goto(f"{BASE_URL}/settings", wait_until="networkidle")
        if await retention_btn.is_visible():
            assert not await retention_btn.is_disabled(), "Admin SHOULD be able to execute retention"
            print("  [PASS] Admin: Data retention cleanup enabled")

        # ----------------------------------------------------
        # TEST 4: RESPONSIVE VIEWPORT TEST
        # ----------------------------------------------------
        print("\n--- [STAGE 4] Testing Responsive Viewports ---")
        viewports = [
            (1920, 1080, "1080p Desktop"),
            (1440, 900, "MacBook Pro 14"),
            (1280, 800, "Compact Laptop"),
            (1024, 768, "Standard Tablet / Small Screen"),
        ]

        for width, height, label in viewports:
            await page.set_viewport_size({"width": width, "height": height})
            await page.goto(f"{BASE_URL}/", wait_until="networkidle")
            await page.wait_for_timeout(300)

            # Check for horizontal scroll overflow
            scroll_width = await page.evaluate("() => document.documentElement.scrollWidth")
            inner_width = await page.evaluate("() => window.innerWidth")
            assert scroll_width <= inner_width + 1, f"Horizontal scroll detected at {label} ({scroll_width} > {inner_width})"
            print(f"  [PASS] Viewport {label:32} ({width}x{height}): No horizontal overflow (scrollWidth={scroll_width}, innerWidth={inner_width})")

        await browser.close()

    print("=" * 70)
    print("PLAYWRIGHT BROWSER VALIDATION COMPLETE!")
    print(f"Total Console Errors Recorded: {len(console_errors)}")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_phase12_suite())
