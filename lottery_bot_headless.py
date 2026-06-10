#!/usr/bin/env python3
"""
Lao Lottery Video Bot - Headless version for GitHub Actions
ດາວໂຫຼດ MP4 ຈາກ 2 ເວັບ lottery ແລ້ວສົ່ງ Telegram
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
        "caption_template": "ລວມບັນຫາຫວຍ🇻🇳🇱🇦🇹🇭\nວັນທີ່ {date}(ເວລາ{time}ໂມງ)",
    },
    {
        "name": "web2",
        "url": "https://bunha-deang.netlify.app/",
        "caption_template": "ບັນຫາຫວຍ🇱🇦🇻🇳🇹🇭\nປະຈຳງວດ ວັນທີ {date} ( ເວລາ{time})",
    },
]

SAVE_DIR = Path("/tmp/lottery_videos")
SAVE_DIR.mkdir(parents=True, exist_ok=True)


def send_video(path: Path, caption_template: str) -> bool:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    now = datetime.now()
    date_str = now.strftime("%d/%m/%Y")
    time_str = now.strftime("%H:%M")
    full_caption = caption_template.format(date=date_str, time=time_str)
    with open(path, "rb") as f:
        r = requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "caption": full_caption.encode("utf-8"),
            },
            files={"video": (path.name, f, "video/mp4")},
            timeout=120,
        )
    result = r.json()
    if result.get("ok"):
        print(f"  ✅ Telegram OK: {path.name}")
        return True
    else:
        print(f"  ❌ Telegram error: {result}")
        return False


async def download_video(page, web: dict) -> Path | None:
    print(f"\n→ {web['name']}: {web['url']}")

    # Inject visibility override before navigation
    await page.add_init_script("""
        Object.defineProperty(document, 'hidden', { get: () => false });
        Object.defineProperty(document, 'visibilityState', { get: () => 'visible' });
    """)

    await page.goto(web["url"], wait_until="networkidle", timeout=30000)
    await page.wait_for_timeout(2000)

    # ຊອກ Random button
    for sel in ["#btn-random", "button:has-text('Random')", "button:has-text('ສຨ່ມ')"]:
        try:
            loc = page.locator(sel)
            if await loc.count() > 0:
                await loc.first.click()
                print("  ✅ Clicked Random")
                await page.wait_for_timeout(1500)
                break
        except Exception:
            pass

    # ຊອກ video/MP4 button
    btn_video = None
    for sel in ["#btn-video", "button:has-text('MP4')", "button:has-text('ວິດີໂອ')", "button:has-text('Video')"]:
        try:
            loc = page.locator(sel)
            if await loc.count() > 0:
                btn_video = loc.first
                print(f"  ✅ Found video btn: {sel}")
                break
        except Exception:
            pass

    if not btn_video:
        print("  ❌ Video button not found")
        return None

    # ລໍ download
    ts = datetime.now().strftime("%H%M%S")
    save_path = SAVE_DIR / f"lottery_{web['name']}_{ts}.mp4"

    try:
        async with page.expect_download(timeout=60000) as dl:
            await btn_video.click()
            print("  ⏳ Waiting for video render (~6s)...")
        download = await dl.value
        await download.save_as(str(save_path))
        size_kb = save_path.stat().st_size // 1024
        print(f"  ✅ Saved: {save_path.name} ({size_kb} KB)")
        return save_path
    except Exception as e:
        print(f"  ❌ Download error: {e}")
        return None


async def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID env vars")
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
                    send_video(path, web["caption_template"])
                else:
                    errors.append(web["name"])
            except Exception as e:
                print(f"  ❌ {web['name']}: {e}")
                errors.append(web["name"])
            finally:
                await page.close()

        await browser.close()

    if errors:
        print(f"\n⚠ Failed: {errors}")
        sys.exit(1)
    else:
        print("\n✅ All done!")


if __name__ == "__main__":
    asyncio.run(main())
