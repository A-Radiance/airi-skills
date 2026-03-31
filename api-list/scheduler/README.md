# AiriLab 后台轮询调度器

> ⚙️ 守护进程 - 自动处理所有 pending 任务

---

## 📁 目录结构

```
scheduler/
├── worker.py              # 后台轮询守护进程
├── airilab-worker.service # systemd 服务配置
├── jobs.db                # SQLite 数据库（运行时生成）
└── README.md              # 本文档
```

---

## 🚀 快速开始

### 方式 1：手动运行（测试用）

```bash
cd ~/.openclaw/skills/api-list/scheduler
python3 worker.py
```

### 方式 2：后台运行

```bash
nohup python3 ~/.openclaw/skills/api-list/scheduler/worker.py > worker.log 2>&1 &
```

### 方式 3：systemd 服务（推荐，生产环境）

```bash
# 1. 复制服务配置
sudo cp ~/.openclaw/skills/api-list/scheduler/airilab-worker.service /etc/systemd/system/

# 2. 重载 systemd
sudo systemctl daemon-reload

# 3. 启用服务
sudo systemctl enable airilab-worker

# 4. 启动服务
sudo systemctl start airilab-worker

# 5. 查看状态
sudo systemctl status airilab-worker

# 6. 查看日志
sudo journalctl -u airilab-worker -f
```

---

## 🔧 配置说明

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `POLL_INTERVAL` | `5` | 轮询间隔（秒） |
| `MAX_ATTEMPTS` | `120` | 最大轮询次数（约 10 分钟） |

### 数据库结构

```sql
CREATE TABLE jobs (
    job_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    chat_id TEXT NOT NULL,
    tool TEXT NOT NULL,          -- 'mj' | 'upscale'
    status TEXT DEFAULT 'pending',
    submitted_at TEXT,
    started_at TEXT,
    completed_at TEXT,
    input_params TEXT,           -- JSON
    output_url TEXT,
    thumbnail_url TEXT,
    error_message TEXT,
    attempts INTEGER DEFAULT 0
);
```

---

## 📊 任务状态流转

```
submitted → pending → processing → completed
                              ↘ failed
```

| 状态 | 说明 |
|------|------|
| `pending` | 刚提交，等待处理 |
| `processing` | 正在轮询中 |
| `completed` | 已完成，结果已获取 |
| `failed` | 失败（超时或 API 错误） |

---

## 🔍 管理命令

### 查看 pending 任务

```bash
sqlite3 ~/.openclaw/skills/api-list/scheduler/jobs.db \
  "SELECT job_id, tool, status, submitted_at FROM jobs WHERE status='pending';"
```

### 查看最近完成的任务

```bash
sqlite3 ~/.openclaw/skills/api-list/scheduler/jobs.db \
  "SELECT job_id, tool, status, completed_at, output_url FROM jobs WHERE status='completed' ORDER BY completed_at DESC LIMIT 10;"
```

### 清理旧任务

```bash
sqlite3 ~/.openclaw/skills/api-list/scheduler/jobs.db \
  "DELETE FROM jobs WHERE completed_at < datetime('now', '-7 days');"
```

### 重启服务

```bash
sudo systemctl restart airilab-worker
```

### 停止服务

```bash
sudo systemctl stop airilab-worker
```

---

## 📝 日志位置

| 类型 | 位置 |
|------|------|
| systemd 日志 | `journalctl -u airilab-worker` |
| 后台运行日志 | `worker.log` |
| 通知日志 | `scheduler/notifications.log` |
| 数据库 | `scheduler/jobs.db` |

---

## ⚠️ 注意事项

1. **Token 有效期**: 7 天，过期需重新登录
2. **并发限制**: 每次最多处理 50 个 pending 任务
3. **超时处理**: 10 分钟后自动标记为失败
4. **通知机制**: 目前仅记录日志，需集成 OpenClaw 通知 API

---

## 🔗 相关文件

- 提交接口：`../scripts/submit.py`
- 获取结果：`../scripts/fetch.py`
- 查询状态：`../scripts/check_status.py`
- 技能文档：`../SKILL.md`

---

**维护者**: AIRI Lab Team  
**更新日期**: 2026-03-27  
**版本**: v2.0
