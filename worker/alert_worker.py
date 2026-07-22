import redis
import json
import time
import requests
import os

r = redis.Redis(host=os.environ.get("REDIS_HOST", "redis"), port=6379, decode_responses=True)
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
DEDUP_WINDOW = 300  # seconds

SEVERITY_EMOJI = {"low": "🟡", "medium": "🟠", "high": "🔴", "critical": "🚨"}


def should_alert(ip, trigger):
    key = f"dedup:{ip}:{trigger}"
    if r.exists(key):
        return False
    r.setex(key, DEDUP_WINDOW, 1)
    return True


def enrich_ip(ip):
    try:
        resp = requests.get(f"https://ipapi.co/{ip}/json/", timeout=3)
        d = resp.json()
        return f"{d.get('country_name', '?')}, {d.get('org', '?')}"
    except Exception:
        return "enrichment unavailable"


def send_telegram(event, max_retries=3):
    geo = enrich_ip(event["ip"])
    msg = (
        f"{SEVERITY_EMOJI.get(event['severity'], '⚠️')} Honeypot triggered: {event['trigger']}\n"
        f"IP: {event['ip']} ({geo})\n"
        f"Path: {event['path']}\n"
        f"Method: {event['method']}\n"
        f"UA: {event['ua'][:120]}\n"
        f"Severity: {event['severity']}\n"
        f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(event['ts']))}"
    )
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                data={"chat_id": CHAT_ID, "text": msg},
                timeout=15,
            )
            if resp.status_code == 200:
                return
            print(f"[!] Telegram send returned {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"[!] Telegram send attempt {attempt}/{max_retries} failed: {e}")
        if attempt < max_retries:
            time.sleep(2 * attempt)  # backoff: 2s, 4s
    # all retries exhausted — fall back to durable local log so the alert isn't silently lost
    with open("/tmp/failed_alerts.log", "a") as f:
        f.write(json.dumps(event) + "\n")
    print(f"[!!] All retries failed for event {event['id']} — written to failed_alerts.log")


def main():
    print("[*] Alert worker started, listening on honeypot:events ...")
    while True:
        _, raw = r.brpop("honeypot:events")
        event = json.loads(raw)
        r.lpush("honeypot:log_archive", raw)
        print(f"[EVENT] {event['trigger']} from {event['ip']}")
        if should_alert(event["ip"], event["trigger"]):
            send_telegram(event)
        else:
            print(f"[dedup] suppressed repeat alert for {event['ip']}/{event['trigger']}")


if __name__ == "__main__":
    main()
