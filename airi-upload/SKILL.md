---
name: airi-upload
description: 上传文件到 AiriLab 平台的 AWS S3 存储。支持图片、视频等多种媒体类型。当用户提到「上传图片」「上传文件」「上传到 AiriLab」「S3 上传」等关键词时触发此技能。
homepage: https://cn.airilab.com
metadata: { "openclaw": { "emoji": "📤", "requires": { "bins": ["curl"] } } }
---

# AiriLab Upload - 文件上传技能

上传文件到 AiriLab 平台的 AWS S3 存储，支持图片、视频等多种媒体类型。

## 当使用此技能

✅ **使用此技能当：**

- 用户需要上传图片到 AiriLab 平台
- 用户需要上传视频文件
- 用户需要上传媒体文件到 S3
- 工作流需要文件作为输入

---

## API 端点

```
POST https://cn.airilab.com/api/Workflow/UploadMedia
```

### 视频上传端点

```
POST https://cn.airilab.com/api/GenerateWorkflow/UploadMediaForVideo
```

---

## 请求参数

### Headers

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `Authorization` | string | ✅ | Bearer Token，格式：`Bearer <access_token>` |
| `Content-Type` | string | ✅ | `multipart/form-data`（由 FormData 自动设置） |

### Body (FormData)

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `myFile` | File | ✅ | 要上传的文件 | `upload-1774506213592.jpeg` |
| `imagePart` | string | ✅ | 图片类型/用途标识 | `base-image` |
| `teamId` | number | ✅ | 团队 ID，默认为 0 | `0` 或 `123` |

---

## imagePart 可选值

| 值 | 说明 | 用途 |
|------|------|------|
| `base-image` | 基础图片 | 默认值，普通图片上传 |
| `reference-image` | 参考图 | 用作参考的图片 |
| `mask-image` | 蒙版图 | 用于局部编辑的蒙版 |
| `video-thumbnail` | 视频缩略图 | 视频封面图 |
| `workflow-input` | 工作流输入 | 工作流处理的输入图片 |

---

## 标准调用命令

### 基础图片上传

```bash
curl -X POST "https://cn.airilab.com/api/Workflow/UploadMedia" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "myFile=@/path/to/image.jpg" \
  -F "imagePart=base-image" \
  -F "teamId=0"
```

### 视频上传

```bash
curl -X POST "https://cn.airilab.com/api/GenerateWorkflow/UploadMediaForVideo" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "myFile=@/path/to/video.mp4" \
  -F "imagePart=video-thumbnail" \
  -F "teamId=0"
```

---

## Python 调用示例

```python
import requests

def upload_to_s3(file_path: str, image_part: str = "base-image", team_id: int = 0, token: str = ""):
    """
    上传文件到 AiriLab S3
    
    参数:
        file_path: 文件路径
        image_part: 图片类型 (base-image, reference-image, mask-image, etc.)
        team_id: 团队 ID
        token: AiriLab 访问 Token
    
    返回:
        dict: 上传结果，包含 file_url 等信息
    """
    url = "https://cn.airilab.com/api/Workflow/UploadMedia"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    with open(file_path, 'rb') as f:
        files = {
            'myFile': (file_path.split('/')[-1], f, 'image/jpeg')
        }
        data = {
            'imagePart': image_part,
            'teamId': team_id
        }
        
        response = requests.post(url, headers=headers, files=files, data=data)
        result = response.json()
        
        if result.get("status") == 200:
            return {
                "success": True,
                "data": result.get("data"),
                "file_url": result.get("data", {}).get("fileUrl")
            }
        else:
            return {
                "success": False,
                "error": result.get("message", "Upload failed"),
                "status": result.get("status")
            }

# 使用示例
result = upload_to_s3(
    file_path="/path/to/image.jpg",
    image_part="base-image",
    team_id=0,
    token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
)

print(result)
```

---

## JavaScript 调用示例

