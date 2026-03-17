# OneBots Room Query Service

[English Version](./README.en.md)

本目录是 **OneBot / QQ 房间查询服务**。

它的目标是：
- 接收 QQ 侧命令
- 查询 `cloud-center` 的房间列表
- 把在线房间信息回复到聊天里

现在这部分**还不能写成“已经完全可用”**。
代码结构、查询逻辑、配置样例都已经整理好了，
但 **QQ / OneBot 实际联调还没有完全跑通**。

---

## 当前状态

目前已经完成：

- OneBot 查询服务代码整理
- 环境变量样例整理
- `cloud-center` 房间查询逻辑接入
- 基础命令支持：
  - `/服务器`
  - `/在线服务器`
  - `/server`
  - `/status`

目前仍待确认 / 待完成：

- QQ 平台侧能力是否完整开启
- OneBot 网关实际消息投递是否稳定
- 群聊 / 私聊事件是否都能正常收到
- 实际发送 `/服务器` 后是否能完成端到端回复

所以目前更准确的说法是：

> **代码与接入框架已具备，但最终平台联调仍在进行中。**

---

## 工作方式

服务启动后，会连接 OneBot WebSocket，然后在收到命令时请求：

```text
CLOUD_CENTER_URL/rooms
```

再把在线房间整理成文本，返回到群聊或私聊。

---

## 环境变量

复制 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

然后填写：

- `BOT_WS_URL`：OneBot WebSocket 地址
- `BOT_ACCESS_TOKEN`：OneBot access token
- `CLOUD_CENTER_URL`：cloud-center 服务地址

示例：

```env
BOT_WS_URL=ws://127.0.0.1:6727/qq/your_app_id/onebot/v12
BOT_ACCESS_TOKEN=change-me-onebot-v12-token
CLOUD_CENTER_URL=http://127.0.0.1:18080
```

这些都是示例值，部署时请换成你自己的实际配置。

---

## 安装与运行

```bash
npm install
npm start
```

运行检查：

```bash
npm run check
```

注意：
`npm start` 只能说明服务进程启动了，
**不代表 QQ 平台侧事件一定已经成功接通。**

---

## 依赖接口

当前依赖 `cloud-center` 提供：

```text
GET /rooms
```

返回格式示例：

```json
{
  "ok": true,
  "rooms": []
}
```

---

## 部署建议

如果你部署在 Linux 服务器上，建议用：
- pm2
- systemd
- Docker / Podman

来托管这个服务。

但在正式对外使用前，建议先完成一次真实 QQ 环境下的端到端验证。

---

## 适用场景

适合：
- QQ 群内查询当前在线房间
- 不想让群友手动打开网页
- 给 Teardown 联机房状态做一个聊天入口

---

## Known Issues

- 当前 QQ / OneBot 端到端联调仍未完全完成
- QQ 平台侧能力、事件订阅和沙箱 / 发布状态会直接影响是否能收到消息
- OneBot 网关在线，不代表查询服务一定已经成功收到群聊或私聊事件
- 当前仓库更适合作为接入基础和开发骨架，而不是“开箱即用成品”
