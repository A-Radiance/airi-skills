---
name: airi-auth
description: AiriLab 统一鉴权技能。整合 Token 管理、验证码登录、Skill 挂起/恢复功能。
homepage: https://cn.airilab.com
metadata: { "openclaw": { "emoji": "🔐", "requires": { "bins": ["curl", "python3"] } } }
---

# AiriLab Auth - 统一鉴权技能

> ⚙️ **v3.0 整合版** - 后台鉴权管理 + 用户登录交互，二合一

---

## 📋 技能概述

本技能整合了原有的 `airi-auth-manager` 和 `airilab-auth`，提供完整的鉴权解决方案：

| 模块 | 文件 | 功能 |
|------|------|------|
| **后台鉴权管理** | `auth_manager.py` | Token 缓存、验证、挂起/恢复 |
| **用户登录交互** | `login_with_card.py` | 交互式卡片登录、验证码处理 |
| **登录 API** | `login.py` | 调用 AiriLab 登录 API |

---

## 🏗️ 架构设计

### 两部分功能

```
┌─────────────────────────────────────────────────────────┐
│                  AiriLab Auth Skill                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │  1️⃣ 后台鉴权管理 (auth_manager.py)               │   │
│  │  • Token 缓存管理                                 │   │
│  │  • API 验证 Token 有效性                          │   │
│  │  • Skill 挂起/恢复机制                           │   │
│  │  • 自动触发登录刷新                              │   │
│  │  • JWT Token 解析                                │   │
│  │  • 单例模式，全局共享                            │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │  2️⃣ 用户登录交互 (login_with_card.py)            │   │
│  │  • 发送交互式卡片（飞书/WeCom）                  │   │
│  │  • 手机号验证码获取                              │   │
│  │  • 验证码校验                                    │   │
│  │  • Token 获取与存储                              │   │
│  │  • 登录成功回调 → auth_manager                   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 调用关系

```
┌─────────────────────────────────────────────────────────┐
│  其他 Skills (api-list, airi-upload, etc.)              │
│  需要鉴权时调用 → auth_manager.require_auth()           │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  auth_manager.py (后台鉴权管理)                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │  1. 检查 Token 是否存在                          │   │
│  │  2. 调用 API 验证 Token 有效性                    │   │
│  │  3. Token 无效 → 触发登录流程                    │   │
│  │  4. 挂起当前 Skill，等待登录完成                 │   │
│  │  5. 登录成功后恢复 Skill                         │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  login_with_card.py (用户登录交互)                       │
│  ┌─────────────────────────────────────────────────┐   │
│  │  1. 发送交互式卡片：[输入手机号]                 │   │
│  │  2. 调用 API 发送验证码                          │   │
│  │  3. 发送卡片：[输入验证码]                       │   │
│  │  4. 调用 API 校验验证码，获取 Token              │   │
│  │  5. 保存 Token 到 .env                           │   │
│  │  6. 回调 → auth_manager.on_auth_success()        │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 使用方式

### 方式 1：其他 Skill 调用（后台鉴权）

**在 Skill 代码中集成：**

```python
# 导入鉴权管理器
from auth_manager import get_auth_manager

auth = get_auth_manager()

def execute(params):
    # 要求鉴权
    auth_result = auth.require_auth(
        skill_name='api-list',
        skill_params=params,
        callback_id=f'api_{time.time()}'
    )
    
    if auth_result['status'] == 'pending_auth':
        # Token 无效，已自动触发登录
        return {
            'status': 'pending_auth',
            'message': '请先登录 AiriLab：' + auth_result['message']
        }
    
    # Token 有效，继续执行
    token = auth_result['token']
    return call_api(params, token=token)
```

**完整示例：**

```python
from auth_manager import get_auth_manager
import time

auth = get_auth_manager()

def upload_image(file_path):
    # 1. 要求鉴权
    auth_result = auth.require_auth(
        skill_name='airi-upload',
        skill_params={'file': file_path},
        callback_id=f'upload_{time.time()}'
    )
    
    # 2. 检查鉴权结果
    if auth_result['status'] == 'pending_auth':
        return {
            'status': 'pending',
            'message': '请先登录：' + auth_result['message']
        }
    
    # 3. Token 有效，执行上传
    token = auth_result['token']
    result = upload_to_s3(file_path, token=token)
    
    return result
```

---

### 方式 2：用户主动登录（交互式卡片）

