# Teardown Room Bridge

[English Version](./README.en.md)


本目录是 **本地 bridge 端**，运行在玩家自己的电脑上。

它的职责很简单：
- 从 Teardown 本地状态里读取房间信息
- 整理出房主、人数、玩家列表、在线状态等数据
- 周期性上报到云端 `cloud-center`
- 提供本地 Web UI 方便配置

---

## 功能概览

- 本地 Web 配置页面
- 自动读取房间状态
- 定时上报云端
- 支持打包成独立 exe 分发给群友
- 支持日志输出，方便排错

默认本地页面：

```text
http://127.0.0.1:8787/
```

---

## 目录说明

```text
bridge/
├─ agent/              # bridge 核心逻辑
├─ web/                # 本地配置页面
├─ scripts/            # 启动/打包脚本
├─ packaging/          # 打包相关配置
├─ app.py              # Web 入口
├─ run_bridge.py       # bridge 启动入口
├─ requirements.txt
└─ bridge_config.example.json
```

---

## 运行方式

### 方式一：直接用 Python 运行

```bash
pip install -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8787
```

也可以使用目录里的启动脚本。

启动后浏览器打开：

```text
http://127.0.0.1:8787/
```

---

## 配置说明

公开仓库里保留的是示例配置：

- `bridge_config.example.json`

实际部署时，你需要根据自己的环境填写：
- `clientId`
- `roomLabel`
- `roomCode`
- `cloudEndpoint`
- `pollInterval`
- `uploadInterval`

示例云端地址：

```text
http://your-cloud-center:18080/report
```

---

## 打包为 exe

如果你想发给不懂 Python 的群友，最方便的方式就是打包成 exe。

目录里已经保留了相关脚本，比如：

- `scripts/build_exe.bat`
- `scripts/release_nuitka_venv312.cmd`

打包后的桥接程序适合直接分发给房主使用。

---

## 运行后会做什么

bridge 启动后会：
- 启动本地 Web UI
- 读取 Teardown 房间状态
- 生成结构化状态数据
- 按间隔上报到云端

这样云端就能统一展示哪些房间在线、谁是房主、当前人数多少。

---

## 日志与排错

bridge 设计时保留了日志能力，方便在不同玩家机器上排查：
- 本地页面打不开
- 读不到状态
- 上报失败
- 配置异常

如果你后面要给别人分发，日志会非常有用。

---

## 依赖关系

bridge 依赖云端服务可用，也就是 `cloud-center` 的上报接口和房间状态汇总逻辑。

如果云端没开，bridge 本地仍然可以运行，但状态无法成功上传。

---

## 适用场景

适合：
- 群友开房后自动上报房间状态
- 多个玩家分布式开房
- 想要统一在网页或机器人里查看所有在线房间

