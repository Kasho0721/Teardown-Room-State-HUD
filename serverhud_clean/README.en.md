# Room State HUD

Steam Workshop:
https://steamcommunity.com/sharedfiles/filedetails/?id=3686800906


This directory contains a **HUD / mod script** used to extract Teardown multiplayer room state.

Its purpose is not fancy UI. It exists to expose structured room state so the bridge can read it and upload it to the cloud service.

---

## What It Maintains

The script tracks data such as:
- host name
- current player count
- max player count
- player list
- uptime / timestamps
- snapshot and sequence values

These values are then consumed by the bridge.

---

## Naming Note

The public-facing mod name has been cleaned up to better match the project:

**Room State HUD**

However, internal registry-style keys and compatibility markers are intentionally preserved so the bridge does not break.

---

## Files

```text
serverhud_clean/
├─ info.txt
└─ main.lua
```
