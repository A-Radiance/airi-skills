# AiriLab Upload Skill

📤 上传文件到 AiriLab 平台的 AWS S3 存储

## 功能

- ✅ 支持图片上传（JPEG, PNG, WebP, GIF）
- ✅ 支持视频上传（MP4, WebM, MOV）
- ✅ 自动 Token 管理（与 airilab-auth 集成）
- ✅ 自动重试机制
- ✅ 内容审核支持
- ✅ 多种图片类型支持

## 安装

Skill 已位于：`~/.openclaw/skills/airi-upload/`

确保已配置 `airilab-auth` 技能用于认证。

## 快速开始

### 1. 先登录获取 Token

```bash
python3 ~/.openclaw/skills/airilab-auth/scripts/login_with_card.py --action start
```

### 2. 上传文件

```bash
# 基础图片上传
python3 ~/.openclaw/skills/airi-upload/scripts/upload_to_s3.py \
  --file /path/to/image.jpg

# 上传参考图
python3 ~/.openclaw/skills/airi-upload/scripts/upload_to_s3.py \
  --file /path/to/image.jpg \
  --image-part reference-image

# 上传视频
python3 ~/.openclaw/skills/airi-upload/scripts/upload_to_s3.py \
  --file /path/to/video.mp4 \
  --is-video

# 指定团队 ID
python3 ~/.openclaw/skills/airi-upload/scripts/upload_to_s3.py \
  --file /path/to/image.jpg \
  --team-id 123

# JSON 格式输出
python3 ~/.openclaw/skills/airi-upload/scripts/upload_to_s3.py \
  --file /path/to/image.jpg \
  --json
```

## 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--file` | ✅ | - | 要上传的文件路径 |
| `--image-part` | ❌ | `base-image` | 图片类型标识 |
| `--team-id` | ❌ | `0` | 团队 ID |
| `--token` | ❌ | 自动读取 | AiriLab Token |
| `--is-video` | ❌ | `false` | 是否为视频上传 |
| `--max-retries` | ❌ | `2` | 最大重试次数 |
| `--delay-ms` | ❌ | `1000` | 重试间隔（毫秒） |
| `--json` | ❌ | `false` | JSON 格式输出 |

## imagePart 可选值

| 值 | 说明 |
|------|------|
| `base-image` | 基础图片（默认） |
| `reference-image` | 参考图 |
| `mask-image` | 蒙版图 |
| `video-thumbnail` | 视频缩略图 |
| `workflow-input` | 工作流输入 |

## API 端点

- **图片上传**: `POST https://cn.airilab.com/api/Workflow/UploadMedia`
- **视频上传**: `POST https://cn.airilab.com/api/GenerateWorkflow/UploadMediaForVideo`

## 响应示例

### 成功

```json
{
  "success": true,
  "data": {
    "fileUrl": "https://s3.amazonaws.com/airilab-media/...",
    "fileName": "upload-1774506213592.jpeg",
    "fileSize": 102400,
    "fileType": "image/jpeg"
  },
  "file_url": "https://s3.amazonaws.com/airilab-media/...",
  "status": 200
}
```

### 失败

```json
{
  "success": false,
  "error": "Token 已过期，请重新登录",
  "status": 401
}
```

## 错误处理

| 状态码 | 说明 | 解决方案 |
|--------|------|----------|
| 200 | 上传成功 | - |
| 203 | 临时错误 | 自动重试 |
| 400 | 请求错误/内容审核失败 | 检查文件或内容 |
| 401 | 未授权 | 重新登录 |
| 403 | 禁止访问 | 检查权限 |
| 500+ | 服务器错误 | 自动重试 |

## 与 airilab-auth 集成

本技能自动从 `airilab-auth` 读取 Token：

- Token 路径：`~/.openclaw/skills/api-list/.env`
- 状态路径：`~/.openclaw/skills/airilab-auth/.auth_state`

如果 Token 过期，技能会自动提示重新登录。

## Python 库使用

```python
import sys
sys.path.insert(0, '/home/ec2-user/.openclaw/skills/airi-upload/scripts')

from upload_to_s3 import upload_file, upload_with_retry

# 简单上传
result = upload_file(
    file_path="/path/to/image.jpg",
    image_part="base-image",
    team_id=0
)

if result["success"]:
    print(f"上传成功：{result['file_url']}")
else:
    print(f"上传失败：{result['error']}")

# 带重试上传
result = upload_with_retry(
    file_path="/path/to/image.jpg",
    max_retries=3,
    delay_ms=1000
)
```

## 注意事项

- ⚠️ **Token 有效期**：7 天，过期需重新登录
- ⚠️ **文件大小**：建议单文件不超过 50MB
- ⚠️ **内容审核**：违规内容会被拒绝
- ⚠️ **速率限制**：避免高频调用

## 相关文件

- 技能文档：`SKILL.md`
- 上传脚本：`scripts/upload_to_s3.py`
- 认证技能：`~/.openclaw/skills/airilab-auth/SKILL.md`

## 许可证

Internal Use Only - AiriLab
