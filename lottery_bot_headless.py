#!/usr/bin/env python3
"""
Lao Lottery Video Bot - Headless version for GitHub Actions
àºàº²àº§à»àº«àº¼àº MP4 àºàº²àº 2 à»àº§àº±àº lottery à»àº¥à»àº§àºªàº»à»àº Telegram
"""

import asyncio
import os
import sys
import requests
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID   = int(os.environ.get("TELEGRAM_CHAT_ID", "0"))

WEBS = [
    {
        "name": "web1",
        "url": "https://timely-cendol-9b1ed2.netlify.app/",
        "caption": "ð² àº«àº§àºàº¥àº²àº§ àºàº²àº¡àºªàº±àº",
    },
    {
        "name": "web2",
        "url": "https://bunha-deang.netlify.app/",
        "caption": "ð´ àºàº²àº¡àºªàº±àºà»àºàº - àº«àº§àºàº¥àº²àº§",
    },
]

SAVE_DIR = Path("/tmp/lottery_videos")
SAVE_DIR.mkdir(parents=True, exist_ok=True)


def send_video(path: Path, caption: str) -> bool:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    today = datetime.now().strftime("%d/%m/%Y")
    full_caption = f"{caption}\nð àºàº§àºàº§àº±àºàºàºµ {today}"
    with open(path, "rb") as f:
        r = requests.post(
            url,
            data={"chat_id": CHAT_ID, "caption": full_caption},
            files={"video": (path.name, f, "video/mp4")},
            timeout=120,
        )
    result = r.json()
    if result.get("ok"):
        print(f"  â Telegram OK: {path.name}")
        return True
    else:
        print(f"  â Telegram error: {result}")
        return False


async def download_video(page, web: dict) -> Path | None:
    print(f"\nâ {web['name']}: {web['url']}")

    # Inject visibility override before navigation
    await page.add_init_script("""
        Object.defineProperty(document, 'hidden', { get: () => false });
        Object.defineProperty(document, 'visibilityState', { get: () => 'visible' });
    """)

    await page.goto(web["url"], wait_until="networkidle", timeout=30000)
    await page.wait_for_timeout(2000)

    # àºàº­àº Random button
    for sel in ["#btn-random", "button:has-text('Random')", "button:has-text('àºªàº¸à»àº¡')"]:
        try:
            loc = page.locator(sel)
            if await loc.count() > 0:
                await loc.first.click()
                print("  â Clicked Random")
                await page.wait_for_timeout(1500)
                break
        except Exception:
            pass

    # àºàº­àº video/MP4 button
    btn_video = None
    for sel in ["#btn-video", "button:has-text('MP4')", "button:has-text('àº§àº´àºàºµà»àº­')", "button:has-text('Video')"]:
        try:
            loc = page.locator(sel)
            if await loc.count() > 0:
                btn_video = loc.first
                print(f"  â Found video btn: {sel}")
                break
        except Exception:
            pass

    if not btn_video:
        print("  â Video button not found")
        return None

    # àº¥à» download
    ts = datetime.now().strftime("%H%M%S")
    save_path = SAVE_DIR / f"lottery_{web['name']}_{ts}.mp4"

    try:
        async with page.expect_download(timeout=60000) as dl:
            await btn_video.click()
            print("  â³ Waiting for video render (~6s)...")
        download = await dl.value
        await download.save_as(str(save_path))
        size_kb = save_path.stat().st_size // 1024
        print(f"  â Saved: {save_path.name} ({size_kb} KB)")
        return save_path
    except Exception as e:
        print(f"  â Download error: {e}")
        return None


async def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("â Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID env vars")
        sys.exit(1)

    print(f"[{datetime.now().strftime('%H:%M')}] Lao Lottery Bot starting...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--autoplay-policy=no-user-gesture-required",
                "--window-size=1280,800",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            accept_downloads=True,
        )

        errors = []
        for web in WEBS:
            page = await context.new_page()
            try:
                path = await download_video(page, web)
                if path:
                    send_video(path, web["caption"])
                else:
                    errors.append(web["name"])
            except Exception as e:
                print(f"  â {web['name']}: {e}")
                errors.append(web["name"])
            finally:
                await page.close()

        await browser.close()

    if errors:
        print(f"\nâ  Failed: {errors}")
        sys.exit(1)
    else:
        print("\nâ All done!")


if __name__ == "__main__":
    asyncio.run(main())
