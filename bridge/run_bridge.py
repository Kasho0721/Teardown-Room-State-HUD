from __future__ import annotations

import threading
import time
import webbrowser

import uvicorn

from agent.config import settings
from agent.logging_utils import setup_logging
from app import app as fastapi_app


def open_browser_later() -> None:
    time.sleep(1.2)
    webbrowser.open(f'http://127.0.0.1:{settings.agent_port}/')


if __name__ == '__main__':
    setup_logging()
    threading.Thread(target=open_browser_later, daemon=True).start()
    uvicorn.run(fastapi_app, host='127.0.0.1', port=settings.agent_port, reload=False)
