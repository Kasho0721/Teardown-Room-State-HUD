from __future__ import annotations

import sys
from pathlib import Path


def app_root() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def logs_dir() -> Path:
    return app_root() / 'logs'


def log_file_path() -> Path:
    return logs_dir() / 'bridge.log'


def ui_candidates() -> list[Path]:
    root = app_root()
    candidates: list[Path] = []
    for name in ['webui.html', 'ui.html']:
        candidates.append(root / name)

    internal = root / '_internal'
    if internal.exists():
        for name in ['webui.html', 'ui.html']:
            candidates.append(internal / name)
    return candidates


def ui_path() -> Path:
    for path in ui_candidates():
        if path.exists():
            return path
    return app_root() / 'webui.html'


def config_path() -> Path:
    root = app_root()
    internal = root / '_internal'
    if internal.exists():
        return internal / 'bridge_config.json'
    return root / 'bridge_config.json'
