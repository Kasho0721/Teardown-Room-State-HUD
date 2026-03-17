const DELAY_THRESHOLD_SECONDS = 90;

function formatTimestamp(timestampSeconds) {
  if (!timestampSeconds || Number.isNaN(Number(timestampSeconds))) {
    return '未知';
  }

  const date = new Date(Number(timestampSeconds) * 1000);
  if (Number.isNaN(date.getTime())) {
    return '未知';
  }

  const formatter = new Intl.DateTimeFormat('zh-CN', {
    hour12: false,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });

  return formatter.format(date);
}

function pickLatestReportedAt(rooms) {
  return rooms.reduce((latest, room) => {
    const reportedAt = Number(room?.reportedAt || 0);
    return reportedAt > latest ? reportedAt : latest;
  }, 0);
}

function getDelayWarnings(onlineRooms, nowSeconds = Math.floor(Date.now() / 1000)) {
  const delayedRooms = onlineRooms.filter((room) => {
    const reportedAt = Number(room?.reportedAt || 0);
    return reportedAt > 0 && nowSeconds - reportedAt > DELAY_THRESHOLD_SECONDS;
  });

  if (delayedRooms.length === 0) {
    return [];
  }

  const maxDelay = delayedRooms.reduce((acc, room) => {
    const reportedAt = Number(room?.reportedAt || 0);
    const delay = Math.max(0, nowSeconds - reportedAt);
    return Math.max(acc, delay);
  }, 0);

  return [
    `⚠ 数据可能延迟：有 ${delayedRooms.length} 台在线服务器超过 ${DELAY_THRESHOLD_SECONDS} 秒未上报，最长约 ${maxDelay} 秒。`,
  ];
}

function formatRoomLine(room, index) {
  const roomLabel = room?.roomLabel || room?.reporterName || room?.reporterId || '未命名房间';
  const hostName = room?.hostName || '未知房主';
  const playerCount = Number(room?.playerCount || 0);
  const maxPlayers = Number(room?.maxPlayers || 0);
  const roomCode = room?.roomCode ? ` | 房间码 ${room.roomCode}` : '';

  return `${index}. ${roomLabel} | ${hostName} | ${playerCount}/${maxPlayers || '?'}人${roomCode}`;
}

function formatRoomDetails(room) {
  const details = [];
  if (Array.isArray(room?.players) && room.players.length > 0) {
    details.push(`   玩家：${room.players.join('、')}`);
  }
  if (room?.reporterName || room?.reporterId) {
    details.push(`   上报端：${room.reporterName || room.reporterId}`);
  }
  if (room?.reportedAt) {
    details.push(`   最近上报：${formatTimestamp(room.reportedAt)}`);
  }
  return details;
}

function formatRoomsReply(rooms, options = {}) {
  const nowSeconds = options.nowSeconds || Math.floor(Date.now() / 1000);
  const onlineRooms = rooms
    .filter((room) => Boolean(room?.online) && !Boolean(room?.offline))
    .sort((a, b) => {
      const reportedDiff = Number(b?.reportedAt || 0) - Number(a?.reportedAt || 0);
      if (reportedDiff !== 0) {
        return reportedDiff;
      }
      return String(a?.roomLabel || a?.reporterName || '').localeCompare(String(b?.roomLabel || b?.reporterName || ''));
    });

  if (onlineRooms.length === 0) {
    return [
      '当前在线服务器：0 台',
      '暂无在线房间，请稍后再试。',
      `最后检查时间：${formatTimestamp(nowSeconds)}`,
    ].join('\n');
  }

  const lines = [`当前在线服务器：${onlineRooms.length} 台`];

  onlineRooms.forEach((room, index) => {
    lines.push(formatRoomLine(room, index + 1));
    lines.push(...formatRoomDetails(room));
  });

  const latestReportedAt = pickLatestReportedAt(onlineRooms);
  lines.push(`最后更新时间：${formatTimestamp(latestReportedAt)}`);
  lines.push(...getDelayWarnings(onlineRooms, nowSeconds));
  lines.push('提示：状态来自 cloud-center，可能存在短暂同步延迟。');

  return lines.join('\n');
}

module.exports = {
  DELAY_THRESHOLD_SECONDS,
  formatRoomsReply,
  formatTimestamp,
};
