# Teardown Room Bridge

This directory contains the **local bridge component** that runs on a player's machine.

Its job is to:
- read local Teardown room state
- extract host, player count, player list, and related room information
- periodically upload that state to `cloud-center`
- provide a local web UI for configuration

---

## Features

- local web configuration page
- automatic room state reading
- periodic cloud reporting
- suitable for packaging as a standalone `.exe`
- logging support for troubleshooting

Default local UI:

```text
http://127.0.0.1:8787/
```

---

## Directory Layout

```text
bridge/
├─ agent/
├─ web/
├─ scripts/
├─ packaging/
├─ app.py
├─ run_bridge.py
├─ requirements.txt
└─ bridge_config.example.json
```

---

## Run with Python

```bash
pip install -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8787
```

You can also use the included scripts.

---

## Configuration

This public repository keeps only an example config:

- `bridge_config.example.json`

You should replace the values with your own environment settings.

Example cloud endpoint:

```text
http://your-cloud-center:18080/report
```

---

## Packaging

This project includes packaging scripts for building a standalone executable, such as:

- `scripts/build_exe.bat`
- `scripts/release_nuitka_venv312.cmd`

That makes it easier to distribute to players who do not want to install Python.
