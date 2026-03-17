const DEFAULT_TIMEOUT_MS = 10000;

function normalizeBaseUrl(url) {
  if (!url) {
    throw new Error('CLOUD_CENTER_URL is required');
  }
  return url.replace(/\/+$/, '');
}

async function fetchRooms(baseUrl) {
  const normalizedBaseUrl = normalizeBaseUrl(baseUrl);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);

  try {
    const response = await fetch(`${normalizedBaseUrl}/rooms`, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`cloud-center responded with ${response.status}`);
    }

    const data = await response.json();
    const rooms = Array.isArray(data?.rooms) ? data.rooms : [];
    return rooms;
  } finally {
    clearTimeout(timeout);
  }
}

module.exports = {
  fetchRooms,
};
