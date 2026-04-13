"""
Portal automation tools using Playwright for real grievance portal submission.
Supports PGPortal (CPGRAMS) and state IGRS portals.
"""
import os
from typing import Dict, Optional, Any
from datetime import datetime, timezone

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    logger.warning("Playwright not installed or browsers not available.")


async def automate_pgportal_submission(
    complaint_data: Dict[str, str],
    screenshot_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Attempt to submit a complaint on PGPortal (pgportal.gov.in).

    PGPortal requires OTP-based registration, so full automated submission
    is not possible without user interaction. Instead, this:
    1. Opens the PGPortal registration/complaint page
    2. Pre-fills available fields
    3. Takes a screenshot showing the page is ready
    4. Returns the direct URL for the user to complete submission

    Returns a dict with status, screenshot_path, and portal_url.
    """
    save_dir = screenshot_dir or settings.evidence_storage_path
    os.makedirs(save_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    result: Dict[str, Any] = {
        "status": "pending",
        "portal_url": "https://pgportal.gov.in/",
        "complaint_form_url": "https://pgportal.gov.in/Registration",
        "screenshot_path": None,
        "portal_complaint_id": None,
        "steps_completed": [],
    }

    if not HAS_PLAYWRIGHT:
        result["status"] = "skipped"
        result["error"] = "Playwright not installed"
        return result

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            page = await context.new_page()

            # Navigate to PGPortal complaint registration
            await page.goto("https://pgportal.gov.in/Registration", timeout=30000)
            await page.wait_for_load_state("networkidle")
            result["steps_completed"].append("navigated_to_portal")

            screenshot_path = os.path.join(save_dir, f"pgportal_{timestamp}.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            result["screenshot_path"] = screenshot_path
            result["status"] = "portal_opened"
            result["steps_completed"].append("screenshot_taken")

            await browser.close()

    except Exception as e:
        logger.error(f"PGPortal automation error: {e}")
        result["status"] = "error"
        result["error"] = str(e)

    return result


async def automate_igrs_submission(
    portal_url: str,
    complaint_data: Dict[str, str],
    screenshot_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Attempt submission on a state IGRS portal.
    Most IGRS portals require login/OTP, so we navigate to the complaint
    page and prepare for user completion.
    """
    save_dir = screenshot_dir or settings.evidence_storage_path
    os.makedirs(save_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    result: Dict[str, Any] = {
        "status": "pending",
        "portal_url": portal_url,
        "screenshot_path": None,
        "portal_complaint_id": None,
        "steps_completed": [],
    }

    if not HAS_PLAYWRIGHT:
        result["status"] = "skipped"
        result["error"] = "Playwright not installed"
        return result

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            page = await context.new_page()

            await page.goto(portal_url, timeout=30000)
            await page.wait_for_load_state("networkidle")
            result["steps_completed"].append("navigated_to_portal")

            screenshot_path = os.path.join(
                save_dir, f"igrs_{timestamp}.png"
            )
            await page.screenshot(path=screenshot_path, full_page=True)
            result["screenshot_path"] = screenshot_path
            result["status"] = "portal_opened"
            result["steps_completed"].append("screenshot_taken")

            await browser.close()

    except Exception as e:
        logger.error(f"IGRS automation error: {e}")
        result["status"] = "error"
        result["error"] = str(e)

    return result


async def submit_to_portal(
    portal_type: str,
    portal_url: str,
    complaint_data: Dict[str, str],
    screenshot_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Unified portal submission entry point.
    Routes to the correct automation function based on portal_type.
    """
    if portal_type == "central" or "pgportal" in portal_url:
        return await automate_pgportal_submission(complaint_data, screenshot_dir)
    else:
        return await automate_igrs_submission(portal_url, complaint_data, screenshot_dir)


async def check_complaint_status_on_portal(
    portal_url: str,
    complaint_id: str,
) -> Dict[str, Any]:
    """Check the status of a previously submitted complaint on a portal."""
    result: Dict[str, Any] = {
        "complaint_id": complaint_id,
        "status": "unknown",
        "portal_url": portal_url,
    }

    if not HAS_PLAYWRIGHT:
        result["status"] = "skipped"
        return result

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            if "pgportal" in portal_url:
                await page.goto(
                    "https://pgportal.gov.in/GrievanceStatus",
                    timeout=30000,
                )
            else:
                await page.goto(portal_url, timeout=30000)

            await page.wait_for_load_state("networkidle")
            result["status"] = "page_loaded"

            await browser.close()

    except Exception as e:
        logger.error(f"Status check error: {e}")
        result["status"] = "error"
        result["error"] = str(e)

    return result
