---
name: api-list
description: AiriLab API 工具调用 - MJ 创意渲染 + 超分辨率放大
homepage: https://cn.airilab.com
depends:
  - airi-auth  # 鉴权管理
metadata: { "openclaw": { "emoji": "🎨", "requires": { "bins": ["curl", "python3"] } } }
---

# API List - AiriLab 核心工具调用

> ⚙️ **v2.1 异步架构** - 提交后立即返回，后台自动轮询，完成后主动通知

---

## ⚠️ 重要提示

**使用本技能前，必须启动后台调度器！**

```bash
# 方式 1：测试运行（前台）
python3 ~/.openclaw/skills/api-list/scheduler/worker.py

# 方式 2：后台运行
nohup python3 ~/.openclaw/skills/api-list/scheduler/worker.py > worker.log 2>&1 &

# 方式 3：systemd 服务（推荐，生产环境）
sudo systemctl start airilab-worker
```

**如果调度器未运行：**
- ❌ 任务会一直停留在 `pending` 状态
- ❌ 不会自动轮询和获取结果
- ❌ 用户不会收到完成通知

---

## 🏗️ 完整架构设计

### 三层架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      用户交互层 (Skill)                          │
│  用户说："帮我生成一张建筑图"                                      │
│  ↓                                                              │
│  Skill 调用 submit.py → 获得 job_id → 回复"后台处理中"            │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      脚本层 (scripts/)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  submit.py   │  │check_status.py│  │   fetch.py   │          │
│  │  提交任务    │  │  查询状态    │  │  获取结果    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     调度层 (scheduler/)                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  worker.py - 后台守护进程                                  │   │
│  │  • 每 5 秒轮询 pending 任务                                 │   │
│  │  • 调用 check_status.py 查询状态                          │   │
│  │  • 完成后调用 fetch.py 获取结果                           │   │
│  │  • 推送通知给用户                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  jobs.db - SQLite 数据库                                  │   │
│  │  • 记录所有任务状态                                       │   │
│  │  • 进程重启不丢失任务                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 标准异步流程

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  1. submit.py   │────▶│  2. scheduler/   │────▶│  3. fetch.py    │
│  提交任务       │     │  worker.py       │     │  获取结果       │
│  返回 job_id    │     │  后台轮询        │     │  通知用户       │
└─────────────────┘     └──────────────────┘     └──────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
  立即返回对话             每 5 秒检查状态          推送结果给用户
  "后台处理中"             完成后获取结果
