# Teardown Room Center

A complete setup for **Teardown multiplayer room state collection, cloud aggregation, dashboard display, and QQ / OneBot queries**.

This project solves two practical problems:

1. Each host player can run a small local bridge that reports room status to a cloud service.
2. The cloud service aggregates all active rooms and exposes them through a web dashboard and a QQ bot.

---

## Project Structure

```text
GitHub/
├─ bridge/           # Local bridge running on player machines
├─ cloud-center/     # Cloud aggregation service + dashboard
├─ onebots/          # OneBot V12 query service
├─ serverhud_clean/  # HUD / mod script used for room state extraction
├─ .gitignore
├─ .gitattributes
├─ LICENSE
└─ README.md
```

---

## Architecture

### 1) bridge
Runs on the player's local machine.

Responsibilities:
- Read local room state
- Extract host name, player count, player list, room info, and heartbeat data
- Periodically upload state to `cloud-center`
- Provide a local web UI for configuration

Default local UI:

```text
http://127.0.0.1:8787/
```

This module is suitable for packaging into a standalone Windows executable and sharing with other players.

---

### 2) cloud-center
Runs on a server.

Responsibilities:
- Accept status reports from bridges
- Store and maintain current room state
- Determine online / offline state based on heartbeat changes
- Provide a dashboard page
- Expose room query APIs for bot services

Current online/offline rule:
- heartbeat changed -> online
- no new change for 30 seconds -> offline

---

### 3) onebots
Runs on a server.

Responsibilities:
- Connect to a OneBot V12 WebSocket endpoint
- Receive group or private commands
- Query `cloud-center` `/rooms`
- Return a formatted online room list

Example commands:
- `/服务器`
- `/在线服务器`
- `/server`
- `/status`

---

## Quick Start

### bridge

```bash
cd bridge
pip install -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8787
```

---

### cloud-center

```bash
cd cloud-center
pip install -r requirements.txt
python server_std.py
```

---

### onebots

```bash
cd onebots
npm install
cp .env.example .env
npm start
```

Then update `.env` with your own values.

---

## Example Config Files

This public version contains example values only:

- `bridge/bridge_config.example.json`
- `cloud-center/data.example/rooms.example.json`
- `onebots/.env.example`

Replace them with your own endpoints, tokens, app IDs, and admin secrets before deployment.

---

## Current Status

- `bridge`: core local collection flow has been organized and is suitable for further packaging / deployment work
- `cloud-center`: core aggregation and dashboard flow is in place
- `onebots`: code and example configuration are included, but **the real QQ / OneBot end-to-end integration is not fully validated yet**

At the moment, the `onebots` module should be treated as:
- code structure ready
- example configuration prepared
- **still pending final platform-side capability setup and end-to-end verification**

---

## Known Issues

- the `onebots` module has not completed real end-to-end verification in a live QQ environment yet
- QQ platform-side capabilities, event subscriptions, sandbox / release state, and platform review state may affect whether messages actually reach the bot service
- a running OneBot gateway process does not guarantee that chat events are flowing into the query service correctly
- this public repository provides code, example configuration, and integration structure, but is not guaranteed to be fully plug-and-play

---

## Public Release Notes

This repository has already been cleaned for public publishing:
- build artifacts removed
- logs removed
- runtime data removed
- virtual environments removed
- `node_modules` removed
- real IPs / tokens / secrets replaced with placeholders

