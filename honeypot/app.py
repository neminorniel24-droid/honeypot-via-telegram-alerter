from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
import redis
import json
import uuid
import time
import os

app = FastAPI()
r = redis.Redis(host=os.environ.get("REDIS_HOST", "redis"), port=6379, decode_responses=True)


def emit_event(trigger: str, request: Request, severity: str = "medium"):
    event = {
        "id": str(uuid.uuid4()),
        "trigger": trigger,
        "severity": severity,
        "ip": request.headers.get("x-forwarded-for", request.client.host),
        "ua": request.headers.get("user-agent", "unknown"),
        "path": str(request.url.path),
        "method": request.method,
        "ts": time.time(),
    }
    r.lpush("honeypot:events", json.dumps(event))
    return event


@app.get("/wp-admin")
@app.get("/administrator")
@app.get("/admin")
async def fake_admin(request: Request):
    emit_event("fake_admin_page", request, severity="high")
    return PlainTextResponse("404 Not Found", status_code=404)


@app.get("/api/v1/internal/users")
async def fake_api(request: Request):
    emit_event("fake_internal_api", request, severity="high")
    return JSONResponse({"detail": "Not found"}, status_code=404)


@app.get("/.env")
@app.get("/backup.sql")
@app.get("/config.php.bak")
async def canary_files(request: Request):
    emit_event("canary_file_access", request, severity="critical")
    return PlainTextResponse("", status_code=404)


@app.get("/health")
async def health():
    return {"status": "ok"}
