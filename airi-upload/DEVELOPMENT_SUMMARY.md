# AiriLab Skills 开发总结

## 📦 已创建的 Skills

### 1. airi-upload 📤

**位置**: `~/.openclaw/skills/airi-upload/`

**功能**: 上传文件到 AiriLab 平台的 AWS S3 存储

**文件结构**:
```
airi-upload/
├── SKILL.md              # 技能文档（8.7KB）
├── README.md             # 使用说明（4.1KB）
├── QUICKSTART.md         # 快速开始指南（3.5KB）
└── scripts/
    ├── upload_to_s3.py   # 上传脚本（9.3KB）
    └── test_upload.py    # 测试脚本（4.2KB）
```

**核心功能**:
- ✅ 支持图片上传（JPEG, PNG, WebP, GIF）
- ✅ 支持视频上传（MP4, WebM, MOV）
- ✅ 自动 Token 管理（与 airilab-auth 集成）
- ✅ 自动重试机制（最多 2 次）
- ✅ 内容审核支持
- ✅ 多种图片类型支持（base-image, reference-image, mask-image 等）

**API 端点**:
- 图片：`POST https://cn.airilab.com/api/Workflow/UploadMedia`
- 视频：`POST https://cn.airilab.com/api/GenerateWorkflow/UploadMediaForVideo`

**请求参数**:
```python
{
    "myFile": <file>,        # 要上传的文件
    "imagePart": "base-image",  # 图片类型
    "teamId": 0              # 团队 ID
}
```

**使用示例**:
```bash
# 上传图片
python3 ~/.openclaw/skills/airi-upload/scripts/upload_to_s3.py \
  --file /path/to/image.jpg

# 上传视频
python3 ~/.openclaw/skills/airi-upload/scripts/upload_to_s3.py \
  --file /path/to/video.mp4 --is-video

# 测试功能
python3 ~/.openclaw/skills/airi-upload/scripts/test_upload.py
```

---

### 2. airilab-auth 🔐（已更新）

**位置**: `~/.openclaw/skills/airilab-auth/`

**功能**: AiriLab 平台登录鉴权，管理 Token

**更新内容**:
- ✅ 简化为仅支持中国大陆手机号（+86）
- ✅ 使用 Schema 2.0 卡片（完全兼容飞书）
- ✅ 纯文字引导 + 直接输入手机号
- ✅ 自动 Token 存储和管理

**登录流程**:
```
1. 用户输入手机号（11 位）
   ↓
2. 发送验证码（POST /api/Accounts/Login）
   ↓
3. 用户输入验证码
   ↓
4. 验证并获取 Token（POST /api/Accounts/Login）
   ↓
5. 保存 Token 到 ~/.openclaw/skills/api-list/.env
```

**使用示例**:
```bash
# 启动登录
python3 ~/.openclaw/skills/airilab-auth/scripts/login_with_card.py --action start

# 检查状态
python3 ~/.openclaw/skills/airilab-auth/scripts/login_with_card.py --action check-status
```

---

## 📊 测试结果

### airi-upload 测试 ✅

```
✅ Token 检查 - 通过
✅ 文件验证 - 通过
✅ 请求结构 - 通过
✅ 错误处理 - 通过
✅ 重试机制 - 通过
```

### airilab-auth 测试 ⚠️

```
✅ 卡片生成 - 通过（Schema 2.0）
✅ 手机号验证 - 通过
❌ 验证码发送 - API 返回错误（服务器端问题）
```

**问题**: AiriLab API 返回 `Unable to send the otp, Please contact support`

**可能原因**:
1. API 服务暂时不可用
2. 需要特定的请求头
3. 手机号格式或权限问题

**解决方案**: 联系 AiriLab 支持团队或稍后重试

---

## 📝 待测试项目

### 1. 实际上传测试

**前置条件**: 需要有效的 AiriLab Token

**测试步骤**:
```bash
# 1. 获取 Token（从浏览器或 airilab-auth）
# 2. 准备测试文件
# 3. 执行上传
python3 ~/.openclaw/skills/airi-upload/scripts/upload_to_s3.py \
  --file /path/to/test.jpg \
  --token "eyJhbGci..."

# 4. 验证返回结果
# 5. 访问返回的 file_url 确认文件可访问
```

### 2. 完整流程测试

**测试场景**:
1. 用户触发上传请求
2. 自动检查 Token 状态
3. Token 过期 → 引导登录
4. Token 有效 → 执行上传
5. 返回上传结果

---

## 🔧 已知问题

### 1. airilab-auth 验证码发送失败

**错误**: `Unable to send the otp, Please contact support`

**状态**: 待修复

**建议**:
- 联系 AiriLab 支持团队
- 检查 API 文档是否有更新
- 尝试使用现有 Token

### 2. 飞书卡片交互限制

**问题**: Schema 2.0 不支持 `action` 标签和按钮点击事件

**解决方案**: 使用文字引导 + 用户回复数字/文字

---

## 📚 文档清单

| 文档 | 位置 | 说明 |
|------|------|------|
| SKILL.md | `airi-upload/SKILL.md` | 完整技能文档 |
| README.md | `airi-upload/README.md` | 使用说明 |
| QUICKSTART.md | `airi-upload/QUICKSTART.md` | 快速开始指南 |
| 测试脚本 | `airi-upload/scripts/test_upload.py` | 功能测试 |
| 上传脚本 | `airi-upload/scripts/upload_to_s3.py` | 核心实现 |

---

## 🚀 下一步计划

### 优先级 1：修复登录功能

1. 联系 AiriLab 支持，报告验证码发送问题
2. 检查 API 文档，确认请求参数
3. 测试不同的请求头组合
4. 验证手机号格式要求

### 优先级 2：完善上传功能

1. 添加进度条显示
2. 支持批量上传
3. 添加文件类型自动检测
4. 实现断点续传

### 优先级 3：优化用户体验

1. 添加上传历史记录
2. 支持文件管理（删除、重命名）
3. 集成到工作流中
4. 添加上传配额管理

---

## 📞 支持资源

- **API 文档**: https://cn.airilab.com/api-docs
- **技术支持**: support@airilab.com
- **内部文档**: `~/.openclaw/skills/airi-upload/`

---

## 📅 开发时间线

- **2026-03-26**: 创建 airi-upload skill
- **2026-03-26**: 简化 airilab-auth 为仅中国大陆
- **2026-03-26**: 完成文档和测试脚本
- **待定**: 实际上传测试（需要有效 Token）

---

**状态**: ✅ 开发完成，待实际测试