**用户触发：**
```
用户：我要登录 AiriLab
用户：Token 过期了
用户：帮我登录一下
```

**Bot 响应流程：**
```
1. 发送卡片：[选择国家/地区]
   🇨🇳 中国大陆 (+86)
   🇺🇸 美国 (+1)

2. 用户选择后，发送卡片：[输入手机号] + [发送验证码按钮]

3. 用户输入手机号，点击发送
   → 调用 API 发送验证码

4. 发送卡片：[输入验证码] + [确认] + [重发]
   验证码已发送至：131****3231

5. 用户输入验证码，点击确认
   → 调用 API 校验验证码
   → 保存 Token 到 ~/.openclaw/skills/api-list/.env
   → 回调 auth_manager.on_auth_success()
   → 恢复所有挂起的 Skills

6. 发送成功卡片：
   ✅ 登录成功！
   - 手机号：131****3231
   - Token 有效期：7 天
   - 过期时间：2026-04-02
```

---

## 📁 文件结构

```
airi-auth/
├── SKILL.md                    # 本文档
├── auth_manager.py             # 后台鉴权管理器
├── login.py                    # 登录 API 调用
├── login_with_card.py          # 交互式卡片登录
├── .auth_state                 # 登录状态（运行时生成）
└── .env                        # Token 存储（实际在 api-list/.env）
```

---

## 🔐 Token 管理

### Token 存储位置

**主 Token 文件**: `~/.openclaw/skills/api-list/.env`

```bash
# AiriLab API 凭证配置
AIRILAB_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
AIRILAB_TOKEN_EXPIRES=1775129855708
AIRILAB_PHONE=13113003231
```

**登录状态文件**: `~/.openclaw/skills/airi-auth/.auth_state`

```json
{
  "loggedIn": true,
  "phone": "13113003231",
  "email": "13113003231",
  "userId": 22577,
  "expiresAt": 1775129855708,
  "expiresAtFormatted": "2026-04-02 11:37:35"
}
```

### Token 有效期

| 属性 | 值 |
|------|------|
| **有效期** | 7 天（604800000 毫秒） |
| **过期检测** | 每次 API 调用前自动验证 |
| **自动刷新** | Token 过期时自动触发登录 |
| **备用模式** | auth_manager 不可用时降级读取 .env |

### JWT Token 解析

```python
from auth_manager import get_auth_manager

auth = get_auth_manager()
token = auth.get_cached_token()
token_info = auth.get_token_info(token)

# token_info 内容：
{
    'userId': 22577,
    'userName': 'siyn',
    'role': 5,
    'iat': 1774525055,
    'exp': 1775129855,
    'expires_at': datetime(2026, 4, 2, 11, 37, 35)
}
```

---

## 🛠️ API 参考

### AuthManager 核心方法

#### `get_cached_token() -> Optional[str]`

获取本地缓存的 Token

**返回**: Token 字符串，如果没有则返回 `None`

---

#### `save_token(token, phone="", expires_at=0)`

保存 Token 到本地

**参数**:
- `token`: Bearer Token
- `phone`: 手机号（可选）
- `expires_at`: 过期时间戳（可选）

---

#### `check_token_valid(token) -> bool`

通过 API 验证 Token 是否有效

**参数**:
- `token`: 要验证的 Token

**返回**: `True` = 有效，`False` = 无效

---

#### `require_auth(skill_name, skill_params, callback_id, token=None) -> Dict`

要求鉴权（如果 Token 无效则挂起 Skill）

**参数**:
- `skill_name`: Skill 名称
- `skill_params`: Skill 调用参数
- `callback_id`: 回调标识（用于恢复）
- `token`: 可选的 Token（不提供则从缓存读取）

**返回**:
```python
{
    'status': 'ok' | 'pending_auth',
    'token': str | None,
    'message': str
}
```

---

#### `on_auth_success(token, phone="", expires_at=0)`

鉴权成功后的回调（由 login_with_card.py 调用）

**参数**:
- `token`: 新的 Token
- `phone`: 手机号
- `expires_at`: 过期时间戳

---

#### `status() -> Dict`

获取鉴权状态

**返回**:
```python
{
    'logged_in': True,
    'token_valid': True,
    'token_info': {...},
    'pending_count': 0,
    'message': '已登录'
}
```

---

## 🚀 命令行工具

### 查看鉴权状态

```bash
python3 ~/.openclaw/skills/airi-auth/auth_manager.py --action status
```

