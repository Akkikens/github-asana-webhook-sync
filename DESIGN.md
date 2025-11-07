# PR ↔ Asana Webhook Sync (Design)

## Goal
Replace GH Actions–based sync (slow) with instant **GitHub Webhooks → Web server** that translates PR lifecycle events into Asana operations. For this task we only **log intended actions**.
