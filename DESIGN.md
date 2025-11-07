# PR ↔ Asana Webhook Sync (Design)

## Goal
Replace GH Actions–based sync (slow) with instant **GitHub Webhooks → Web server** that translates PR lifecycle events into Asana operations. For this task we only **log intended actions**.

## Event → Intended Action
- `pull_request.opened` → Ensure Asana task exists for PR; assign to PR assignee if present, else to **PR author**.
- `pull_request.assigned` / `edited` (assignee changed) → Update Asana assignee.
- `pull_request.unassigned` → Assign to **PR author** (default).
- `pull_request.closed`:
  - merged: Complete task
  - closed w/o merge: **Complete task** (per spec)
- `pull_request.reopened` → Reopen task
- `pull_request.synchronize` → No-op (optional comment: “new commits pushed”)
