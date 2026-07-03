#!/usr/bin/env python3
"""Log into MySSCguide admin, screenshot /admin/users, and send to Telegram."""

import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

IST = ZoneInfo("Asia/Kolkata")

ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

LOGIN_URL = "https://www.mysscguide.com/login"
ADMIN_USERS_URL = "https://www.mysscguide.com/admin/users"
SCREENSHOT_DIR = Path(__file__).parent / "screenshots"


def send_telegram_photo(photo_path: Path, caption: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    with photo_path.open("rb") as photo:
        response = requests.post(
            url,
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
            files={"photo": photo},
            timeout=60,
        )
    response.raise_for_status()


def send_telegram_message(text: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    response = requests.post(
        url,
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
        timeout=30,
    )
    response.raise_for_status()


def take_admin_snapshot() -> Path:
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now(IST).strftime("%Y-%m-%d_%H-%M-%S")
    screenshot_path = SCREENSHOT_DIR / f"admin_users_{timestamp}.png"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        page.goto(ADMIN_USERS_URL, wait_until="networkidle", timeout=60_000)
        page.wait_for_selector("#email", timeout=30_000)

        page.fill("#email", ADMIN_EMAIL)
        page.fill("#password", ADMIN_PASSWORD)
        page.click('button[type="submit"]')

        page.wait_for_url("**/admin/users**", timeout=30_000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        page.evaluate("window.scrollBy(0, 1500)")
        page.wait_for_timeout(800)

        page.screenshot(path=str(screenshot_path), full_page=False)
        browser.close()

    return screenshot_path


def main() -> int:
    try:
        screenshot = take_admin_snapshot()
        now = datetime.now(IST)
        caption = f"MySSCguide admin users — {now.strftime('%d %b %Y, %I:%M %p')} IST"
        send_telegram_photo(screenshot, caption)
        print(f"Screenshot sent: {screenshot}")
        return 0
    except Exception as exc:
        error_msg = f"MySSCguide snapshot failed: {exc}"
        print(error_msg, file=sys.stderr)
        try:
            send_telegram_message(error_msg)
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
