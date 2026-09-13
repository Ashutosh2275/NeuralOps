# SentinelOps AI - Role-Based Access Control Browser Test
import asyncio, pathlib, sys
from playwright.async_api import async_playwright

BASE_URL = 'http://localhost:5173'
SCREENSHOT_DIR = pathlib.Path('data/screenshots')
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

async def test_rbac_matrix():
    print("=" * 60)
    print("SENTINELOPS AI - ROLE-BASED ACCESS CONTROL PLAYWRIGHT TEST")
    print("=" * 60)
    artifact_dir = pathlib.Path(r"C:/Users/ASUS/.gemini/antigravity/brain/1657116c-2c21-4618-ae91-2b9e9572c726/screenshots")
    artifact_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        # ----------------------------------------------------
        # TEST 1: VIEWER ROLE
        # ----------------------------------------------------
        print("\n[TEST 1] Testing VIEWER role...")
        await page.goto(f"{BASE_URL}/", wait_until="networkidle")
        await page.wait_for_timeout(1000)

        role_select = page.locator('[data-testid="role-selector"]')
        await role_select.wait_for(state="visible")
        await role_select.select_option("viewer")
        await page.wait_for_timeout(800)

        selected_val = await role_select.input_value()
        assert selected_val == "viewer", f"Expected viewer, got {selected_val}"
        print("  [OK] Viewer role selected in UI dropdown")

        # Navigate to Investigations
        await page.goto(f"{BASE_URL}/investigations", wait_until="networkidle")
        await page.wait_for_timeout(800)
        launch_btn = page.locator('[data-testid="launch-investigation-btn"]')
        await launch_btn.wait_for(state="visible")
        assert await launch_btn.is_disabled(), "Launch button must be disabled for viewer"
        print("  [OK] Investigations: Launch Investigation button is disabled for VIEWER")

        # Navigate to Tools
        await page.goto(f"{BASE_URL}/tools", wait_until="networkidle")
        await page.wait_for_timeout(800)
        run_btn = page.locator('[data-testid="run-tool-btn"]').first
        await run_btn.wait_for(state="visible")
        assert await run_btn.is_disabled(), "Run Tool button must be disabled for viewer"
        print("  [OK] Tools: Run Tool button is disabled for VIEWER")

        # Navigate to Settings
        await page.goto(f"{BASE_URL}/settings", wait_until="networkidle")
        await page.wait_for_timeout(800)
        retention_btn = page.locator('[data-testid="execute-retention-btn"]')
        await retention_btn.wait_for(state="visible")
        assert await retention_btn.is_disabled(), "Execute Retention button must be disabled for viewer"
        print("  [OK] Settings: Execute Retention button is disabled for VIEWER")

        shot1 = SCREENSHOT_DIR / "role_viewer_enforced.png"
        await page.screenshot(path=str(shot1), full_page=True)
        (artifact_dir / shot1.name).write_bytes(shot1.read_bytes())
        print(f"  [OK] Screenshot captured: {shot1}")

        # ----------------------------------------------------
        # TEST 2: OPERATOR ROLE
        # ----------------------------------------------------
        print("\n[TEST 2] Testing OPERATOR role...")
        await page.goto(f"{BASE_URL}/", wait_until="networkidle")
        await page.wait_for_timeout(500)
        role_select = page.locator('[data-testid="role-selector"]')
        await role_select.select_option("operator")
        await page.wait_for_timeout(800)

        selected_val = await role_select.input_value()
        assert selected_val == "operator", f"Expected operator, got {selected_val}"
        print("  [OK] Operator role selected in UI dropdown")

        await page.goto(f"{BASE_URL}/investigations", wait_until="networkidle")
        await page.wait_for_timeout(800)
        launch_btn = page.locator('[data-testid="launch-investigation-btn"]')
        await launch_btn.wait_for(state="visible")
        assert not await launch_btn.is_disabled(), "Launch button must be enabled for operator"
        print("  [OK] Investigations: Launch Investigation button is ENABLED for OPERATOR")

        await page.goto(f"{BASE_URL}/tools", wait_until="networkidle")
        await page.wait_for_timeout(800)
        run_btn = page.locator('[data-testid="run-tool-btn"]').first
        await run_btn.wait_for(state="visible")
        assert not await run_btn.is_disabled(), "Run Tool button must be enabled for operator"
        print("  [OK] Tools: Run Tool button is ENABLED for OPERATOR")

        await page.goto(f"{BASE_URL}/settings", wait_until="networkidle")
        await page.wait_for_timeout(800)
        retention_btn = page.locator('[data-testid="execute-retention-btn"]')
        await retention_btn.wait_for(state="visible")
        assert await retention_btn.is_disabled(), "Execute Retention button must be disabled for operator"
        print("  [OK] Settings: Execute Retention button is restricted from OPERATOR")

        shot2 = SCREENSHOT_DIR / "role_operator_enforced.png"
        await page.screenshot(path=str(shot2), full_page=True)
        (artifact_dir / shot2.name).write_bytes(shot2.read_bytes())
        print(f"  [OK] Screenshot captured: {shot2}")

        # ----------------------------------------------------
        # TEST 3: ADMIN ROLE
        # ----------------------------------------------------
        print("\n[TEST 3] Testing ADMIN role...")
        await page.goto(f"{BASE_URL}/", wait_until="networkidle")
        await page.wait_for_timeout(500)
        role_select = page.locator('[data-testid="role-selector"]')
        await role_select.select_option("admin")
        await page.wait_for_timeout(800)

        selected_val = await role_select.input_value()
        assert selected_val == "admin", f"Expected admin, got {selected_val}"
        print("  [OK] Admin role selected in UI dropdown")

        await page.goto(f"{BASE_URL}/settings", wait_until="networkidle")
        await page.wait_for_timeout(800)
        retention_btn = page.locator('[data-testid="execute-retention-btn"]')
        await retention_btn.wait_for(state="visible")
        assert not await retention_btn.is_disabled(), "Execute Retention button must be enabled for admin"
        print("  [OK] Settings: Execute Retention button is ENABLED for ADMIN")

        print("  [*] Executing Data Retention Policy cleanup (dry run)...")
        await retention_btn.click()
        await page.wait_for_timeout(2000)

        report = page.locator("text=Execution Report (Dry Run: true)")
        await report.wait_for(state="visible", timeout=8000)
        print("  [OK] Retention Policy Report rendered live from backend!")

        shot3 = SCREENSHOT_DIR / "role_admin_retention_executed.png"
        await page.screenshot(path=str(shot3), full_page=True)
        (artifact_dir / shot3.name).write_bytes(shot3.read_bytes())
        print(f"  [OK] Screenshot captured: {shot3}")

        await browser.close()
        print("\n" + "=" * 60)
        print("ALL 3 ROLE-BASED ACCESS CONTROL TESTS PASSED PERFECTLY!")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_rbac_matrix())

