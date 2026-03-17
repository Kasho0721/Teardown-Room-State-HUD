const { fetchRooms } = require('./cloud-center');
const { formatRoomsReply } = require('./formatter');

const SUPPORTED_COMMANDS = new Set(['/服务器', '/在线服务器', '/server', '/status']);
const SERVICE_UNAVAILABLE_MESSAGE = '状态服务暂时不可用，请稍后再试。';

function extractPlainText(message) {
  if (typeof message === 'string') {
    return message.trim();
  }

  if (!Array.isArray(message)) {
    return '';
  }

  const text = message
    .filter((segment) => segment && segment.type === 'text')
    .map((segment) => segment?.data?.text || '')
    .join('');

  return text.trim();
}

function matchCommand(message) {
  const text = extractPlainText(message);
  if (!text) {
    return null;
  }

  const normalized = text.split(/\s+/)[0];
  if (!SUPPORTED_COMMANDS.has(normalized)) {
    return null;
  }

  return normalized;
}

async function buildReplyForCommand(command, config) {
  if (!SUPPORTED_COMMANDS.has(command)) {
    return null;
  }

  try {
    const rooms = await fetchRooms(config.cloudCenterUrl);
    return formatRoomsReply(rooms);
  } catch (error) {
    console.error('[commands] Failed to fetch rooms:', error);
    return SERVICE_UNAVAILABLE_MESSAGE;
  }
}

module.exports = {
  SUPPORTED_COMMANDS,
  SERVICE_UNAVAILABLE_MESSAGE,
  extractPlainText,
  matchCommand,
  buildReplyForCommand,
};
