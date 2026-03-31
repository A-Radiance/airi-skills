#!/usr/bin/env python3
"""
AiriLab 任务提交接口

职责：仅负责提交任务，返回 job_id
不轮询、不等待、不获取结果

标准流程：
1. 调用 submit.py 提交任务
2. 获得 job_id 后立即返回
3. 由调度层负责后台轮询

鉴权流程：
1. 调用 auth_manager.require_auth() 验证 Token
2. Token 无效时自动挂起并触发登录
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
from dotenv import load_dotenv
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
    print("   2. 或者从 GitHub 克隆:")
    print("      git clone <repo> ~/.openclaw/skills/airi-auth")
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
    print(f"   1. 检查 airi-auth 技能是否完整:")
    print(f"      ls -la {AUTH_MANAGER_PATH}/")
    print()
    print("   2. 重新安装 airi-auth:")
    print("      clawhub install airi-auth --force")
    print()
    sys.exit(1)


# ==================== API 配置 ====================

API_URL = "https://cn.airilab.com/api/Universal/Generate"


# ==================== 鉴权函数 ====================

def require_auth(skill_params: dict) -> dict:
    """
    要求鉴权（封装 auth_manager）
    
    返回:
        {
            'success': bool,
            'token': str | None,
            'message': str,
            'help': str (可选)
        }
    """
    auth = get_auth_manager()
    
    callback_id = f"api_submit_{time.time()}"
    auth_result = auth.require_auth(
        skill_name='api-list',
        skill_params=skill_params,
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


# ==================== Payload 构建函数 ====================

def build_mj_payload(prompt: str, style: str = "contemporary", aspect_ratio: str = "16:9",
                     project_id: int = 130538, team_id: int = 52) -> dict:
    """构建 MJ 创意渲染的 payload"""
    style_map = {"contemporary": 1, "classical": 2, "futuristic": 3, "minimal": 4}
    aspect_map = {"16:9": 1, "4:3": 2, "1:1": 3, "9:16": 4}
    
    return {
        "toolsetEntry": 2,
        "toolsetLv2": "inspire",
        "workflowId": 0,
        "prompt": prompt,
        "styleId": style_map.get(style, 1),
        "aspectRatio": aspect_map.get(aspect_ratio, 1),
        "imageCount": 4,
        "language": "chs",
        "teamId": team_id,
        "projectId": project_id,
        "projectName": "lowcode"
    }


def build_upscale_payload(image_url: str, mode: int = 15, width: int = 1288, height: int = 816,
                          project_id: int = 130538, team_id: int = 52) -> dict:
    """构建超分辨率放大的 payload"""
    return {
        "toolsetEntry": 2,
        "toolsetLv2": "upscale",
        "upscaleMode": mode,
        "baseImage": image_url,
        "workflowId": 15,
        "width": width,
        "height": height,
        "language": "chs",
        "teamId": team_id,
        "projectId": project_id,
        "projectName": "lowcode"
    }


# ==================== 提交函数 ====================

def submit(payload: dict, token: str) -> dict:
    """
    提交生成任务
    
    参数:
        payload: 请求体
        token: Bearer Token
    
    返回:
        {
            "success": bool,
            "job_id": str,
            "tool": str,
            "submitted_at": str,
            "message": str
        }
    """
    headers = {
        "accept": "text/plain",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "authorization": f"Bearer {token}",
        "content-type": "application/json",
        "origin": "https://cn.airilab.com",
        "referer": "https://cn.airilab.com/stdio/workspace/130538",
        "user-agent": "Mozilla/5.0"
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30, verify=False)
        
        if response.status_code == 200:
            result = json.loads(response.text)
            
            if result.get("status") == 200:
                data = result.get("data", {})
                job_id = data.get("jobId")
                workflow = data.get("workflow")
                message = data.get("message", "")
                
                toolset_lv2 = payload.get("toolsetLv2", "unknown")
                
                return {
                    "success": True,
                    "job_id": job_id,
                    "tool": toolset_lv2,
                    "workflow": workflow,
                    "submitted_at": datetime.now().isoformat(),
                    "message": message
                }
            else:
                return {
                    "success": False,
                    "error": result.get('message', 'Unknown error')
                }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "message": response.text[:200]
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e)
        }


# ==================== 快捷提交函数 ====================

def submit_mj(prompt: str, style: str = "contemporary", aspect_ratio: str = "16:9") -> dict:
    """提交 MJ 创意渲染任务"""
    auth_result = require_auth({'tool': 'mj', 'prompt': prompt})
    
    if not auth_result['success']:
        return {
            'success': False,
            'job_id': None,
            'message': auth_result['message'],
            'requires_auth': True,
            'help': auth_result.get('help')
        }
    
    payload = build_mj_payload(prompt, style, aspect_ratio)
    result = submit(payload, auth_result['token'])
    
    if result['success']:
        result['requires_auth'] = False
    else:
        result['requires_auth'] = False
    
    return result


def submit_upscale(image_url: str, mode: int = 15, width: int = 1288, height: int = 816) -> dict:
    """提交超分辨率放大任务"""
    auth_result = require_auth({'tool': 'upscale', 'image_url': image_url})
    
    if not auth_result['success']:
        return {
            'success': False,
            'job_id': None,
            'message': auth_result['message'],
            'requires_auth': True,
            'help': auth_result.get('help')
        }
    
    payload = build_upscale_payload(image_url, mode, width, height)
    result = submit(payload, auth_result['token'])
    
    if result['success']:
        result['requires_auth'] = False
    else:
        result['requires_auth'] = False
    
    return result


# ==================== 命令行入口 ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AiriLab 任务提交接口")
    parser.add_argument("--tool", required=True, choices=["mj", "upscale"], help="工具类型")
    
    # MJ 参数
    parser.add_argument("--prompt", help="MJ 提示词")
    parser.add_argument("--style", default="contemporary", help="MJ 风格")
    parser.add_argument("--aspect-ratio", default="16:9", help="MJ 宽高比")
    
    # Upscale 参数
    parser.add_argument("--image-url", help="放大图片 URL")
    parser.add_argument("--mode", type=int, default=15, help="放大模式：15=基础，16=创意")
    parser.add_argument("--width", type=int, default=1288, help="目标宽度")
    parser.add_argument("--height", type=int, default=816, help="目标高度")
    
    args = parser.parse_args()
    
    # 提交任务
    if args.tool == "mj":
        if not args.prompt:
            print("❌ 错误：MJ 模式需要 --prompt 参数")
            sys.exit(1)
        result = submit_mj(args.prompt, args.style, args.aspect_ratio)
    
    elif args.tool == "upscale":
        if not args.image_url:
            print("❌ 错误：Upscale 模式需要 --image-url 参数")
            sys.exit(1)
        result = submit_upscale(args.image_url, args.mode, args.width, args.height)
    
    # 输出结果
    if result["success"]:
        print("✅ 任务已提交")
        print(f"📋 Job ID: {result['job_id']}")
        print(f"🔧 工具：{result['tool']}")
        print(f"🔗 Workflow: {result['workflow']}")
        print(f"⏰ 时间：{result['submitted_at']}")
        print()
        print("💡 提示：任务正在后台处理，请等待通知")
    else:
        if result.get('requires_auth'):
            print(f"🔐 需要鉴权：{result['message']}")
            if result.get('help'):
                print(result['help'])
        else:
            print(f"❌ 提交失败：{result.get('error', result['message'])}")
        sys.exit(1)
