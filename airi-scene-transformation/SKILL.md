---
name: airi-image-trans
description: 当用户提供已有图片，并希望对其进行风格或场景“修改”、“转换”、“变化”时使用，例如：
- 氛围转换（白天 → 夜晚、晴天 → 雨天）
- 风格变化（写实 → 插画）
- 局部或整体视觉效果修改

  必须满足：
- 用户提供了原始图片

  不要用于：
- 从零生成新图片
- 仅做分辨率提升
---

---

## 鉴权说明

本 Skill 调用 AiriLab API，必须先通过 `airi-auth-manager` 验证Token是否有效

执行流程：
1. 调用 `airi-auth-manager` skill验证Token是否有效
2. 若 Token 无效，调用 `airi-auth-manager` skill登录流程
3. 登录成功后继续执行本 Skill

---

## 完整调用链逻辑 (严格执行)

### Step 1: 向服务器发送用户图片数据
## 输入说明

如果用户提供图片：

1. 先调用 `airi-upload` skill上传图片
2. 获取返回的 `file_url`
3. 将 `file_url` 作为参数传入本 API

**⚠️ 严格要求**
- 记住每张图片对应的的file_url，后续生成任务referenceImage参数需要

### Step 2: 获取projectId和projectName（不可跳过）

1. 先调用 `airi-project` skill上传图片
2. 获取返回的 `teamId和projectId`
3. 将 `teamId和projectId` 作为参数传入本 API

**⚠️ 严格要求**
- step2必须执行以重新获取teamId和projectId，不可跳过
- projectId和teamId需按照airi-project中的描述交由用户选择

### Step 3: 发起生成任务

**端点**: `POST https://cn.airilab.com/api/Universal/Generate`

**请求头**:
```
Authorization: Bearer {TOKEN}
Content-Type: application/json
```

**请求体**:
```json
{
  "toolsetEntry":2,
  "toolsetLv2":"scene",
  "toolsetLv3":"mood",
  "prompt-container":true,
  "exploreReference-container":true,
  "baseImage":"https://airi-production.s3.cn-north-1.amazonaws.com.cn/base-image/dde6871d-da3e-41b2-8d4a-e4a096f40794.jpg",
  "workflowId":13,
  "additionalPrompt":"",
  "referenceImage":[],
  "designLibraryName":"Architecture",
  "designLibraryId":22,
  "firstTierName":"Office",
  "firstTierId":1,
  "secondTierName":"High-rise",
  "secondTierId":1,
  "styleId":1,
  "cameraViewName":"general",
  "cameraViewId":20,
  "graphicStyleId":1,
  "atmosphereId":0,
  "atmosphereType":"",
  "additionalNegativePrompt":"",
  "imageType":"",
  "inputFidelityLevel":0,
  "controlLevel":0,
  "maskImage":"",
  "originalImage":"",
  "initialCNImage":"",
  "horizontalPercentage":0,
  "verticalPercentage":0,
  "firstFrame":"",
  "imageTail":"",
  "videoPrompt":0,
  "timeLapse":0,
  "cameraSpeed":0,
  "prompt":"",
  "privateModel":"",
  "height":1304,
  "width":1736,
  "angleIndex":0,
  "imageCount":1,
  "language":"en",
  "teamId":0,
  "projectId":123,
  "projectName":""
}
```
**⚠️ 严格要求**
- 不能加上任何没有出现在上面请求体格式中的参数
- 请求体必须严格按照上述格式来写

**关键参数说明**:
| 参数 | 说明 | 默认值或示例 |
|------|------|--------|
| `prompt` | 用户描述（必填） | - |
| `additionalPrompt` | 用户描述（必填） | - |
| `projectId` | 填写上面获取到的projectId | - |
| `projectName` | 填写上面获取到的projectName | - |
| `baseImage` | 用户发送的第1张图片或者指定的基图 | "https://airi-production.s3.cn-north-1.amazonaws.com.cn/base-image/371b8a1b-3e79-48a5-99e5-2d1db6cbd46e.jpg" |
| `referenceImage` | 用户发送的第2张图片或者指定的风格参考图片 | [{"url":"https://airi-production.s3.cn-north-1.amazonaws.com.cn/base-image/371b8a1b-3e79-48a5-99e5-2d1db6cbd46e.jpg","type":0}] |