```

### 核心原则

| 原则 | 说明 |
|------|------|
| **单一职责** | 每个脚本只做一件事 |
| **状态持久化** | 所有任务记录到 SQLite |
| **异步处理** | 提交后立即返回，不阻塞 |
| **主动通知** | 完成后推送结果给用户 |

---

## 🛠️ 可用工具

| 工具 | toolsetLv2 | workflowId | 说明 |
|------|-----------|-----------|------|
| **MJ 创意渲染** | `inspire` | `4` | MidJourney 驱动，艺术性概念探索 |
| **基础超分辨率** | `upscale` | `15` | 纯像素放大，内容完全不变 |
| **创意超分辨率** | `upscale` | `15` | AI 增强细节，补充纹理 |

---

## 📜 脚本说明

### scripts/ 目录

| 脚本 | 职责 | 调用时机 | 输入 | 输出 |
|------|------|---------|------|------|
| `submit.py` | 提交任务，返回 job_id | Skill 收到用户请求时 | prompt / image_url | job_id, status |
| `check_status.py` | 查询单次状态 | scheduler 轮询时 | job_id | status (pending/processing/completed/failed) |
| `fetch.py` | 获取最终结果 | 任务完成后 | job_id | output_url, thumbnail_url |

### scheduler/ 目录

| 文件 | 说明 | 是否必需 |
|------|------|---------|
| `worker.py` | 后台轮询守护进程 | ✅ 必需 |
| `airilab-worker.service` | systemd 服务配置 | ✅ 生产环境必需 |
| `jobs.db` | SQLite 数据库（运行时生成） | ✅ 自动生成 |
| `README.md` | 调度器详细文档 | 📖 参考 |

---

## 🔧 调度器详细配置

### 配置参数

| 参数 | 默认值 | 说明 | 修改位置 |
|------|--------|------|---------|
| `POLL_INTERVAL` | `5` 秒 | 轮询间隔 | `worker.py` 第 23 行 |
| `MAX_ATTEMPTS` | `120` 次 | 最大轮询次数（约 10 分钟） | `worker.py` 第 24 行 |
| `DB_PATH` | `scheduler/jobs.db` | 数据库路径 | `worker.py` 第 21 行 |
| `LIMIT` | `50` | 每次最多处理的任务数 | `worker.py` 第 90 行 |

### 数据库结构

```sql
CREATE TABLE jobs (
    job_id TEXT PRIMARY KEY,           -- 任务 ID
    user_id TEXT NOT NULL,             -- 用户 ID
    chat_id TEXT NOT NULL,             -- 聊天 ID（用于通知）
    tool TEXT NOT NULL,                -- 工具类型：'mj' | 'upscale'
    status TEXT DEFAULT 'pending',     -- 状态
    submitted_at TEXT,                 -- 提交时间
    started_at TEXT,                   -- 开始处理时间
    completed_at TEXT,                 -- 完成时间
    input_params TEXT,                 -- 输入参数（JSON）
    output_url TEXT,                   -- 输出 URL
    thumbnail_url TEXT,                -- 缩略图 URL
    error_message TEXT,                -- 错误信息
    attempts INTEGER DEFAULT 0         -- 轮询尝试次数
);

CREATE INDEX idx_status ON jobs(status);
CREATE INDEX idx_user ON jobs(user_id);
```

### 任务状态流转

```
                    ┌─────────────┐
                    │  submitted  │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
          ┌────────│  pending    │────────┐
          │        └──────┬──────┘        │
          │               │               │
          │               ▼               │
          │        ┌─────────────┐        │
          │        │ processing  │        │
          │        └──────┬──────┘        │
          │               │               │
          │               ▼               │
          │        ┌─────────────┐        │
          │        │  completed  │        │
          │        └─────────────┘        │
          │                               │
          └───────▶  failed  ◀────────────┘
                   (超时/API 错误)
```

| 状态 | 触发条件 | 下一步 |
|------|---------|--------|
| `pending` | 任务刚提交 | scheduler 轮询 |
| `processing` | API 返回 processing/sending_now | 继续轮询 |
| `completed` | API 返回 completed | 获取结果 → 通知用户 |
| `failed` | 超时 (120 次) 或 API 错误 | 通知用户，可重试 |

---

## 🚀 使用示例

### 示例 1：提交 MJ 任务

```bash
python3 ~/.openclaw/skills/api-list/scripts/submit.py \
  --tool mj \
  --prompt "现代建筑，玻璃幕墙，黄昏" \
  --style contemporary \
  --aspect-ratio 16:9

# 输出：
# ✅ 任务已提交
# 📋 Job ID: abc123-def456
# 🔧 工具：inspire
# 💡 提示：任务正在后台处理，请等待通知
```

### 示例 2：提交放大任务

```bash
python3 ~/.openclaw/skills/api-list/scripts/submit.py \
  --tool upscale \
  --image-url "https://..." \
  --mode 15  # 15=基础，16=创意

# 输出：
# ✅ 任务已提交
# 📋 Job ID: xyz789-uvw012
# 🔧 工具：upscale
# 💡 提示：任务正在后台处理，请等待通知
```

### 示例 3：手动查询状态

```bash
python3 ~/.openclaw/skills/api-list/scripts/check_status.py \
  --job-id "abc123-def456"

# 输出：
# 📋 Job ID: abc123-def456
# 📊 状态：processing
# ⏰ 时间：2026-03-27T04:20:00
```

### 示例 4：获取结果

```bash
python3 ~/.openclaw/skills/api-list/scripts/fetch.py \
  --job-id "abc123-def456"

