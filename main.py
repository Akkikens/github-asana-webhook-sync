import os, hmac, hashlib, json
from typing import Any, Dict, Optional
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

def external_id(repo_full: str, pr_number: int) -> str:
    """just a simple way to uniquely identify a PR: owner/repo#123"""
    return f"{repo_full}#{pr_number}"

def pr_author_login(pr: Dict[str, Any]) -> Optional[str]:
    """who opened this PR?"""
    user = pr.get("user") or {}
    return user.get("login")

def current_assignee_login(pr: Dict[str, Any]) -> Optional[str]:
    """who's assigned to the PR right now (if anyone)"""
    assignee = pr.get("assignee") or {}
    return assignee.get("login")

def plan_intended_action(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    figure out what we'd do in Asana based on what happened in GitHub
    not actually calling any APIs yet, just planning
    """
    action = payload.get("action")
    pr = payload.get("pull_request")
    repo_full = payload.get("repository", {}).get("full_name")

    if not pr or not repo_full:
        return {"kind": "noop", "reason": "missing pr or repo"}

    pr_num = pr.get("number")
    ext = external_id(repo_full, pr_num)
    assignee = current_assignee_login(pr)
    author = pr_author_login(pr)
    merged = bool(pr.get("merged"))

    # fallback: if nobody's assigned, use the author
    default_assignee = author

    if action == "opened":
        return {
            "kind": "ensure_task",
            "externalId": ext,
            "assignTo": assignee or default_assignee,
            "source": "opened"
        }

    if action in ("assigned", "edited"):
        if assignee:
            return {"kind": "assign", "externalId": ext, "assignTo": assignee, "source": action}
        return {"kind": "assign", "externalId": ext, "assignTo": default_assignee, "source": action}

    if action == "unassigned":
        return {"kind": "assign", "externalId": ext, "assignTo": default_assignee, "source": "unassigned->author"}

    if action == "closed":
        return {"kind": "complete", "externalId": ext, "merged": merged}

    if action == "reopened":
        return {"kind": "reopen", "externalId": ext}

    if action == "synchronize":
        return {"kind": "noop", "reason": "new commits pushed; no asana change"}

    return {"kind": "noop", "reason": f"unhandled action {action}"}

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
