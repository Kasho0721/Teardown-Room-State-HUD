# OneBots Room Query Service

This directory contains the **OneBot / QQ room query service**.

Its intended purpose is to:
- receive QQ-side commands
- query room data from `cloud-center`
- send formatted room status replies back to chat

However, this part should **not** be described as fully working yet.
The code structure, query logic, and example configuration are already organized, but **the real QQ / OneBot end-to-end integration has not been fully validated**.

---

## Current Status

Completed so far:

- query service code organized
- environment variable examples prepared
- `cloud-center` room query logic connected
- basic command support:
  - `/服务器`
  - `/在线服务器`
  - `/server`
  - `/status`

Still pending / not fully confirmed:

- whether all required QQ platform capabilities are enabled
- whether the OneBot gateway is delivering events reliably
- whether group and private message events are both received correctly
- whether sending `/服务器` in a real QQ environment completes the full end-to-end reply flow

The more accurate wording right now is:

> **The code and integration skeleton are ready, but final platform-side integration is still in progress.**

---

## How It Works

After startup, the service connects to the OneBot WebSocket endpoint. When it receives a supported command, it requests:

```text
CLOUD_CENTER_URL/rooms
```

It then formats the online room list and sends the result back to the chat.

---

## Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Then fill in:
- `BOT_WS_URL`
- `BOT_ACCESS_TOKEN`
- `CLOUD_CENTER_URL`

Example:

```env
BOT_WS_URL=ws://127.0.0.1:6727/qq/your_app_id/onebot/v12
BOT_ACCESS_TOKEN=change-me-onebot-v12-token
CLOUD_CENTER_URL=http://127.0.0.1:18080
```

These are placeholder values only.
Replace them with your real deployment settings.

---

## Install and Run

```bash
npm install
npm start
```

Check syntax with:

```bash
npm run check
```

Note:
A successful `npm start` only means the process starts.
It does **not** guarantee that QQ platform events are already flowing correctly.

---

## Dependency

This service currently depends on `cloud-center` providing:

```text
GET /rooms
```

Example response:

```json
{
  "ok": true,
  "rooms": []
}
```

---

## Deployment Note

For Linux deployment, using pm2, systemd, Docker, or Podman is recommended.

---

## Known Issues

- the QQ / OneBot end-to-end flow is still not fully verified
- QQ platform capabilities, event subscriptions, and sandbox / release status directly affect whether messages can actually be received
- an online OneBot gateway does not necessarily mean the query service is already receiving group or private events correctly
- the current repository is better treated as an integration base and development skeleton, not a guaranteed plug-and-play final product
