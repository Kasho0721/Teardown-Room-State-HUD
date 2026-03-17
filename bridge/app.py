from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import uvicorn

from agent.config import Settings, settings
from agent.local_config import load_local_config, save_local_config
from agent.logging_utils import setup_logging
from agent.runtime_paths import config_path, ui_candidates, ui_path
from agent.service import AgentService


LOG_PATH = setup_logging()
logger = logging.getLogger(__name__)
service = AgentService(settings)


def get_ui_html():
    resolved_ui_path = ui_path()

    for path in ui_candidates():
        if path.exists():
            logger.info('Found UI at: %s', path)
            return path.read_text(encoding='utf-8')

    logger.error('UI file not found, candidates: %s', [str(path) for path in ui_candidates()])
    logger.info('Expected fallback UI path: %s', resolved_ui_path)
    return None


# 预加载 HTML
_UI_HTML = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global _UI_HTML
    logger.info(
        'Bridge startup: cwd=%s config=%s ui=%s log=%s cloud=%s port=%s',
        __import__('os').getcwd(),
        config_path(),
        ui_path(),
        LOG_PATH,
        settings.cloud_endpoint,
        settings.agent_port,
    )
    _UI_HTML = get_ui_html()
    service.start()
    yield
    service.stop()


app = FastAPI(title='Teardown Room Bridge', lifespan=lifespan)


@app.get('/')
def root():
    if _UI_HTML:
        return HTMLResponse(_UI_HTML)
    return {'name': settings.agent_name, 'endpoints': ['/health', '/status', '/bridge/status', '/config']}


@app.get('/health')
def health():
    return service.get_health()


@app.get('/status')
def status():
    return service.get_status()


@app.get('/bridge/status')
def bridge_status():
    return service.get_bridge_status()


@app.get('/config')
def get_config():
    return load_local_config()


@app.post('/config')
async def post_config(request: Request):
    data = await request.json()
    cfg = save_local_config(data)
    global service
    service.stop()
    service = AgentService(Settings.from_env())
    service.start()
    return {'ok': True, 'config': cfg}


if __name__ == '__main__':
    uvicorn.run('app:app', host='127.0.0.1', port=settings.agent_port, reload=False)