**输出**:
```json
{
  "logged_in": true,
  "token_valid": true,
  "token_info": {
    "userId": 22577,
    "userName": "siyn",
    "role": 5,
    "exp": 1775129855,
    "expires_at": "2026-04-02 11:37:35"
  },
  "pending_count": 0,
  "message": "已登录"
}
```

---

### 验证 Token

```bash
python3 ~/.openclaw/skills/airi-auth/auth_manager.py \
  --action check-token --token "eyJhbGci..."
```

**输出**:
```
Token ✅ 有效
```

---

### 触发登录

```bash
python3 ~/.openclaw/skills/airi-auth/auth_manager.py \
  --action trigger-login
```

---

### 查看挂起的 Skills

```bash
python3 ~/.openclaw/skills/airi-auth/auth_manager.py \
  --action list-pending
```

**输出**:
```
挂起的 Skills (2):
  - api-list (id=api_1711519200.123)
  - airi-upload (id=upload_1711519201.456)
```

---

## 📊 登录 API 详情

### 1. 发送验证码

**端点**: `POST https://cn.airilab.com/api/Accounts/Login`

**请求体**:
```json
{
  "phoneNumber": "13113003231",
  "email": "",
  "isAgreedToTerms": true,
  "role": 2,
  "code": "",
  "countryCode": "+86",
  "countryName": "China",
  "openId": "",
  "language": "chs"
}
```

**成功响应**:
```json
{
  "status": 200,
  "message": "Otp sent",
  "data": 22577
}
```

---

### 2. 校验验证码（获取 Token）

**端点**: `POST https://cn.airilab.com/api/Accounts/Login`

**请求体**:
```json
{
  "phoneNumber": "13113003231",
  "email": "",
  "isAgreedToTerms": true,
  "role": 2,
  "code": "743065",
  "countryCode": "+86",
  "countryName": "China",
  "openId": "",
  "language": "chs"
}
```

**成功响应**:
```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "email": "13113003231",
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 604800000,
    "firstTime": false,
    "version": "2.2.2.1",
    "chineseLanguage": true
  }
}
```

---

## ⚠️ 注意事项

### 安全

- ⚠️ **Token 保护**: 不要在日志中明文显示完整 Token
- ⚠️ **手机号脱敏**: 显示时使用 `131****3231` 格式
- ⚠️ **敏感文件**: `.env` 和 `.auth_state` 不应提交到版本控制

### 有效期

- ⚠️ **Token 有效期**: 7 天，过期需重新登录
- ⚠️ **验证码有效期**: 5-10 分钟
- ⚠️ **错误重试**: 验证码错误最多 3 次，之后需重新获取

### 多账号

- ✅ **支持切换**: 通过不同手机号登录
- ✅ **自动覆盖**: 新登录会覆盖旧 Token

### 网络错误处理

- ✅ **保守策略**: 网络错误时不阻止执行
- ✅ **降级模式**: auth_manager 不可用时读取 .env

---

## 🔗 依赖技能

| 技能 | 用途 |
|------|------|
| **api-list** | 使用 airi-auth 进行 API 鉴权 |
| **airi-upload** | 使用 airi-auth 进行上传鉴权 |
| **airilab-magic-prompt** | 使用 airi-auth 进行提示词生成鉴权 |

---

## 📝 更新日志

### v3.0 (2026-03-27) - 整合版 ⭐

**重大变更**:
- ✅ 整合 `airi-auth-manager` + `airilab-auth` 为统一技能
- ✅ 简化依赖关系，减少维护成本

**新增**:
- ✅ 统一的 SKILL.md 文档
- ✅ 完整的架构图和调用流程
- ✅ 详细的 API 参考和示例

**文件变更**:
- ✅ `auth_manager.py` - 后台鉴权管理
- ✅ `login.py` - 登录 API 调用
- ✅ `login_with_card.py` - 交互式卡片登录

---

### v2.0 (原 airi-auth-manager) - 鉴权管理器

- ✅ Token 缓存管理
- ✅ API 验证 Token 有效性
- ✅ Skill 挂起/恢复机制
- ✅ JWT Token 解析

---

### v1.0 (原 airilab-auth) - 登录技能

- ✅ 手机号验证码登录
- ✅ 交互式卡片支持
- ✅ Token 存储和管理

---

**维护者**: AIRI Lab Team  
**更新日期**: 2026-03-27  
**版本**: v3.0
