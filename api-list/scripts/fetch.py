#!/usr/bin/env python3
"""
AiriLab 结果获取接口

职责：仅负责根据 job_id 获取最终结果
不检查状态、不轮询

标准流程：
1. 确认 job 状态为 completed（由调度层检查）
2. 调用 fetch.py 获取结果
3. 返回产物 URL

鉴权流程：
1. 调用 auth_manager.require_auth() 验证 Token
2. Token 无效时返回错误
3. Token 有效时继续执行

依赖：
- airi-auth (强依赖，必须安装)
"""

import requests
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# ==================== 强依赖检查 ====================

AUTH_MANAGER_PATH = Path.home() / '.openclaw' / 'skills' / 'airi-auth'

if not AUTH_MANAGER_PATH.exists():
    print("❌ 致命错误：缺少依赖技能 'airi-auth'")
    print()
    print("   airi-auth 是 api-list 的强依赖，没有它无法执行任何操作。")
    print()
    print("💡 解决方案：")
    print("   1. 安装 airi-auth 技能:")
    print("      clawhub install airi-auth")
    print()
    sys.exit(1)

sys.path.insert(0, str(AUTH_MANAGER_PATH))

try:
    from auth_manager import get_auth_manager
except ImportError:
    print("❌ 致命错误：无法导入 auth_manager")
    print()
    print("   airi-auth 技能已安装，但 auth_manager.py 无法加载。")
    print()
    print("💡 解决方案：")
    print(f"   检查 airi-auth 技能是否完整：ls -la {AUTH_MANAGER_PATH}/")
    print()
    sys.exit(1)


# ==================== 鉴权函数 ====================

def require_auth() -> dict:
    """要求鉴权"""
    auth = get_auth_manager()
    callback_id = f"api_fetch_{time.time()}"
    auth_result = auth.require_auth(
        skill_name='api-list-fetch',
        skill_params={'action': 'fetch_result'},
        callback_id=callback_id
    )
    
    if auth_result['status'] == 'pending_auth':
        return {
            'success': False,
            'token': None,
            'message': auth_result['message'],
            'help': '请使用以下命令登录：python3 ~/.openclaw/skills/airi-auth/login_with_card.py'
        }
    
    return {
        'success': True,
        'token': auth_result['token'],
        'message': '鉴权通过'
    }
