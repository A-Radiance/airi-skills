# Changelog - api-list Skill

所有重要变更将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

---

## [2.2.0] - 2026-03-27

### 🔒 强依赖策略

#### ✅ 新增
- **强依赖检查**: 启动时检查 airi-auth 是否存在
- **明确错误信息**: 依赖缺失时提供清晰的安装指引
- **无 fallback 策略**: 依赖不存在直接终止，避免隐藏问题

#### 📝 更新
- **scripts/submit.py** - 添加强依赖检查，移除备用模式
- **scripts/fetch.py** - 添加强依赖检查，移除备用模式
- **scripts/check_status.py** - 添加强依赖检查，移除备用模式
- **scheduler/worker.py** - 添加强依赖检查

#### 🔧 技术细节

**强依赖检查模板**:
```python
AUTH_MANAGER_PATH = Path.home() / '.openclaw' / 'skills' / 'airi-auth'

if not AUTH_MANAGER_PATH.exists():
    print("❌ 致命错误：缺少依赖技能 'airi-auth'")
    print("💡 解决方案：clawhub install airi-auth")
    sys.exit(1)
```

#### ⚠️ 行为变更

| 场景 | v2.1 (旧) | v2.2 (新) |
|------|-----------|-----------|
| airi-auth 未安装 | ⚠️ 降级读取 .env | ❌ 直接终止 |
| auth_manager 导入失败 | ⚠️ 使用备用模式 | ❌ 直接终止 |
| Token 过期 | ⚠️ 尝试备用 Token | ❌ 提示重新登录 |

---

## [2.1.0] - 2026-03-27

### 🔐 鉴权集成

#### ✅ 新增
- **统一鉴权**: 所有脚本集成 `airi-auth`
- **自动刷新**: Token 过期时自动触发登录流程
- **备用模式**: auth_manager 不可用时降级读取 `.env`
- **错误提示**: 鉴权失败时明确提示用户登录

#### 📝 更新
- **scripts/submit.py**: 添加 `require_auth()` 调用
- **scripts/fetch.py**: 添加 `require_auth()` 调用
- **scripts/check_status.py**: 添加 `require_auth()` 调用
- **scheduler/worker.py**: 处理鉴权错误状态

#### 🔧 技术细节
```python
# 所有脚本现在使用统一的鉴权方式
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

---

## [2.0.0] - 2026-03-27

### ⭐ 重大变更 - 异步架构重构

#### 🎯 设计原则
- **单一职责**: 每个脚本只负责一个功能
- **状态持久化**: 所有任务记录到 SQLite 数据库
- **异步处理**: 提交后立即返回，不阻塞用户对话
- **主动通知**: 任务完成后推送结果给用户

#### ✅ 新增
- **scripts/submit.py** - 统一任务提交接口
  - 支持 MJ 创意渲染 (`--tool mj`)
  - 支持超分辨率放大 (`--tool upscale`)
  - 返回 job_id 后立即结束，不轮询
  
- **scripts/check_status.py** - 单次状态查询
  - 查询指定 job_id 的当前状态
  - 不循环、不轮询
  
- **scripts/fetch.py** - 结果获取接口
  - 根据 job_id 获取最终产物
  - 返回 output_url 和 thumbnail_url
  
- **scheduler/worker.py** - 后台轮询守护进程
  - 每 5 秒轮询 pending 任务
  - 自动获取结果并通知用户
  - 支持最大 120 次轮询（10 分钟超时）
  
- **scheduler/jobs.db** - SQLite 数据库
  - 记录所有任务状态
  - 支持进程重启不丢失任务
  
- **scheduler/airilab-worker.service** - systemd 服务配置
  - 生产环境推荐运行方式
  - 自动重启、日志记录

#### ❌ 删除
- `scripts/upscale.py` - 同步阻塞，功能重复
- `scripts/upscale_complete.py` - 同步等待完成
- `scripts/upscale_async.py` - 异步逻辑混乱
- `scripts/generate.py` - 功能分散到 submit.py
- `scripts/api_caller.py` - 已删除
- `scripts/async_manager.py` - 已删除
- `scripts/get_result.py` - 已删除
- `scripts/job_status.py` - 已删除
- `scripts/notify.py` - 已删除
- `scripts/notify_v2.py` - 已删除
- `scripts/poll_and_notify.py` - 已删除
- `ASYNC_USAGE.md` - 文档过期
- `IMPLEMENTATION_SUMMARY.md` - 文档过期

#### 📝 更新
- **SKILL.md** - 完全重写，反映新架构
- **references/tools-catalog.md** - 精简为仅保留 MJ 和 Upscale

#### 🔧 技术细节
- 数据库表结构:
  ```sql
  CREATE TABLE jobs (
      job_id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      chat_id TEXT NOT NULL,
      tool TEXT NOT NULL,
      status TEXT DEFAULT 'pending',
      submitted_at TEXT,
      completed_at TEXT,
      input_params TEXT,
      output_url TEXT,
      thumbnail_url TEXT,
      error_message TEXT,
      attempts INTEGER DEFAULT 0
  );
  ```

- 状态流转:
  ```
  submitted → pending → processing → completed
                              ↘ failed
  ```

#### 📖 使用方式变更

**v1.x (旧)**:
```bash
# 同步等待，阻塞对话
python3 scripts/upscale_complete.py --image-url "..."
# 等待 3-5 分钟...
# 输出结果
```

**v2.0 (新)**:
```bash
# 1. 提交任务（立即返回）
python3 scripts/submit.py --tool upscale --image-url "..."
# ✅ 任务已提交，Job ID: abc123
# 💡 提示：任务正在后台处理，请等待通知

# 2. 后台自动轮询（scheduler/worker.py）
# 3. 完成后推送结果给用户
```

#### 🚀 迁移指南

1. **停止旧进程**:
   ```bash
   pkill -f upscale_complete
   pkill -f upscale_async
   ```

2. **启动新调度器**:
   ```bash
   # 测试运行
   python3 scheduler/worker.py
   
   # 或 systemd 方式
   sudo systemctl start airilab-worker
   ```

3. **更新调用方式**:
   - Skill 层调用 `submit.py` 而非 `upscale_complete.py`
   - 提交后立即返回，提示用户"后台处理中"

---

## [1.0.0] - 2026-03-18

### 🎉 初始版本

#### ✅ 新增
- 基础 API 调用功能
- 支持 MJ 创意渲染
- 支持超分辨率放大（基础/创意）
- 统一使用 `/api/Universal/Generate` 接口
- 三步流程：提交 → 轮询 → 获取结果

#### 📁 文件结构
```
api-list/
├── SKILL.md
├── scripts/
│   ├── generate.py
│   ├── job_status.py
│   ├── get_result.py
│   ├── upscale.py
│   ├── upscale_complete.py
│   └── upscale_async.py
└── references/
    ├── api-reference.md
    └── tools-catalog.md
```

---

## 版本说明

### Semantic Versioning

- **MAJOR** (2.0.0): 不兼容的 API 变更（异步架构重构）
- **MINOR** (x.1.0): 向后兼容的功能新增
- **PATCH** (x.x.1): 向后兼容的问题修复

### 升级建议

- **v1.x → v2.0**: 重大变更，需要更新调用方式和启动调度器
- **v2.0 → v2.x**: 直接升级，向后兼容

---

**维护者**: AIRI Lab Team  
**项目**: api-list Skill  
**仓库**: `~/.openclaw/skills/api-list/`
