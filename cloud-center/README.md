# Cloud Center

[English Version](./README.en.md)


本目录是 **云端汇总服务**。

它负责接收各个本地 bridge 上报的房间状态，并统一提供：
- 房间状态聚合
- 在线 / 离线判断
- Dashboard 网页展示
- 给机器人或其他客户端查询的接口

---

## 功能概览

- 接收 bridge 上报
- 存储当前房间状态
- 输出在线房间列表
- 提供 Dashboard 页面
- 提供 `/rooms` 等接口供机器人调用

---

## 核心规则

当前状态判定思路：
- **心跳发生变化**：视为在线
- **连续 30 秒没有新变化**：视为离线

这个策略比较朴素，但很适合这种“房间状态轮询上报”的场景。

---

## 目录说明

```text
cloud-center/
├─ web/                   # Dashboard 页面资源
├─ server.py              # 旧版本/简化入口
├─ server_std.py          # 当前主服务实现
├─ requirements.txt
└─ data.example/
   └─ rooms.example.json  # 示例房间数据
```

---

## 启动方式

```bash
pip install -r requirements.txt
python server_std.py
```

启动后通常会提供：
- Dashboard 页面
- `/rooms` 查询接口
- `/report` 上报入口

---

## 示例接口

### 读取房间列表

```text
GET /rooms
```

典型返回结构：

```json
{
  "ok": true,
  "rooms": []
}
```

### 接收 bridge 上报

```text
POST /report
```

bridge 会把本地解析出的房间状态发到这里。

---

## Dashboard

cloud-center 自带一个简单 Dashboard，用来直观看当前有哪些房间在线。

如果你后面想继续优化，可以继续加：
- 房主筛选
- 房间人数排序
- 最近更新时间
- 离线原因展示
- 管理权限控制

---

## 示例数据

仓库里保留的是示例数据：

- `data.example/rooms.example.json`

真实运行时数据不要直接提交到公开仓库。

---

## 部署建议

如果你部署到公网，建议额外配：
- Nginx / Caddy 反向代理
- systemd / supervisor 托管
- HTTPS
- 基础鉴权或管理口令

如果只是小范围自用，直接跑也够用。

---

## 与其他模块的关系

- `bridge/` 把状态上报到这里
- `onebots/` 从这里读取在线房间列表

所以它算是整套系统里的中枢。
