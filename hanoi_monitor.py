#!/usr/bin/env python3
"""
Hanoi Lottery Monitor
ຕິດຕາມຜົນຫວຍຮານວຍ 5 ຮອບ ຈາກ viet5.xsmbac.live
ສົ່ງ: ຂໍ້ຄວາມ + ຮູບ screenshot + video MP4 ໄປ Telegram
ເຮັດວຽກ: 14:10 - 21:00 (UTC+7) ເທົ່ານັ້ນ
"""

import asyncio
import os
import sys
import json
import requests
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta
from playwright.async_api import async_playwright

# ─── Config ──────────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID   = int(os.environ.get("TELEGRAM_CHAT_ID", "0"))

WEB_URL      = "https://viet5.xsmbac.live/"
STATE_FILE   = Path("/tmp/hanoi_sent_state.json")
MONITOR_INTERVAL = 5   # ວິນາທີ

# UTC+7
TZ_LAO = timezone(timedelta(hours=7))

# ຊ່ວງເວລາທີ່ bot ເຮັດວຽກ (ເວລາລາວ)
WORK_START = (14, 10)   # 14:10
WORK_END   = (21, 0)    # 21:00

# 5 ຮອບ: (ຊື່, ໂມງ, ນາທີ)
ROUNDS = [
    {"id": "r1", "name": "ຮອບ 1", "hour": 15, "minute": 30, "tab_index": 0},
    {"id": "r2", "name": "ຮອບ 2", "hour": 16, "minute": 30, "tab_index": 1},
    {"id": "r3", "name": "ຮອບ 3", "hour": 17, "minute": 30, "tab_index": 2},
    {"id": "r4", "name": "ຮອບ 4", "hour": 18, "minute": 30, "tab_index": 3},
    {"id": "r5", "name": "ຮອບ 5", "hour": 19, "minute": 30, "tab_index": 4},
]

SUMMARY_TABS = [
    {"id": "summary",      "name": "ສຫຼຸບ 5 ຮອບ",     "tab_text": "ສະຫຼຸບ"},
    {"id": "summary_laothai", "name": "ສຫຼຸບ ລາວ+ໄທ", "tab_text": "ສະຫຼຸບ ລາວ ແລະ ໄທ"},
]