```javascript
async function uploadFile(file, imageType = "base-image", teamId = 0, token) {
  const formData = new FormData();
  formData.append("myFile", file, file.name);
  formData.append("imagePart", imageType);
  formData.append("teamId", teamId);
  
  const response = await fetch(
    "https://cn.airilab.com/api/Workflow/UploadMedia",
    {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`
      },
      body: formData
    }
  );
  
  const result = await response.json();
  
  if (result.status === 200) {
    return {
      success: true,
      data: result.data,
      fileUrl: result.data.fileUrl
    };
  } else {
    return {
      success: false,
      error: result.message,
      status: result.status
    };
  }
}
```

---

## 响应结构

### 成功响应 (200)

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "fileUrl": "https://s3.amazonaws.com/airilab-media/...",
    "fileName": "upload-1774506213592.jpeg",
    "fileSize": 102400,
    "fileType": "image/jpeg",
    "uploadedAt": "2026-03-26T04:00:00Z"
  }
}
```

### 错误响应

**401 Unauthorized**
```json
{
  "status": 401,
  "message": "Unauthorized"
}
```

**400 Bad Request (内容审核失败)**
```json
{
  "status": 400,
  "message": "Content moderation failed"
}
```

**403 Forbidden**
```json
{
  "status": 403,
  "message": "Forbidden"
}
```

---

## 错误处理

| 状态码 | 说明 | 处理建议 |
|--------|------|----------|
| 200 | 上传成功 | 返回文件 URL |
| 203 | 临时错误 | 建议重试 |
| 212 | 服务器处理错误 | 检查文件格式 |
| 400 | 请求错误 | 检查参数或内容审核失败 |
| 401 | 未授权 | Token 过期，需要重新登录 |
| 403 | 禁止访问 | 权限不足 |
| 500+ | 服务器错误 | 稍后重试 |

---

## 重试机制

建议实现自动重试逻辑：

```python
def upload_with_retry(file_path, max_retries=2, delay_ms=1000, **kwargs):
    """带重试的上传"""
    for attempt in range(max_retries + 1):
        try:
            result = upload_to_s3(file_path, **kwargs)
            if result["success"]:
                return result
            
            # 可重试的错误
            if result.get("status") >= 500 or result.get("status") in [203, 400]:
                if attempt < max_retries:
                    time.sleep(delay_ms / 1000)
                    continue
            
            return result
        except Exception as e:
            if attempt < max_retries:
                time.sleep(delay_ms / 1000)
                continue
            raise e
    
    return {"success": False, "error": "Max retries exceeded"}
```

---

## 认证（重要）

**需要用户提供 Bearer Token** —— Token 有有效期，过期需重新登录。

### 获取 Token

使用 `airilab-auth` 技能进行登录获取 Token：

```bash
# 先登录获取 Token
python ~/.openclaw/skills/airilab-auth/scripts/login_with_card.py --action start
```

### Token 存储位置

Token 通常存储在：
- `~/.openclaw/skills/api-list/.env` 中的 `AIRILAB_API_KEY`
- 或用户提供的临时 Token

---

## 注意事项

- ✅ **Token 有效期**：Token 有过期时间，失效需重新登录
- ✅ **文件大小**：建议单文件不超过 50MB
- ✅ **支持格式**：JPEG, PNG, WebP, MP4, WebM 等
- ✅ **内容审核**：上传内容会通过审核，违规内容会被拒绝
- ✅ **速率限制**：遵守 API 限流，避免高频调用
- ✅ **安全**：Token 不存储、不记录日志

---

## 与 airilab-auth 集成

上传前自动检查 Token 状态：

```python
from pathlib import Path
import json

def get_auth_token():
    """从 airilab-auth 获取 Token"""
    env_file = Path.home() / '.openclaw' / 'skills' / 'api-list' / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('AIRILAB_API_KEY='):
                    return line.split('=', 1)[1].strip()
    return None

def check_token_expiry():
    """检查 Token 是否过期"""
    state_file = Path.home() / '.openclaw' / 'skills' / 'airilab-auth' / '.auth_state'
    if state_file.exists():
        state = json.loads(state_file.read_text())
        expires_at = state.get('expiresAt', 0)
        import time
        if time.time() * 1000 >= expires_at:
            return False
    return True
```

---

## 快速参考

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `myFile` | ✅ | - | 文件对象 |
| `imagePart` | ✅ | `base-image` | 图片类型 |
| `teamId` | ✅ | `0` | 团队 ID |
| `Authorization` | ✅ | - | Bearer Token |

---

## 相关文件

- 认证技能：`~/.openclaw/skills/airilab-auth/SKILL.md`
- API 调用清单：`~/.openclaw/skills/api-list/SKILL.md`
- Token 配置：`~/.openclaw/skills/api-list/.env`
