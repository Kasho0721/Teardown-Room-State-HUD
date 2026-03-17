# Cloud Center

This directory contains the **cloud aggregation service**.

It receives room state reports from local bridges and provides:
- room state aggregation
- online / offline decision logic
- dashboard display
- APIs for bot or client queries

---

## Features

- accepts bridge reports
- stores current room state
- returns online room lists
- provides a dashboard page
- provides `/rooms` and related endpoints

---

## Current Online Rule

The current rule is intentionally simple:
- heartbeat changed -> online
- no new change for 30 seconds -> offline

---

## Run

```bash
pip install -r requirements.txt
python server_std.py
```

After startup, it typically provides:
- dashboard page
- `/rooms`
- `/report`

---

## Example Data

A sample file is included for public reference:

- `data.example/rooms.example.json`

Do not commit real runtime room data to a public repository.
