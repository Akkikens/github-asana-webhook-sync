import os, hmac, hashlib
from typing import Optional
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")
if not SECRET:
    print("⚠️  GITHUB_WEBHOOK_SECRET not set. Set it in .env or environment.")

def verify_sig(raw: bytes, sig_header: Optional[str]) -> bool:
    """make sure this webhook actually came from GitHub"""
    if not sig_header or not sig_header.startswith("sha256="):
        return False
    
    digest = hmac.new(SECRET.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    expected = f"sha256={digest}"
    return hmac.compare_digest(expected, sig_header)

@app.post("/webhooks/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None)
):
    """webhook endpoint with signature verification"""
    if not SECRET:
        raise HTTPException(status_code=500, detail="Server misconfigured: missing GITHUB_WEBHOOK_SECRET")

    raw = await request.body()
    
    if not verify_sig(raw, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    payload = await request.json()
    print("Verified webhook:", payload.get("action"))
    return JSONResponse({"ok": True})
