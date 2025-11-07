import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

@app.post("/webhooks/github")
async def github_webhook(request: Request):
    """basic webhook endpoint to receive GitHub events"""
    payload = await request.json()
    print("Received webhook:", payload.get("action"))
    return JSONResponse({"ok": True})
