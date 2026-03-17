# Teardown Room Center

[English Version](./README.en.md)


一个用于 **Teardown 联机房间状态采集、云端汇总展示、以及 QQ/OneBot 查询** 的完整方案。

这套项目主要解决两件事：

1. 让每个开房玩家本地运行一个小型 bridge，把当前房间状态自动上报到云端。
2. 让云端统一汇总所有房间，并通过网页和 QQ 机器人对外展示在线状态。

---

## 项目结构

```text
GitHub/
├─ bridge/           # 本地 bridge，运行在玩家电脑上
├─ cloud-center/     # 云端汇总服务 + Dashboard
├─ onebots/          # OneBot V12 机器人服务
├─ serverhud_clean/  # 相关 HUD / mod 脚本
├─ .gitignore
└─ README.md
```

---

## 整体架构

### 1) bridge
运行在玩家本地机器上。

它会：
- 读取本地房间状态
- 生成房主、人数、玩家列表、房间信息等状态数据
- 周期性上报到云端 `cloud-center`
- 提供一个本地 Web UI 方便配置

默认本地页面：

```text
http://127.0.0.1:8787/
```

适合打包成 exe 后发给群友直接运行。

---

### 2) cloud-center
运行在服务器上。

它会：
- 接收 bridge 的状态上报
- 保存并维护当前房间状态
- 根据心跳变化判断在线 / 离线
- 提供网页 Dashboard
- 对外提供房间列表接口，供机器人查询

当前核心思路：
- 有心跳变化：判定在线
- 持续 30 秒没有新变化：判定离线

---

### 3) onebots
运行在服务器上。

它会：
- 连接 OneBot V12 WebSocket
- 接收群聊 / 私聊命令
- 查询 `cloud-center` 的 `/rooms`
- 返回在线房间列表

当前支持命令示例：
- `/服务器`
- `/在线服务器`
- `/server`
- `/status`

---

## 适用场景

这套东西适合：
- Teardown 多人联机房管理
- 群内快速查询谁在开房
- 把分散在不同玩家电脑上的联机状态统一展示出来
- 给 QQ 群加一个“查房间状态”的机器人入口

---

## 快速开始

## 一、本地 bridge
进入 `bridge/` 目录后：

```bash
pip install -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8787
```

或者直接使用项目里的启动脚本。

配置完成后，bridge 会把房间状态上报到云端。

公开仓库里提供的是示例配置：

- `bridge/bridge_config.example.json`

你需要自行复制并改成自己的配置。

---

## 二、云端 cloud-center
进入 `cloud-center/` 目录后：

```bash
pip install -r requirements.txt
python server_std.py
```

启动后可提供：
- Dashboard 页面
- `/rooms` 接口
- `/report` 上报入口

如果你要部署到公网，建议再配一个反向代理。

---

## 三、OneBot 服务
进入 `onebots/` 目录后：

```bash
npm install
cp .env.example .env
npm start
```

然后按你的实际环境填写 `.env`：
- OneBot WebSocket 地址
- access token
- cloud-center 地址

运行检查：

```bash
npm run check
```

---

## 示例配置

仓库里保留的是 **示例值**，不是可直接用于生产的真实配置：

- `bridge/bridge_config.example.json`
- `cloud-center/data.example/rooms.example.json`
- `onebots/.env.example`

你部署时需要改成自己的地址、token、AppID、管理员口令等。

---

## 脱敏说明

这个公开目录已经做过整理：

- 已移除构建产物
- 已移除日志文件
- 已移除虚拟环境和 `node_modules`
- 已移除运行时数据
- 已替换真实服务器地址
- 已替换 token / secret / 管理口令
- 已把真实配置改成示例配置

---

## 推荐发布方式

建议把这个目录作为 GitHub 仓库根目录直接上传。

基础流程：

```bash
git init
git add .
git commit -m "Initial commit"
```

如果你后面想把它拆成多仓库，也可以按模块独立：
- `bridge`
- `cloud-center`
- `onebots`

不过当前这种单仓库方式更方便整体维护。

---

## 后续可优化方向

你后面如果继续做，可以考虑补这些：

- 更完整的部署文档
- Docker / Podman 部署方案
- systemd / pm2 托管示例
- GitHub Actions 自动检查
- bridge 一键打包发布脚本
- 更规范的接口文档
- Dashboard 权限控制

---

## 当前状态

- `bridge`：核心链路已整理，可继续完善分发与部署细节
- `cloud-center`：基础汇总与展示链路已具备
- `onebots`：代码与配置样例已整理，但 **QQ / OneBot 实际联调仍未完全跑通**

当前 `onebots` 部分更适合视为：
- 已完成代码框架
- 已完成环境变量与查询逻辑整理
- **待完成平台侧能力配置与最终联调验证**

---

## Known Issues

- `onebots` 模块目前还没有完成真实 QQ 环境下的端到端验证
- QQ 开放平台侧能力、事件订阅、沙箱 / 发布状态都会影响机器人是否真正收到消息
- OneBot 网关进程启动成功，不等于聊天事件一定已经正确流入查询服务
- 当前公开仓库提供的是代码、示例配置和接入框架，不保证开箱即用
