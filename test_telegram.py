import requests
import os
import sys
import io
from dotenv import load_dotenv

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

load_dotenv()

TG_TOKEN = os.environ.get("TG_TOKEN", "").strip()
TG_CHAT  = os.environ.get("TG_CHAT", "").strip()

print(f"TG_TOKEN : {TG_TOKEN[:10]}...{TG_TOKEN[-5:] if len(TG_TOKEN) > 15 else '(short?)'}")
print(f"TG_CHAT  : {TG_CHAT}")

if not TG_TOKEN or not TG_CHAT:
    print("ERROR: TG_TOKEN or TG_CHAT is missing in .env")
    sys.exit(1)

print("\nSending test message to Telegram...")

try:
    resp = requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        data={
            "chat_id":    TG_CHAT,
            "text":       "✅ Divi Monitor — Telegram connection test successful!",
            "parse_mode": "HTML",
        },
        timeout=15,
    )
    print(f"HTTP Status : {resp.status_code}")
    print(f"Response    : {resp.text}")
    if resp.status_code == 200:
        print("\n✅ SUCCESS — Telegram is working correctly!")
    else:
        print("\n❌ FAILED — Check token and chat ID above.")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("Possible reasons:")
    print("  1. Wrong TG_TOKEN in .env")
    print("  2. Wrong TG_CHAT in .env")
    print("  3. Bot was never started (send /start to your bot first)")
    print("  4. Network/firewall blocking api.telegram.org")
