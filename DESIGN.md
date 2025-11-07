# GitHub ↔ Asana Webhook Sync (Design Doc)

## Context
Right now, our GitHub-Asana sync uses GitHub Actions. It works fine, but it's not exactly snappy — every time we need to sync something, we're spinning up a whole runner, which adds like 30+ seconds of lag each time.

I wanted to see if we could do better. So I built a webhook-based version that just reacts directly to GitHub events as they happen. This first version doesn't actually make any Asana API calls yet — it just receives the webhooks and logs out what it *would* do. The idea is to get the foundation solid before we start hitting real APIs.

## What I'm trying to accomplish
- **Make it faster:** Instead of waiting for Actions to spin up, just catch the webhook and handle it immediately
- **Keep the code simple:** I want this to be easy to read and maintain. No over-engineering or clever tricks that make it hard to understand what's going on
- **Make sure it's reliable:** Verify webhook signatures properly, only process the events we care about, and log everything clearly so we can debug issues
- **Set us up for the future:** Structure things so plugging in real Asana API calls later is straightforward

## How GitHub events map to Asana actions

| GitHub Action | What we'll do in Asana | Notes |
|----------------|-------------------------|-------|
| `opened` | Create a task for the PR (if it doesn't exist) and assign it to whoever's assigned to the PR. If nobody's assigned, just use the PR author. | Falls back to author if no assignee |
| `assigned` / `edited` | Update the task's assignee to match whoever's currently assigned on the PR | |
| `unassigned` | Put the task back on the PR author's plate | |
| `closed` (merged or not) | Mark the task as done | |
| `reopened` | Reopen the task | |
| `synchronize` | Nothing — just log that commits were pushed | We don't need to do anything when code changes |

For each of these, we're currently just logging a structured JSON "plan" that describes what the Asana API call would look like.

## How it's built
- **Framework:** FastAPI (Python) — seemed like the obvious choice for a simple webhook receiver
- **Endpoint:** `POST /webhooks/github`
- **Security:** Verifying signatures with HMAC-SHA256 using the `GITHUB_WEBHOOK_SECRET`
- **Response:** Always returns `200 OK` after we verify the signature is legit
- **Logging:** Prints out structured JSON so we can see exactly what's happening:
  ```json
  {
    "event": "pull_request",
    "action": "opened",
    "repo": "Akkikens/github-asana-webhook-sync",
    "plan": {
      "kind": "ensure_task",
      "assignTo": "Akkikens"
    }
  }
  ```

## Next steps
That's basically it. Next step is wiring up the actual Asana API calls, but I wanted to make sure the webhook handling itself was solid first.