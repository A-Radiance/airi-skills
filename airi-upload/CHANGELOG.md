# Changelog - airi-upload Skill

所有重要变更将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

---

## [1.1.0] - 2026-03-27

### 🔒 强依赖策略

#### ✅ 新增
- **强依赖检查**: 启动时检查 airi-auth 是否存在
- **明确错误信息**: 依赖缺失时提供清晰的安装指引
- **无 fallback 策略**: 依赖不存在直接终止

#### 📝 更新
- **scripts/upload_to_s3.py** - 添加强依赖检查，移除备用模式

#### 🔧 技术细节

**强依赖检查**:
```python
AUTH_MANAGER_PATH = Path.home() / '.openclaw' / 'skills' / 'airi-auth'

if not AUTH_MANAGER_PATH.exists():
    print("❌ 致命错误：缺少依赖技能 'airi-auth'")
    print("💡 解决方案：clawhub install airi-auth")
    sys.exit(1)
```

---

## [1.0.0] - 2026-03-26

### 🎉 初始版本

- ✅ 支持图片上传到 S3
- ✅ 支持视频上传
- ✅ 自动 Token 管理
- ✅ 重试机制
