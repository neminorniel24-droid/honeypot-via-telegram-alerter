# Honeypot with Real-Time Telegram Alerting

A lightweight, containerized deception system that detects reconnaissance and exploitation attempts against decoy endpoints and delivers real-time alerts via Telegram. Built to demonstrate deception-based threat detection patterns used in enterprise security operations, scaled down into a reproducible, self-hosted stack.

## Architecture
Internet / Attacker
│
▼

Honeypot Service (FastAPI)
│
├── Fake admin panel (/wp-admin, /admin, /administrator)
├── Fake internal API (/api/v1/internal/users)
└── Canary files (/.env, /backup.sql, /config.php.bak)
│
▼

Redis Event Queue
│
▼
Alert Worker
│
├── Deduplication (5-minute window per IP + trigger)
├── IP geolocation enrichment
├── Retry logic with exponential backoff
└── Durable local fallback log on delivery failure
│
▼
Telegram Bot API(Bot Father)
│
▼
Real-time alert to operator

Detection and alerting are intentionally decoupled — the honeypot only emits events, and a separate worker process decides how and whether to alert. This prevents a single scanner sweep from flooding the alert channel, and keeps a durable audit trail independent of whether any one alert delivery succeeds.

## Stack

- **FastAPI** — decoy HTTP service
- **Redis** — event queue and short-term dedup state
- **Python worker** — consumes events, enriches, alerts, retries
- **Telegram Bot API** — real-time notification delivery
- **Docker Compose** — orchestration
- **OWASP Juice Shop** — included as an isolated, deliberately vulnerable target for safe offensive practice, separate from the honeypot itself

## Features

- Fake admin login, internal API, and canary file endpoints that mimic common attacker targets
- Structured JSON events (trigger type, IP, user-agent, path, method, timestamp, severity)
- Per-IP, per-trigger deduplication to prevent alert fatigue during automated scans
- Severity-tagged alerts (low / medium / high / critical) with distinct visual indicators
- Retry with exponential backoff on alert delivery failure, plus a local durable fallback log so no event is silently lost
- Fully isolated Docker network — no shared state with any real application

## Setup

```bash
git clone https://github.com/neminorniel24-droid/honeypot-via-telegram-alerter.git
cd honeypot-via-telegram-alerter
cp .env.example .env
# Edit .env with your Telegram bot token and chat ID
docker compose up --build -d
```

Get a Telegram bot token via [@BotFather](https://t.me/BotFather) (`/newbot`), then retrieve your chat ID:

```bash
curl -s "https://api.telegram.org/bot<TOKEN>/getUpdates"
```


### Test it

```bash
curl http://localhost:8000/wp-admin
curl http://localhost:8000/.env
curl http://localhost:8000/api/v1/internal/users
```

Each should trigger a distinct Telegram alert with severity-appropriate formatting.

## Why This Matters — Industry and Government Relevance

Deception technology is a recognized, growing category within modern cybersecurity practice, distinct from traditional perimeter defenses like firewalls and signature-based intrusion detection. It doesn't try to block attackers outright — it detects them by luring interaction with resources that have no legitimate reason to be touched. Any hit is inherently high-confidence, since real users and real application logic never reach these paths.

### Industry benefits

- **Early breach detection**: Traditional monitoring often only flags an incident after data has already been accessed or exfiltrated. Decoys catch attackers during the reconnaissance phase — before they reach anything real — giving defenders a head start.
- **Near-zero false positives**: Unlike anomaly-based detection systems that require tuning and generate substantial noise, a hit on a honeypot route is almost never benign. This makes alerts actionable rather than something analysts learn to ignore.
- **Low operational cost**: This entire stack runs on modest resources (a few small containers) and requires no proprietary licensing, making it accessible to organizations that can't afford commercial deception platforms (e.g. Illusive Networks, Attivo/SentinelOne deception products, TrapX).
- **Attacker profiling**: Logged user-agents, request patterns, and (with future enhancements like fake credential capture) attempted payloads help security teams understand what tools and techniques are actively targeting their perimeter, informing prioritization of real defenses.
- **Compliance support**: Frameworks such as ISO 27001, SOC 2, and PCI-DSS increasingly expect evidence of proactive threat detection capabilities, not just reactive controls — deception technology is one recognized way to demonstrate this.

### Government and public sector relevance

- **Critical infrastructure protection**: Government networks and critical infrastructure operators are common targets for both opportunistic and state-sponsored reconnaissance. Cheap, easily deployable decoys across many endpoints let smaller agencies with limited security budgets extend meaningful detection coverage.
- **Threat intelligence contribution**: Aggregated, anonymized data from honeypot networks (a technique long used by national CERTs and organizations like SANS Internet Storm Center) helps build a broader picture of active scanning campaigns, emerging exploitation techniques, and botnet activity.
- **Insider threat and lateral movement detection**: Internally deployed decoys (not just internet-facing ones) can detect compromised internal accounts or malicious insiders probing systems they have no legitimate reason to access — relevant in classified or sensitive environments where external perimeter defense isn't the only concern.
- **Low-cost force multiplier**: Public sector security teams are frequently understaffed relative to private industry. A detection method that requires no per-seat licensing and minimal maintenance overhead extends limited analyst attention further.
- **Alignment with Zero Trust initiatives**: Many government cybersecurity mandates (e.g., US federal Zero Trust Architecture guidance) emphasize assuming breach and detecting lateral movement rather than relying solely on perimeter defense — deception technology directly supports this posture.

## Known Limitations

This is an educational and portfolio project, not a production-hardened deployment. Notable gaps, documented transparently:

- No persistent storage beyond Redis; event history is lost if the Redis container restarts without a mounted volume
- Fake endpoints currently return generic 404s rather than believable fake content, limiting attacker profiling depth
- No reverse proxy layer yet to make decoy routes indistinguishable from a real application's routes
- Not yet tested against real internet-facing traffic; currently validated only in a local Docker environment
- No integration with threat intelligence feeds (e.g. AbuseIPDB, GreyNoise) to filter out known benign scanners

## Roadmap

- [ ] Fake login page with credential capture (logged, never actually authenticates)
- [ ] Persistent structured logging (SQLite or Elasticsearch)
- [ ] nginx reverse proxy layer for production-realistic deployment
- [ ] Threat intelligence enrichment and noise suppression
- [ ] Daily digest mode for low-severity events to reduce alert fatigue

## Disclaimer

This project is intended for use on infrastructure you own or are explicitly authorized to test. It is built and documented as part of ongoing cybersecurity testing and research. Do not deploy detection or deception tooling against systems without proper authorization.

## Author

Nemin Orniel — Computer Science student, Karunya University. Built as part of hands-on penetration testing and defensive security practice.