# 输出：
# ✅ 获取结果成功
# 📋 Job ID: abc123-def456
# 🖼️  输出 URL: https://...
# 🔧 工具：inspire
```

---

## 🔧 调度器管理

### 启动守护进程

```bash
# 方式 1：手动运行（测试）
python3 ~/.openclaw/skills/api-list/scheduler/worker.py

# 方式 2：后台运行
nohup python3 ~/.openclaw/skills/api-list/scheduler/worker.py > worker.log 2>&1 &

# 方式 3：systemd 服务（推荐）
sudo systemctl start airilab-worker
```

### 查看状态

```bash
# systemd 方式
sudo systemctl status airilab-worker
sudo journalctl -u airilab-worker -f

# 手动方式
ps aux | grep worker.py
tail -f worker.log
```

### 停止服务

```bash
# systemd 方式
sudo systemctl stop airilab-worker

# 手动方式
pkill -f worker.py
```

### 重启服务

```bash
sudo systemctl restart airilab-worker
```

### 查看数据库

```bash
# 查看 pending 任务
sqlite3 ~/.openclaw/skills/api-list/scheduler/jobs.db \
  "SELECT job_id, tool, status, submitted_at FROM jobs WHERE status='pending';"

# 查看最近完成的任务
sqlite3 ~/.openclaw/skills/api-list/scheduler/jobs.db \
  "SELECT job_id, tool, output_url, completed_at FROM jobs WHERE status='completed' ORDER BY completed_at DESC LIMIT 10;"

# 查看失败任务
sqlite3 ~/.openclaw/skills/api-list/scheduler/jobs.db \
  "SELECT job_id, tool, error_message, completed_at FROM jobs WHERE status='failed' ORDER BY completed_at DESC LIMIT 10;"

# 清理 7 天前的旧任务
sqlite3 ~/.openclaw/skills/api-list/scheduler/jobs.db \
  "DELETE FROM jobs WHERE completed_at < datetime('now', '-7 days');"
```

### 日志位置

| 类型 | 位置 | 查看命令 |
|------|------|---------|
| systemd 日志 | journal | `journalctl -u airilab-worker -f` |
| 后台运行日志 | `worker.log` | `tail -f worker.log` |
| 通知日志 | `scheduler/notifications.log` | `cat scheduler/notifications.log` |
| 数据库 | `scheduler/jobs.db` | `sqlite3 scheduler/jobs.db` |

---

## 📊 任务状态

| 状态 | 说明 | 下一步 |
|------|------|--------|
| `pending` | 刚提交，等待处理 | scheduler 轮询 |
| `processing` | 正在处理中 | 继续轮询 |
| `completed` | 已完成 | 通知用户 |
| `failed` | 失败 | 通知用户，可重试 |

---

## 🔐 鉴权集成

### Token 管理

所有脚本都集成了 `airi-auth` 统一鉴权：

```python
from auth_manager import get_auth_manager

auth = get_auth_manager()
auth_result = auth.require_auth(
    skill_name='api-list',
    skill_params=params,
    callback_id=f'api_{time.time()}'
)

if auth_result['status'] == 'pending_auth':
    # Token 无效，已自动触发登录
    return {'success': False, 'message': '请先登录'}

# Token 有效，继续执行
token = auth_result['token']
```

### Token 有效期

- **有效期**: 7 天
- **过期检测**: 每次 API 调用前自动验证
- **自动刷新**: Token 过期时自动触发登录流程
- **备用模式**: auth_manager 不可用时降级读取 `.env`

### Token 存储位置

```bash
# 主 Token 文件
~/.openclaw/skills/api-list/.env

