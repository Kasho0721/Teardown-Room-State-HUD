from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from agent.runtime_paths import log_file_path

_LOGGING_INITIALIZED = False


def setup_logging() -> Path:
    global _LOGGING_INITIALIZED

    log_path = log_file_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    if _LOGGING_INITIALIZED:
        return log_path

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt='%(asctime)s %(levelname)s %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    has_file_handler = False
    has_console_handler = False
    log_path_resolved = log_path.resolve()

    for handler in root_logger.handlers:
        if isinstance(handler, RotatingFileHandler):
            base_name = getattr(handler, 'baseFilename', '')
            if base_name and Path(base_name).resolve() == log_path_resolved:
                has_file_handler = True
        elif isinstance(handler, logging.StreamHandler):
            has_console_handler = True
        handler.setFormatter(formatter)

    if not has_file_handler:
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=3 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8',
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    if not has_console_handler and sys.stdout is not None:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    logging.captureWarnings(True)
    logging.getLogger(__name__).info(
        'Logging initialized: file=%s pid=%s frozen=%s',
        log_path_resolved,
        os.getpid(),
        getattr(sys, 'frozen', False),
    )
    _LOGGING_INITIALIZED = True
    return log_path
