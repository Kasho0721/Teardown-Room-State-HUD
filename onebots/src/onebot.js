const WebSocket = require('ws');

function buildWsHeaders(accessToken) {
  if (!accessToken) {
    return {};
  }

  return {
    Authorization: `Bearer ${accessToken}`,
  };
}

function sendJson(ws, payload) {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    throw new Error('OneBot websocket is not connected');
  }
  ws.send(JSON.stringify(payload));
}

function normalizeId(value) {
  if (value === undefined || value === null || value === '') {
    return null;
  }
  return String(value);
}

function buildTextMessage(message) {
  const text = typeof message === 'string' ? message : String(message ?? '');
  return [
    {
      type: 'text',
      data: {
        text,
      },
    },
  ];
}

function isEventPayload(payload) {
  return Boolean(payload && typeof payload === 'object' && typeof payload.type === 'string' && typeof payload.detail_type === 'string');
}

function isActionResponsePayload(payload) {
  return Boolean(payload && typeof payload === 'object' && typeof payload.status === 'string' && Object.prototype.hasOwnProperty.call(payload, 'retcode'));
}

function createMessageApi(ws) {
  return {
    sendMessage(params) {
      sendJson(ws, {
        action: 'send_message',
        params,
        echo: `send-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      });
    },
    sendGroupMessage(groupId, message) {
      this.sendMessage({
        detail_type: 'group',
        group_id: normalizeId(groupId),
        message: buildTextMessage(message),
      });
    },
    sendPrivateMessage(userId, message) {
      this.sendMessage({
        detail_type: 'private',
        user_id: normalizeId(userId),
        message: buildTextMessage(message),
      });
    },
    replyToMessage(target, message) {
      if (!target || !target.detailType) {
        throw new Error('Missing reply target detailType');
      }

      if (target.detailType === 'group' && target.groupId) {
        this.sendGroupMessage(target.groupId, message);
        return;
      }

      if (target.detailType === 'private' && target.userId) {
        this.sendPrivateMessage(target.userId, message);
        return;
      }

      throw new Error(`Unsupported reply target detailType: ${target.detailType}`);
    },
  };
}

function createOneBotClient(options) {
  const {
    wsUrl,
    accessToken,
    onEvent,
    reconnectDelayMs = 5000,
  } = options;

  if (!wsUrl) {
    throw new Error('BOT_WS_URL is required');
  }

  let ws = null;
  let reconnectTimer = null;
  let closedByUser = false;

  const connect = () => {
    console.log(`[onebot] Connecting to ${wsUrl}`);
    ws = new WebSocket(wsUrl, {
      headers: buildWsHeaders(accessToken),
    });

    ws.on('open', () => {
      console.log('[onebot] WebSocket connected');
    });

    ws.on('message', async (raw) => {
      try {
        const text = raw.toString();
        const payload = JSON.parse(text);

        if (isActionResponsePayload(payload)) {
          if (payload.status !== 'ok') {
            console.warn('[onebot] Action failed:', payload);
          }
          return;
        }

        if (!isEventPayload(payload)) {
          return;
        }

        if (typeof onEvent === 'function') {
          await onEvent(payload, createMessageApi(ws));
        }
      } catch (error) {
        console.error('[onebot] Failed to handle incoming message:', error);
      }
    });

    ws.on('error', (error) => {
      console.error('[onebot] WebSocket error:', error.message);
    });

    ws.on('close', (code, reason) => {
      console.warn(`[onebot] WebSocket closed: code=${code}, reason=${reason.toString()}`);
      ws = null;
      if (!closedByUser) {
        reconnectTimer = setTimeout(connect, reconnectDelayMs);
      }
    });
  };

  connect();

  return {
    close() {
      closedByUser = true;
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
      }
      if (ws) {
        ws.close();
      }
    },
  };
}

module.exports = {
  buildTextMessage,
  createOneBotClient,
  normalizeId,
};