# 内容格式
AIRILAB_API_KEY=eyJhbGci...
AIRILAB_TOKEN_EXPIRES=1775129855708
AIRILAB_PHONE=13113003231
```

---

## ⚠️ 注意事项

### 运行要求

- ⚠️ **调度器必须运行**: 否则任务不会自动处理
- ⚠️ **Token 有效期**: 7 天，过期需重新登录
- ⚠️ **轮询间隔**: 默认 5 秒（可调整）
- ⚠️ **超时时间**: 默认 10 分钟（120 次轮询）
- ⚠️ **并发限制**: 每次最多处理 50 个 pending 任务

### 最佳实践

- ✅ **使用 systemd**: 生产环境推荐用 systemd 管理
- ✅ **定期检查**: 查看失败任务，分析原因
- ✅ **清理旧数据**: 定期清理 7 天前的已完成任务
- ✅ **日志监控**: 监控 worker.log 和 systemd 日志
- ✅ **状态持久化**: 进程重启不丢失任务

### 故障排查

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| 任务一直 pending | 调度器未运行 | 启动 worker.py |
| Token 过期错误 | Token 已过期 | 重新登录 |
| 任务失败 | API 错误或超时 | 查看 error_message，重试 |
| 通知未发送 | 通知逻辑未实现 | 检查 `notify_user()` 函数 |

---

## 📁 目录结构

```
api-list/
├── SKILL.md                 # 技能文档（本文件）
├── CHANGELOG.md             # 变更日志
├── .env                     # Token 配置
│
├── scripts/                 # 脚本层
│   ├── submit.py            # 提交任务
│   ├── check_status.py      # 查询状态
│   └── fetch.py             # 获取结果
│
├── scheduler/               # 调度层
│   ├── worker.py            # 后台守护进程
│   ├── airilab-worker.service  # systemd 配置
│   ├── jobs.db              # SQLite 数据库（运行时生成）
│   ├── notifications.log    # 通知日志（运行时生成）
│   └── README.md            # 调度器详细文档
│
└── references/
    └── tools-catalog.md     # 工具目录
```

---

## 🔗 相关文件

### 依赖技能

| 技能 | 位置 | 用途 |
|------|------|------|
| **airi-auth** | `~/.openclaw/skills/airi-auth/` | 统一鉴权管理 + 登录 |
| **airi-upload** | `~/.openclaw/skills/airi-upload/` | 图片上传（可选） |

### 文档

| 文档 | 位置 |
|------|------|
| 调度器详细文档 | `scheduler/README.md` |
| 变更日志 | `CHANGELOG.md` |
| 工具目录 | `references/tools-catalog.md` |

---

## 📝 更新日志

### v2.1 (2026-03-27) - 鉴权集成 🔐

**新增**:
- ✅ 所有脚本集成 `airi-auth`
- ✅ Token 过期自动触发登录
- ✅ 备用鉴权模式（降级读取 .env）
- ✅ 明确的鉴权错误提示

**更新**:
- ✅ `scripts/submit.py` - 添加鉴权逻辑
- ✅ `scripts/fetch.py` - 添加鉴权逻辑
- ✅ `scripts/check_status.py` - 添加鉴权逻辑
- ✅ `scheduler/worker.py` - 处理鉴权错误

---

### v2.0 (2026-03-27) - 异步架构重构 ⭐

**重大变更**:
- ✅ 重构为异步处理架构
- ✅ 添加 SQLite 状态持久化
- ✅ 添加后台轮询守护进程
- ✅ 脚本职责分离（submit/check_status/fetch）
- ❌ 删除同步阻塞脚本（upscale.py, upscale_complete.py, upscale_async.py）

**新增**:
- ✅ `scripts/submit.py` - 统一提交接口
- ✅ `scripts/check_status.py` - 单次状态查询
- ✅ `scripts/fetch.py` - 结果获取
- ✅ `scheduler/worker.py` - 后台守护进程
- ✅ `scheduler/jobs.db` - SQLite 数据库

---

### v1.0 (2026-03-18) - 初始版本

- ✅ 基础 API 调用功能
- ✅ 支持 MJ 和 Upscale 工具

---

**维护者**: AIRI Lab Team  
**更新日期**: 2026-03-27  
**版本**: v2.1
