#version 2

shared = shared or {}
server = server or {}
client = client or {}

shared.roomState = shared.roomState or {
  hostName = "",
  playerCount = 0,
  maxPlayers = 0,
  players = {},
  startedAt = 0,
  uptimeSeconds = 0,
  lastUpdate = 0,
  sequence = 0,
  changedAt = 0,
  emittedAt = 0,
  snapshot = "",
}

local hud = {
  enabled = true,
  x = 0.03,
  y = 0.08,
  lineH = 24,
  pad = 12,
  width = 520,
}

local textCache = ""
local serverStartedAt = 0
local lastLogAt = -1
local lastSnapshotState = ""

local buildHudLines

local function nowSeconds()
  return math.floor(GetTime())
end

local function safeString(v)
  if v == nil then return "" end
  return tostring(v)
end

local function safeNumber(v, default)
  if type(v) == "number" then return v end
  local n = tonumber(v)
  if n == nil then return default or 0 end
  return n
end

local function shallowCopyList(list)
  local out = {}
  if type(list) ~= "table" then return out end
  for i = 1, #list do
    out[#out + 1] = safeString(list[i])
  end
  return out
end

local function joinPlayers(players)
  return table.concat(shallowCopyList(players), "|")
end

local function ensureServerStartedAt()
  if serverStartedAt == 0 then
    serverStartedAt = nowSeconds()
  end
  if shared.roomState.startedAt == 0 then
    shared.roomState.startedAt = serverStartedAt
  end
end

local function normalizeRoomState()
  local s = shared.roomState
  ensureServerStartedAt()

  s.hostName = safeString(s.hostName)
  s.playerCount = safeNumber(s.playerCount, 0)
  s.maxPlayers = safeNumber(s.maxPlayers, 0)
  s.startedAt = safeNumber(s.startedAt, serverStartedAt)
  s.uptimeSeconds = math.max(0, nowSeconds() - s.startedAt)
  s.lastUpdate = nowSeconds()
  s.sequence = safeNumber(s.sequence, 0)
  s.changedAt = safeNumber(s.changedAt, 0)
  s.emittedAt = safeNumber(s.emittedAt, 0)
  s.snapshot = safeString(s.snapshot)

  if type(s.players) ~= "table" then
    s.players = {}
  end

  if s.playerCount <= 0 and #s.players > 0 then
    s.playerCount = #s.players
  end

  if s.maxPlayers < s.playerCount then
    s.maxPlayers = s.playerCount
  end
end

local function tryCall(fn)
  local ok, a, b, c, d = pcall(fn)
  if ok then return true, a, b, c, d end
  return false, nil, nil, nil, nil
end

local function detectHostName(playerIds)
  playerIds = playerIds or {}

  for _, playerId in ipairs(playerIds) do
    local okHost, isHost = tryCall(function()
      return IsPlayerHost(playerId)
    end)
    if okHost and isHost then
      local okName, name = tryCall(function()
        return GetPlayerName(playerId)
      end)
      if okName and name ~= nil and tostring(name) ~= "" then
        return tostring(name)
      end
    end
  end

  if shared.roomState.hostName ~= "" then
    return shared.roomState.hostName
  end

  return "HOST_UNKNOWN"
end

local function detectPlayerList(playerIds)
  local players = {}
  playerIds = playerIds or {}

  for _, playerId in ipairs(playerIds) do
    local okName, name = tryCall(function()
      return GetPlayerName(playerId)
    end)
    if okName and name ~= nil and tostring(name) ~= "" then
      players[#players + 1] = tostring(name)
    else
      players[#players + 1] = "Player" .. tostring(playerId)
    end
  end

  if #players > 0 then
    return players
  end

  if #shared.roomState.players > 0 then
    return shallowCopyList(shared.roomState.players)
  end

  if shared.roomState.hostName ~= "" and shared.roomState.hostName ~= "HOST_UNKNOWN" then
    return { shared.roomState.hostName }
  end

  return {}
end

local function detectMaxPlayers(playerCount)
  local candidates = {
    function() return GetInt("savegame.mod.serverhud.maxplayers", 12) end,
    function() return GetInt("savegame.mod.maxplayers", 12) end,
  }

  for _, fn in ipairs(candidates) do
    local ok, value = tryCall(fn)
    if ok and value ~= nil then
      local n = tonumber(value)
      if n ~= nil and n > 0 then
        return math.floor(n)
      end
    end
  end

  return math.max(12, shared.roomState.maxPlayers, playerCount)
end

local function buildSnapshotText(state)
  local s = state or shared.roomState
  local playersText = joinPlayers(s.players)
  return "SEQ=" .. tostring(s.sequence)
    .. ";CHANGED=" .. tostring(s.changedAt)
    .. ";EMITTED=" .. tostring(s.emittedAt)
    .. ";HOST=" .. safeString(s.hostName)
    .. ";COUNT=" .. tostring(s.playerCount) .. "/" .. tostring(s.maxPlayers)
    .. ";PLAYERS=" .. playersText
    .. ";UPTIME=" .. tostring(s.uptimeSeconds)
    .. ";LAST=" .. tostring(s.lastUpdate)
end

local function markSnapshotChangeIfNeeded()
  local s = shared.roomState
  local stateKey = safeString(s.hostName)
    .. "#" .. tostring(s.playerCount)
    .. "#" .. tostring(s.maxPlayers)
    .. "#" .. joinPlayers(s.players)

  if stateKey ~= lastSnapshotState then
    s.sequence = safeNumber(s.sequence, 0) + 1
    s.changedAt = nowSeconds()
    lastSnapshotState = stateKey
  end
end

local function writeRoomStateToRegistry()
  local s = shared.roomState
  local base = "savegame.mod.serverhud"
  local playersText = joinPlayers(s.players)

  s.emittedAt = nowSeconds()
  s.snapshot = buildSnapshotText(s)

  SetString(base .. ".hostName", safeString(s.hostName))
  SetInt(base .. ".playerCount", safeNumber(s.playerCount, 0))
  SetInt(base .. ".maxPlayers", safeNumber(s.maxPlayers, 0))
  SetString(base .. ".players", playersText)
  SetInt(base .. ".startedAt", safeNumber(s.startedAt, 0))
  SetInt(base .. ".uptimeSeconds", safeNumber(s.uptimeSeconds, 0))
  SetInt(base .. ".lastUpdate", safeNumber(s.lastUpdate, 0))
  SetInt(base .. ".sequence", safeNumber(s.sequence, 0))
  SetInt(base .. ".changedAt", safeNumber(s.changedAt, 0))
  SetInt(base .. ".emittedAt", safeNumber(s.emittedAt, 0))
  SetString(base .. ".hudText", textCache)
  SetString(base .. ".snapshot", s.snapshot)
end

local function writeRoomStateToDebugLog()
  local nowTs = nowSeconds()
  if lastLogAt == nowTs then
    return
  end
  lastLogAt = nowTs

  local s = shared.roomState
  local playersText = joinPlayers(s.players)
  DebugPrint("TDSTATLOG HOST=" .. safeString(s.hostName)
    .. " COUNT=" .. tostring(s.playerCount) .. "/" .. tostring(s.maxPlayers)
    .. " PLAYERS=" .. playersText
    .. " UPTIME=" .. tostring(s.uptimeSeconds)
    .. " LAST=" .. tostring(s.lastUpdate))
end

local function updateRoomStateFromGame()
  local s = shared.roomState
  ensureServerStartedAt()

  local allPlayerIds = {}
  local okPlayers, playersResult = tryCall(function()
    return GetAllPlayers()
  end)
  if okPlayers and type(playersResult) == "table" then
    allPlayerIds = playersResult
  end

  local hostName = detectHostName(allPlayerIds)
  local players = detectPlayerList(allPlayerIds)
  local playerCount = #players
  local maxPlayers = detectMaxPlayers(playerCount)

  if playerCount == 0 and hostName ~= "" and hostName ~= "HOST_UNKNOWN" then
    players = { hostName }
    playerCount = 1
  end

  s.hostName = hostName
  s.players = players
  s.playerCount = playerCount
  s.maxPlayers = maxPlayers
  normalizeRoomState()
  markSnapshotChangeIfNeeded()
  buildHudLines()
  writeRoomStateToRegistry()
  writeRoomStateToDebugLog()
end

buildHudLines = function()
  local s = shared.roomState
  normalizeRoomState()

  local playersText = joinPlayers(s.players)
  if playersText == "" then playersText = "-" end

  local lines = {
    "TDSTAT",
    "HOST=" .. safeString(s.hostName),
    "COUNT=" .. tostring(s.playerCount) .. "/" .. tostring(s.maxPlayers),
    "PLAYERS=" .. playersText,
    "UPTIME=" .. tostring(s.uptimeSeconds),
  }

  textCache = table.concat(lines, "\n")
  return lines
end

local function drawHud(lines)
  UiPush()
    UiTranslate(UiWidth() * hud.x, UiHeight() * hud.y)
    UiFont("regular.ttf", 22)

    local height = hud.pad * 2 + (#lines * hud.lineH)
    UiColor(0, 0, 0, 0.55)
    UiRect(hud.width, height)

    UiTranslate(hud.pad, hud.pad)
    for i = 1, #lines do
      if i == 1 then
        UiColor(0.4, 1.0, 0.7, 1.0)
      else
        UiColor(1, 1, 1, 1)
      end
      UiText(lines[i])
      UiTranslate(0, hud.lineH)
    end
  UiPop()
end

function server.init()
  ensureServerStartedAt()
  updateRoomStateFromGame()
end

function server.tick(dt)
  updateRoomStateFromGame()
end

function client.init()
end

function client.draw()
  if not hud.enabled then return end
  local lines = buildHudLines()
  drawHud(lines)
end

function serverhud_getRoomState()
  normalizeRoomState()
  return shared.roomState
end

function serverhud_getHudText()
  normalizeRoomState()
  buildHudLines()
  return textCache
end

function serverhud_setDebugState(hostName, playerNames, maxPlayers)
  ensureServerStartedAt()
  shared.roomState.hostName = hostName or shared.roomState.hostName
  shared.roomState.players = shallowCopyList(playerNames or {})
  shared.roomState.playerCount = #shared.roomState.players
  shared.roomState.maxPlayers = maxPlayers or math.max(shared.roomState.playerCount, shared.roomState.maxPlayers, 12)
  normalizeRoomState()
end