**返回示例**:
```json
{
  "status": 200,
  "message": "Generation request accepted",
  "data": {
    "jobId": "2aacccf9-f2e8-4225-adf2-f08f28206726",
    "workflow": "0",
    "userId": 1557,
    "message": "Your generation has been queued. You will receive updates via WebSocket at /universalSocket"
  }
}
```

**Action**: 提取 `data.jobId` 用于后续查询

---

### Step 4: 轮询获取生成结果

**端点**: `POST https://cn.airilab.com/api/CrudRouters/getOneRecord`

**请求头**:
```
Authorization: Bearer {TOKEN}
Content-Type: application/json
```

**请求体**:
```json
{
  "projectId": 5033,
  "teamId": 0,
  "language": "chs",
  "desiredGenerationId": "<jobId>"
}
```

⚠️ **重要**: `projectId` 和 `teamId` 必须与 Generate 请求中的一致！

**轮询逻辑**:
- 每隔 **2~3 秒** 请求一次
- 不要超过20次轮询
- 检查 `projectGenerationModel` 字段是否有内容

**返回示例**:
```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "projectGenerationModel": [
      {
        "projectMedias": [
          {
            "url": "https://airi-production.s3.cn-north-1.amazonaws.com.cn/devenv/22894739-0d25-421f-ae16-18fa01226444-3.jpg"
          }
        ]
      }
    ]
  }
}
```

---

### Step 5: 展示图片

从返回结果中提取图片 URL：
```
data.projectGenerationModel[].projectMedias[].url
```

通过相对应的聊天软件API直接将图片发送给用户，同时还要附上链接

```
✅ 图片生成完成！

[图片]

生成描述：<用户的原始描述>
耗时：<生成用时>
Job ID: <jobId>
```

---

## 错误处理

| 错误类型 | 错误信息 | 处理方式 |
|----------|----------|----------|
| 参数缺失 | Parameters missing | 检查 designLibraryId、firstTierId 等配置 |
| 网络错误 | Connection refused | 重试 3 次，失败则报错 |
| 生成失败 | status=failed | 告知用户并建议修改描述重试 |
| 轮询超时 | 20 次未完成 | 告知用户任务可能卡住，提供 jobId |
| 结果为空 | projectMedias=[] | 告知用户生成结果为空 |

## 使用示例

### 示例 1: 简单生成

**用户**: 帮我生成一张现代高层办公楼的效果图

**执行流程**:
1. 提取描述："现代高层办公楼的效果图"
2. 调用 Generate 接口 → 获取 jobId
3. 轮询 Job 状态（每 3 秒）
4. 状态=completed 后调用 getOneRecord
5. 发送图片给用户

---

### 示例 2: 带详细参数

**用户**: 生成一个室内设计的图片，要温馨的风格，暖色调

**执行流程**:
1. 提取描述："室内设计的图片，要温馨的风格，暖色调"
2. 可选：调整 designLibraryId 为室内设计对应的 ID
3. 执行完整调用链
4. 返回结果

---

## 调试指南

### 问题：Parameters missing

**可能原因**:
1. designLibraryId、firstTierId、secondTierId 组合无效
2. workflowId 配置错误
3. 缺少必填字段

**解决方案**:
1. 联系管理员获取有效的配置 ID 列表
2. 使用 Web 界面生成一次，查看网络请求
3. 尝试最小化参数请求

### 问题：任务一直 sending_now

**可能原因**:
1. 服务器负载高
2. 任务队列堵塞

**解决方案**:
1. 延长轮询时间至 5 分钟
2. 检查账户额度是否充足

---

## 注意事项

1. **TOKEN 安全**: 不要将 TOKEN 暴露在日志或公开场合
2. **异步生成**: 生成是异步的，通常需要 30 秒~2 分钟
3. **轮询间隔**: 严格遵守 2~3 秒间隔，避免频繁请求被限流
4. **端口切换**: getOneRecord 使用端口 58105，不是 58129
5. **结果提取**: 确保正确解析嵌套的 `projectGenerationModel[].projectMedias[].url`
6. **额度限制**: 检查账户生成额度，避免超限

---

## 相关文件

- 配置位置：`~/.openclaw/workspace/TOOLS.md`
- 技能位置：`~/.openclaw/skills/airi-scene-transformation`

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0 | 2026-03-20 | 初始版本，基于官方文档 |