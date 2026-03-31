# AiriLab Upload - 快速开始指南

## 📤 上传文件到 AiriLab S3

### 前置条件

1. **获取 AiriLab Token**
   - 登录 AiriLab 网站 (https://cn.airilab.com)
   - 从浏览器开发者工具获取 Token
   - 或使用 `airilab-auth` 技能登录

2. **准备要上传的文件**
   - 图片：JPEG, PNG, WebP, GIF
   - 视频：MP4, WebM, MOV
   - 建议单文件不超过 50MB

---

## 🚀 快速使用

### 方式 1：命令行上传

```bash
# 上传图片
python3 ~/.openclaw/skills/airi-upload/scripts/upload_to_s3.py \
  --file /path/to/image.jpg

# 上传视频
python3 ~/.openclaw/skills/airi-upload/scripts/upload_to_s3.py \
  --file /path/to/video.mp4 \
  --is-video

# 指定 Token
python3 ~/.openclaw/skills/airi-upload/scripts/upload_to_s3.py \
  --file /path/to/image.jpg \
  --token "eyJhbGciOiJIUzI1NiIs..."
```

### 方式 2：Python 代码

```python
import sys
sys.path.insert(0, '/home/ec2-user/.openclaw/skills/airi-upload/scripts')

from upload_to_s3 import upload_file

result = upload_file(
    file_path="/path/to/image.jpg",
    image_part="base-image",
    team_id=0
)

if result["success"]:
    print(f"上传成功：{result['file_url']}")
else:
    print(f"上传失败：{result['error']}")
```

### 方式 3：cURL

```bash
curl -X POST "https://cn.airilab.com/api/Workflow/UploadMedia" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "myFile=@/path/to/image.jpg" \
  -F "imagePart=base-image" \
  -F "teamId=0"
```

---

## 📋 imagePart 参数说明

| 值 | 说明 | 用途 |
|------|------|------|
| `base-image` | 基础图片 | 默认值，普通图片上传 |
| `reference-image` | 参考图 | 用作参考的图片 |
| `mask-image` | 蒙版图 | 用于局部编辑的蒙版 |
| `video-thumbnail` | 视频缩略图 | 视频封面图 |
| `workflow-input` | 工作流输入 | 工作流处理的输入图片 |

---

## 🔑 获取 Token

### 从浏览器获取

1. 登录 https://cn.airilab.com
2. 打开浏览器开发者工具 (F12)
3. 进入 **Application** → **Local Storage**
4. 找到 `token` 键，复制值

### 从配置文件获取

```bash
cat ~/.openclaw/skills/api-list/.env | grep AIRILAB_API_KEY
```

### 使用 airilab-auth 登录

```bash
# 启动登录流程
python3 ~/.openclaw/skills/airilab-auth/scripts/login_with_card.py --action start

# 检查登录状态
python3 ~/.openclaw/skills/airilab-auth/scripts/login_with_card.py --action check-status
```

---

## 📊 响应示例

### 成功响应

```json
{
  "success": true,
  "file_url": "https://s3.amazonaws.com/airilab-media/uploads/2026/03/26/image.jpg",
  "data": {
    "fileUrl": "https://s3.amazonaws.com/airilab-media/uploads/2026/03/26/image.jpg",
    "fileName": "upload-1774506213592.jpeg",
    "fileSize": 102400,
    "fileType": "image/jpeg",
    "uploadedAt": "2026-03-26T04:00:00Z"
  },
  "status": 200
}
```

### 错误响应

**Token 过期**
```json
{
  "success": false,
  "error": "Token 已过期，请重新登录",
  "status": 401
}
```

**文件不存在**
```json
{
  "success": false,
  "error": "文件不存在：/path/to/image.jpg",
  "status": 400
}
```

**内容审核失败**
```json
{
  "success": false,
  "error": "Content moderation failed",
  "status": 400
}
```

---

## ⚠️ 常见问题

### Q: 上传失败，错误 401

**A:** Token 过期或无效，请重新登录获取新 Token。

### Q: 上传失败，错误 400

**A:** 可能是：
- 文件格式不支持
- 文件过大（>50MB）
- 内容审核失败

### Q: 上传失败，错误 500

**A:** 服务器错误，请稍后重试或联系支持。

### Q: 如何上传视频？

**A:** 使用 `--is-video` 参数：
```bash
python3 upload_to_s3.py --file video.mp4 --is-video
```

### Q: 如何指定团队？

**A:** 使用 `--team-id` 参数：
```bash
python3 upload_to_s3.py --file image.jpg --team-id 123
```

---

## 🔗 相关文件

- **技能文档**: `~/.openclaw/skills/airi-upload/SKILL.md`
- **上传脚本**: `~/.openclaw/skills/airi-upload/scripts/upload_to_s3.py`
- **使用说明**: `~/.openclaw/skills/airi-upload/README.md`
- **认证技能**: `~/.openclaw/skills/airilab-auth/SKILL.md`

---

## 📞 支持

如有问题，请联系 AiriLab 支持团队或查看文档：
- API 文档：https://cn.airilab.com/api-docs
- 技术支持：support@airilab.com
