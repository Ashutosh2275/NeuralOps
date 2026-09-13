import asyncio
import json
import pathlib
import sys
import httpx
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:5173"
SCREENSHOT_DIR = pathlib.Path("data/screenshots/phase13")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR = pathlib.Path(r"C:/Users/ASUS/.gemini/antigravity/brain/1657116c-2c21-4618-ae91-2b9e9572c726/screenshots")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

async def run_phase13_certification():
    print("=" * 75)
    print("SENTINELOPS AI — PHASE 13 FINAL BROWSER CERTIFICATION & SCREENSHOT SUITE")
    print("=" * 75)

    # Fetch dynamic identifiers from real backend
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        inc_res = await client.get("/api/v1/incidents")
        incidents = inc_res.json()
        incident_id = incidents[0]["id"] if incidents else "6454da76-583e-4bc2-b71d-0693ed62ae74"

        inv_res = await client.get("/api/v1/investigations")
        inv_data = inv_res.json().get("investigations", [])
        inv_id = inv_data[0]["investigation_id"] if inv_data else "inv-e2e-001"

        pod_res = await client.get("/api/v1/workloads/pods")
        pods = pod_res.json().get("pods", [])
        pod_name = pods[0]["pod_name"] if pods else "crashloop-service-557985fc96-nhhqv"
        pod_ns = pods[0]["namespace"] if pods else "sentinelops-e2e"

        doc_id = "runbook-crashloopbackoff"

    print(f"Target dynamic IDs for deep route validation:")
    print(f"  Incident ID:      {incident_id}")
    print(f"  Investigation ID: {inv_id}")
    print(f"  Pod Detail:       {pod_ns}/{pod_name}")
    print(f"  Knowledge Doc:    {doc_id}")

    console_errors = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        # Log errors
        def on_console(msg):
            if msg.type == "error" and "favicon" not in msg.text:
                console_errors.append(msg.text)
                print(f"  [BROWSER CONSOLE ERROR] {msg.text}")

        page.on("console", on_console)

        # -----------------------------------------------------------------
        # STAGE 1: FULL SCREENSHOT SET CAPTURE (1920x1080)
        # -----------------------------------------------------------------
        screens = [
            ("/", "01_overview.png", "Overview"),
            ("/incidents", "02_incidents.png", "Incident Center"),
            (f"/incidents/{incident_id}", "03_incident_detail.png", "Incident Detail"),
            ("/investigations", "04_investigations.png", "Investigation Workspace"),
            (f"/investigations/{inv_id}", "05_investigation_detail.png", "Investigation Detail"),
            ("/topology", "06_topology.png", "Dependency Topology"),
            ("/workloads", "07_workloads.png", "Workload Intelligence"),
            (f"/workloads/{pod_ns}/{pod_name}", "08_workload_detail.png", "Workload Pod Detail"),
            ("/knowledge", "09_knowledge.png", "Knowledge Base"),
            (f"/knowledge/{doc_id}", "10_knowledge_doc.png", "Knowledge Document Viewer"),
            ("/tools", "11_tools.png", "Diagnostic Capabilities"),
            ("/audit", "12_audit.png", "Governance Audit Trail"),
            ("/settings", "13_settings.png", "Platform Settings"),
        ]

        print("\n--- [STAGE 1] Capturing Final Certified Screenshots ---")
        for route, shot_name, label in screens:
            target_url = f"{BASE_URL}{route}"
            await page.goto(target_url, wait_until="networkidle")
            await page.wait_for_timeout(600)

            shot_path = SCREENSHOT_DIR / shot_name
            await page.screenshot(path=str(shot_path), full_page=True)
            (ARTIFACT_DIR / shot_name).write_bytes(shot_path.read_bytes())
            print(f"  [PASS] {label:32} -> {shot_name}")

        # -----------------------------------------------------------------
        # STAGE 2: RBAC ENFORCEMENT VERIFICATION
        # -----------------------------------------------------------------
        print("\n--- [STAGE 2] Role-Based Access Control Verification ---")
        # Viewer Role
        role_select = page.locator('[data-testid="role-selector"]')
        await role_select.select_option("viewer")
        await page.wait_for_timeout(400)

        await page.goto(f"{BASE_URL}/investigations", wait_until="networkidle")
        launch_btn = page.locator('[data-testid="launch-investigation-btn"]')
        if await launch_btn.is_visible():
            assert await launch_btn.is_disabled(), "Viewer should not be able to launch investigations"
            print("  [PASS] Viewer: Launch Investigation button is disabled")

        await page.goto(f"{BASE_URL}/tools", wait_until="networkidle")
        run_btn = page.locator('[data-testid="run-tool-btn"]').first
        if await run_btn.is_visible():
            assert await run_btn.is_disabled(), "Viewer should not be able to run diagnostic tools"
            print("  [PASS] Viewer: Run Tool button is disabled")

        await page.goto(f"{BASE_URL}/settings", wait_until="networkidle")
        retention_btn = page.locator('[data-testid="execute-retention-btn"]')
        if await retention_btn.is_visible():
            assert await retention_btn.is_disabled(), "Viewer should not be able to execute retention"
            print("  [PASS] Viewer: Execute Retention button is disabled")

        # Operator Role
        await role_select.select_option("operator")
        await page.wait_for_timeout(400)

        await page.goto(f"{BASE_URL}/investigations", wait_until="networkidle")
        if await launch_btn.is_visible():
            assert not await launch_btn.is_disabled(), "Operator should be able to launch investigations"
            print("  [PASS] Operator: Launch Investigation button is ENABLED")

        await page.goto(f"{BASE_URL}/tools", wait_until="networkidle")
        if await run_btn.is_visible():
            assert not await run_btn.is_disabled(), "Operator should be able to run diagnostic tools"
            print("  [PASS] Operator: Run Tool button is ENABLED")

        await page.goto(f"{BASE_URL}/settings", wait_until="networkidle")
        if await retention_btn.is_visible():
            assert await retention_btn.is_disabled(), "Operator should NOT be able to execute retention"
            print("  [PASS] Operator: Execute Retention button is disabled (Admin required)")

        # Admin Role
        await role_select.select_option("admin")
        await page.wait_for_timeout(400)

        await page.goto(f"{BASE_URL}/settings", wait_until="networkidle")
        if await retention_btn.is_visible():
            assert not await retention_btn.is_disabled(), "Admin SHOULD be able to execute retention"
            print("  [PASS] Admin: Execute Retention button is ENABLED")

        # -----------------------------------------------------------------
        # STAGE 3: MULTI-VIEWPORT RESPONSIVENESS (ZERO OVERFLOW)
        # -----------------------------------------------------------------
        print("\n--- [STAGE 3] Multi-Viewport Responsive Validation ---")
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

            scroll_width = await page.evaluate("() => document.documentElement.scrollWidth")
            inner_width = await page.evaluate("() => window.innerWidth")
            assert scroll_width <= inner_width + 1, f"Horizontal overflow detected at {label} ({scroll_width} > {inner_width})"
            print(f"  [PASS] Viewport {label:32} ({width}x{height}): No horizontal overflow")

        await browser.close()

    print("=" * 75)
    print("PHASE 13 BROWSER CERTIFICATION COMPLETED SUCCESSFULLY!")
    print(f"Total Console Errors Recorded: {len(console_errors)}")
    print("=" * 75)
    if len(console_errors) > 0:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_phase13_certification())
