# Changelog - airi-auth Skill

所有重要变更将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

---

## [3.1.0] - 2026-03-27

### 🔒 依赖管理增强

#### ✅ 新增
- **DEPENDENCIES.md**: 完整的依赖关系图文档
- **check-dependencies.py**: 依赖检查工具
- **强依赖策略**: 依赖不存在时直接终止，无 fallback

#### 📝 更新
- **SKILL.md**: 添加依赖声明元数据 (`depends` 字段)
- **api-list**: 更新为强依赖检查
- **airi-upload**: 更新为强依赖检查

#### 📊 依赖关系

```
airi-auth 🔐 (基础技能)
    │
    ├─→ api-list 🎨
    ├─→ airi-upload 📤
    ├─→ airilab-magic-prompt ✨
    └─→ airilab-design-pack 🏗️
```

#### 🔧 使用示例

**检查依赖**:
```bash
python3 ~/.openclaw/skills/check-dependencies.py
```

**依赖声明**:
```yaml
---
name: api-list
depends:
  - airi-auth  # 强依赖
---
```

---

## [3.0.0] - 2026-03-27

### ⭐ 重大变更 - 技能整合

整合原有的 `airi-auth-manager` 和 `airilab-auth` 为统一的 `airi-auth` 技能。

#### 🎯 整合原因

1. **逻辑上是一个整体**: Token 管理 + 登录流程本就应该在一起
2. **减少依赖复杂度**: 避免技能间循环依赖
3. **便于维护**: 一个技能一个版本号
4. **简化安装**: 用户只需安装一个技能

#### ✅ 新增

- **统一文档**: SKILL.md 整合了两部分功能说明
- **清晰架构**: 区分"后台鉴权管理"和"用户登录交互"
- **完整示例**: 包含代码示例和 API 详情

#### 📁 文件结构

```
airi-auth/
├── SKILL.md                 # 统一文档
├── auth_manager.py          # 后台鉴权管理（原 airi-auth-manager）
├── login.py                 # 登录 API（原 airilab-auth）
├── login_with_card.py       # 交互式登录（原 airilab-auth）
└── .auth_state              # 登录状态
```

#### 🔄 迁移指南

**从 airi-auth-manager 迁移**:
```python
# 旧：from airi-auth-manager/auth_manager import ...
# 新：
from auth_manager import get_auth_manager

auth = get_auth_manager()
auth_result = auth.require_auth(...)
```

**从 airilab-auth 迁移**:
- 登录流程不变
- 触发词不变
- API 接口不变

#### ⚠️ 破坏性变更

- ❌ 删除 `airi-auth-manager/` 目录
- ❌ 删除 `airilab-auth/` 目录
- ✅ 所有依赖技能需要更新引用路径

---

## [2.0.0] - 2026-03-26 (原 airi-auth-manager)

### 鉴权管理器

#### ✅ 新增

- Token 缓存管理
- API 验证 Token 有效性
- Skill 挂起/恢复机制
- JWT Token 解析
- 单例模式，全局共享

#### 📁 文件结构

```
airi-auth-manager/
├── SKILL.md
├── auth_manager.py
└── .pending_skills.json
```

---

## [1.0.0] - 2026-03-24 (原 airilab-auth)

### 登录技能

#### ✅ 新增

- 手机号验证码登录
- 交互式卡片支持（飞书/WeCom）
- Token 存储和管理
- 登录成功回调

#### 📁 文件结构

```
airilab-auth/
├── SKILL.md
├── scripts/
│   ├── login.py
│   └── login_with_card.py
└── .auth_state
```

---

## 版本说明

### Semantic Versioning

- **MAJOR** (3.0.0): 不兼容的 API 变更（技能整合）
- **MINOR** (x.1.0): 向后兼容的功能新增
- **PATCH** (x.x.1): 向后兼容的问题修复

### 升级建议

- **v2.x → v3.0**: 需要更新依赖路径
- **v1.x → v3.0**: 需要更新依赖路径
- **v3.0 → v3.x**: 直接升级，向后兼容

---

**维护者**: AIRI Lab Team  
**项目**: airi-auth Skill  
**仓库**: `~/.openclaw/skills/airi-auth/`
