# AiriLab 工具目录（精简版）

> ⚙️ 仅保留 **MJ 创意渲染** 和 **超分辨率放大** 工具

---

## 🎨 创意渲染

### airilab_inspire_MJ

| 属性 | 值 |
|------|------|
| **api_name** | `airilab_inspire_MJ` |
| **toolset_id** | `2` |
| **base_model_ids** | `4` |
| **状态** | ✅ 活跃 |

**功能**: 基于 MidJourney 模型的创意渲染，快速生成建筑效果图

**使用场景**: 从零开始生成创意建筑效果图

**必需参数**: 
- `prompt`: 风格描述文本

**可选参数**: 
- `style`: 风格类型（现代/古典/未来等）
- `aspect_ratio`: 宽高比

**输入文件**: 无

**输出**: 生成的图片

---

## 🔍 超分辨率放大

### basic upscale - 基础放大

| 属性 | 值 |
|------|------|
| **api_name** | `basic upscale` |
| **toolset_id** | `15` |
| **base_model_ids** | `13` |
| **状态** | ✅ 活跃 |

**功能**: 基础超分辨率放大，纯像素放大，内容完全不变

**使用场景**: 放大图片并提升清晰度，保持原始内容

**必需参数**: 
- `input_image`: 输入图片 URL
- `scale_factor`: 放大倍数（2x/4x）

**可选参数**: 
- `width`: 目标宽度
- `height`: 目标高度

**输出**: 放大后的高清图片

---

### creative upscale - 创意放大

| 属性 | 值 |
|------|------|
| **api_name** | `creative upscale` |
| **toolset_id** | `17` |
| **base_model_ids** | `12` |
| **状态** | ✅ 活跃 |

**功能**: 创意超分辨率放大，AI 增强细节，补充纹理

**使用场景**: 创意式放大图片，AI 补充缺失细节

**必需参数**: 
- `input_image`: 输入图片 URL
- `scale_factor`: 放大倍数

**可选参数**: 
- `width`: 目标宽度
- `height`: 目标高度

**输出**: 创意放大后的图片（细节增强）

---

## 📊 放大模式对比

| 模式 | Mode ID | 特点 | 适用场景 |
|------|---------|------|---------|
| **基础超分辨率** | `15` | 纯像素放大，内容不变 | 保持原始设计，仅提升分辨率 |
| **创意超分辨率** | `16` | AI 增强，补充细节 | 需要增强纹理和细节 |

---

## 🛠️ 工具调用方式

### MJ 创意渲染

```python
from generate import build_mj_payload

payload = build_mj_payload(
    prompt="现代建筑，玻璃幕墙，黄昏",
    style="contemporary",
    aspect_ratio="16:9"
)
```

### 超分辨率放大

```python
from generate import build_upscale_payload

payload = build_upscale_payload(
    image_url="https://...",
    mode=15,  # 15=基础，16=创意
    width=1288,
    height=816
)
```

---

## ⚠️ 已弃用工具

以下工具已从本技能包中移除，如需使用请自行恢复：

- ~~物体消除 (eraser_V2)~~
- ~~局部重绘 (edit_V2, CN inpaint_V2)~~
- ~~万物植入 (perfect_replacement)~~
- ~~精模渲染 (detail model rendering)~~
- ~~氛围渲染 (atmosphere swift_V2)~~
- ~~图形风格 (graphic style change)~~
- ~~视频生成 (video)~~
- ~~智能编辑 (smart edit)~~
- ~~其他工具 (partialenhance, angleconversion, extend_V2)~~

---

**维护者**: AIRI Lab Team  
**更新日期**: 2026-03-27  
**版本**: 精简版 v2.0
