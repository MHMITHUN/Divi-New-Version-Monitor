import feedparser
import requests
import os
import sys
import time
import re
import json
import html
import io
from datetime import datetime, timezone
from dotenv import load_dotenv

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

load_dotenv()

RSS_SOURCES = [
    "https://www.divichangelog.com/feed",
    "https://www.divichangelog.com/feed/",
    "https://www.elegantthemes.com/blog/feed",
]

LATEST_FILE = "latest.txt"
MAX_RETRIES = 3
RETRY_DELAY = 5

TG_TOKEN    = os.environ.get("TG_TOKEN", "").strip()
TG_CHAT     = os.environ.get("TG_CHAT", "").strip()
SLACK_HOOK  = os.environ.get("SLACK_WEBHOOK", "").strip()
RSS_URL     = os.environ.get("RSS_URL", RSS_SOURCES[0]).strip()

def log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{ts}] {msg}")

def clean_html(raw: str) -> str:
    raw = html.unescape(raw or "")
    raw = re.sub(r"<br\s*/?>", "\n", raw, flags=re.IGNORECASE)
    raw = re.sub(r"<[^>]+>", "", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    return raw.strip()

def extract_changelog_lines(content: str, max_items: int = 8) -> list[str]:
    text = clean_html(content)
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("–") or line.startswith("-"):
            clean = line.lstrip("–- ").strip()
            if clean and len(clean) > 10:
                lines.append(clean)
        if len(lines) >= max_items:
            break
    return lines

def read_latest() -> str:
    if not os.path.exists(LATEST_FILE):
        return ""
    try:
        with open(LATEST_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""

def write_latest(version: str):
    try:
        with open(LATEST_FILE, "w", encoding="utf-8") as f:
            f.write(version)
        log(f"✅ latest.txt updated → {version}")
    except Exception as e:
        log(f"⚠️  Could not write latest.txt: {e}")

def fetch_rss() -> tuple[str, str, str, str]:
    sources = [RSS_URL] + [s for s in RSS_SOURCES if s != RSS_URL]

    for source_url in sources:
        log(f"🔍 Trying RSS source: {source_url}")
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                feed = feedparser.parse(source_url)
                status = getattr(feed, "status", 200)
                if status and status >= 400:
                    log(f"   ⚠️  HTTP {status} from {source_url}")
                    raise ValueError(f"HTTP {status}")

                if not feed.entries:
                    log(f"   ⚠️  Feed returned 0 entries (attempt {attempt})")
                    if attempt < MAX_RETRIES:
                        time.sleep(RETRY_DELAY * attempt)
                        continue
                    break

                entry   = feed.entries[0]
                title   = (entry.get("title") or "").strip()
                link    = (entry.get("link") or "").strip()
                pub_raw = entry.get("published") or entry.get("updated") or ""
                content = ""

                if entry.get("content"):
                    content = entry["content"][0].get("value", "")
                elif entry.get("summary"):
                    content = entry["summary"]

                if not title:
                    log("   ⚠️  Entry has no title")
                    break

                log(f"   ✅ Got entry: {title}")
                return title, link, pub_raw, content

            except Exception as e:
                log(f"   ❌ Attempt {attempt}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * attempt)

    raise RuntimeError("All RSS sources exhausted — no valid entries found.")

def send_telegram(title: str, link: str, pub_date: str, changelog: list[str]):
    if not TG_TOKEN or not TG_CHAT:
        log("⚠️  Telegram credentials not set — skipping")
        return False

    items_text = ""
    if changelog:
        items = "\n".join(f"  • {c[:120]}" for c in changelog[:8])
        items_text = f"\n\n<b>📋 Highlights:</b>\n{items}"
        if len(changelog) > 8:
            items_text += f"\n  <i>...and {len(changelog) - 8} more fixes</i>"

    nice_date = pub_date
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(pub_date)
        nice_date = dt.strftime("%d %b %Y, %H:%M UTC")
    except Exception:
        pass

    message = (
        f"🚀 <b>New Divi Update Released!</b>\n"
        f"{'─' * 30}\n"
        f"📦 <b>Version:</b> {html.escape(title)}\n"
        f"📅 <b>Released:</b> {nice_date}"
        f"{items_text}\n\n"
        f"🔗 <a href=\"{link}\">Read Full Changelog</a>\n"
        f"{'─' * 30}\n"
        f"<i>⚡ Monitored by Divi Update Watcher</i>"
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                data={
                    "chat_id":    TG_CHAT,
                    "text":       message,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": False,
                },
                timeout=20,
            )
            resp.raise_for_status()
            log(f"✅ Telegram sent (attempt {attempt})")
            return True
        except Exception as e:
            log(f"❌ Telegram attempt {attempt}/{MAX_RETRIES}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

    log("❌ Telegram: all retries failed")
    return False

def send_slack(title: str, link: str, pub_date: str, changelog: list[str], is_new: bool = True):
    if not SLACK_HOOK:
        log("⚠️  Slack webhook not set — skipping")
        return False

    nice_date = pub_date
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(pub_date)
        nice_date = dt.strftime("%d %b %Y, %H:%M UTC")
    except Exception:
        pass

    if is_new:
        header_text  = f"🚀 New Divi Update: {title}"
        status_emoji = "🎉"
        status_text  = f"*{title}* was just released!"
    else:
        header_text  = f"✅ Divi Monitor: No new update ({title})"
        status_emoji = "🔍"
        status_text  = f"Latest version is still *{title}* — no changes."

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": header_text, "emoji": True}
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{status_emoji} {status_text}\n📅 *Released:* {nice_date}"
            }
        },
    ]

    if is_new and changelog:
        items = "\n".join(f"• {c[:120]}" for c in changelog[:6])
        if len(changelog) > 6:
            items += f"\n_...and {len(changelog) - 6} more_"
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*📋 Highlights:*\n{items}"}
        })

    if is_new:
        blocks.append({
            "type": "actions",
            "elements": [{
                "type": "button",
                "text": {"type": "plain_text", "text": "📖 View Changelog", "emoji": True},
                "url": link,
                "style": "primary"
            }]
        })

    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": "⚡ _Divi Update Watcher · GitHub Actions_"}]
    })

    payload = {"blocks": blocks}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(
                SLACK_HOOK,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=20,
            )
            resp.raise_for_status()
            log(f"✅ Slack sent (attempt {attempt})")
            return True
        except Exception as e:
            log(f"❌ Slack attempt {attempt}/{MAX_RETRIES}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

    log("❌ Slack: all retries failed")
    return False

def main():
    log("=" * 50)
    log("🔎 Divi Version Monitor — Starting check")
    log("=" * 50)

    try:
        title, link, pub_date, content = fetch_rss()
    except RuntimeError as e:
        log(f"💥 FATAL: {e}")
        sys.exit(1)

    changelog = extract_changelog_lines(content, max_items=10)
    log(f"📋 Parsed {len(changelog)} changelog items")

    old_version = read_latest()
    log(f"📁 Stored version : {old_version or '(none)'}")
    log(f"🌐 Latest version : {title}")

    if title != old_version:
        log("🆕 NEW VERSION DETECTED!")

        notify_ok = False

        tg_ok = send_telegram(title, link, pub_date, changelog)
        if tg_ok:
            notify_ok = True

        sl_ok = send_slack(title, link, pub_date, changelog, is_new=True)
        if sl_ok:
            notify_ok = True

        write_latest(title)

        if not notify_ok:
            log("⚠️  Version updated but all notifications failed")
        else:
            log("🎉 All done — notifications sent successfully!")

    else:
        log("✅ No new update. Everything is up to date.")

        if SLACK_HOOK:
            send_slack(title, link, pub_date, changelog, is_new=False)

    log("=" * 50)
    log("✅ Monitor run complete")
    log("=" * 50)

if __name__ == "__main__":
    main()