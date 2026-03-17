require('dotenv').config();

const { buildReplyForCommand, matchCommand } = require('./commands');
const { createOneBotClient, normalizeId } = require('./onebot');

const config = {
  wsUrl: process.env.BOT_WS_URL,
  accessToken: process.env.BOT_ACCESS_TOKEN || '',
  cloudCenterUrl: process.env.CLOUD_CENTER_URL,
};

function isMessageEvent(event) {
  return event?.type === 'message' && typeof event?.detail_type === 'string';
}

function normalizeMessageEvent(event) {
  if (!isMessageEvent(event)) {
    return null;
  }

  const detailType = event.detail_type;
  const userId = normalizeId(event.user_id || event?.sender?.user_id || event?.user?.id);
  const groupId = normalizeId(event.group_id || event?.group?.group_id || event?.group?.id);

  return {
    id: normalizeId(event.id || event.message_id),
    time: Number(event.time || 0),
    detailType,
    subType: typeof event.sub_type === 'string' ? event.sub_type : '',
    userId,
    groupId,
    message: event.message,
    rawEvent: event,
  };
}

async function handleEvent(event, client) {
  const normalizedEvent = normalizeMessageEvent(event);
  if (!normalizedEvent) {
    return;
  }

  const command = matchCommand(normalizedEvent.message);
  if (!command) {
    return;
  }

  const reply = await buildReplyForCommand(command, config);
  if (!reply) {
    return;
  }

  if (normalizedEvent.detailType === 'group' && normalizedEvent.groupId) {
    client.replyToMessage(normalizedEvent, reply);
    return;
  }

  if (normalizedEvent.detailType === 'private' && normalizedEvent.userId) {
    client.replyToMessage(normalizedEvent, reply);
  }
}

function validateConfig() {
  if (!config.wsUrl) {
    throw new Error('Missing BOT_WS_URL');
  }
  if (!config.cloudCenterUrl) {
    throw new Error('Missing CLOUD_CENTER_URL');
  }
}

function main() {
  validateConfig();
  console.log('[bot] Starting cloud-center OneBot V12 service');
  console.log(`[bot] cloud-center: ${config.cloudCenterUrl}`);
  console.log(`[bot] onebot ws: ${config.wsUrl}`);

  const client = createOneBotClient({
    wsUrl: config.wsUrl,
    accessToken: config.accessToken,
    onEvent: handleEvent,
  });

  const shutdown = () => {
    console.log('[bot] Shutting down');
    client.close();
    process.exit(0);
  };

  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);
}

main();
