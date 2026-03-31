#!/usr/bin/env python3
"""
AiriLab 登录鉴权工具 - 支持飞书交互式卡片
提供手机号验证码登录、Token 管理与存储，以及飞书卡片 UI 支持
"""

import os
import sys
import json
import argparse
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# 配置路径
SKILL_DIR = Path(__file__).parent.parent
API_LIST_DIR = Path.home() / '.openclaw' / 'skills' / 'api-list'
AUTH_STATE_FILE = SKILL_DIR / '.auth_state'
ENV_FILE = API_LIST_DIR / '.env'

# API 端点
SEND_OTP_URL = "https://cn.airilab.com/api/Accounts/Login"
VERIFY_CODE_URL = "https://cn.airilab.com/api/Accounts/Login"

# 请求头模板
DEFAULT_HEADERS = {
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,fr;q=0.8",
    "content-type": "application/json",
    "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


# ==================== 卡片模板 ====================

def build_phone_input_card() -> Dict[str, Any]:
    """构建手机号输入卡片 - Schema 2.0 统一使用中国大陆手机号"""
    return {
        "schema": "2.0",
        "config": {
            "wide_screen_mode": True
        },
        "header": {
            "title": {
                "tag": "plain_text",
                "content": "🔐 AiriLab 登录"
            },
            "template": "blue"
        },
        "body": {
            "elements": [
                {
                    "tag": "markdown",
                    "content": "**请输入手机号登录**\n\n用于接收验证码，首次登录会自动注册账号。"
                },
                {
                    "tag": "input",
                    "placeholder": "请输入 11 位手机号，例如：13113003231",
                    "value": {
                        "action": "submit_phone",
                        "countryCode": "+86"
                    }
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "📱 发送验证码"
                            },
                            "type": "primary",
                            "value": {
                                "action": "send_otp",
                                "countryCode": "+86"
                            }
                        }
                    ]
                },
                {
                    "tag": "markdown",
                    "content": "*当前区号：+86（中国大陆）*"
                }
            ]
        }
    }


def build_country_select_card_with_buttons() -> Dict[str, Any]:
    """构建带按钮的国家选择卡片"""
    # 注意：飞书 Schema 2.0 不支持 action 标签，使用变通方案
    # 让用户直接回复数字或国家代码
    return {
        "schema": "2.0",
        "config": {
            "wide_screen_mode": True
        },
        "header": {
            "title": {
                "tag": "plain_text",
                "content": "🔐 AiriLab 登录"
            },
            "template": "blue"
        },
        "body": {
            "elements": [
                {
                    "tag": "markdown",
                    "content": "**选择国家/地区**\n\n请点击下方快捷选项，或直接输入手机号："
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "━━━━━━━━━━━━━━━━\n🇨🇳 **中国大陆**  `+86`\n   例：13113003231\n━━━━━━━━━━━━━━━━\n🇺🇸 **美国**  `+1`\n   例：2065551234\n━━━━━━━━━━━━━━━━"
                    }
                },
                {
                    "tag": "markdown",
                    "content": "**快捷回复：**\n• 回复 `1` 选择中国大陆\n• 回复 `2` 选择美国\n• 或直接输入完整手机号"
                }
            ]
        }
    }


def build_phone_input_card() -> Dict[str, Any]:
    """构建手机号输入卡片 - Schema 2.0 纯文字引导"""
    # Schema 2.0 不支持 input 标签，改用文字引导
    return {
        "schema": "2.0",
        "config": {
            "wide_screen_mode": True
        },
        "header": {
            "title": {
                "tag": "plain_text",
                "content": "🔐 AiriLab 登录"
            },
            "template": "blue"
        },
        "body": {
            "elements": [
                {
                    "tag": "markdown",
                    "content": "**请输入手机号登录**\n\n用于接收验证码，首次登录会自动注册账号。\n\n━━━━━━━━━━━━━━━━━━\n\n**📱 回复你的 11 位手机号：**\n例：`13113003231`\n\n━━━━━━━━━━━━━━━━━━\n\n*当前区号：+86（中国大陆）*"
                }
            ]
        }
    }


def build_code_input_card(phone: str) -> Dict[str, Any]:
    """构建验证码输入卡片"""
    masked_phone = phone[:3] + "****" + phone[-4:]
    
    return {
        "schema": "2.0",
        "config": {
            "wide_screen_mode": True
        },
        "header": {
            "title": {
                "tag": "plain_text",
                "content": "📲 输入验证码"
            },
            "template": "green"
        },
        "body": {
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**验证码已发送至：{masked_phone}**\n\n请输入 6 位验证码："
                    }
                },
                {
                    "tag": "input",
                    "placeholder": "请输入 6 位验证码",
                    "value": {
                        "action": "submit_code",
                        "phone": phone
                    }
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "✅ 确认登录"
                            },
                            "type": "primary",
                            "value": {
                                "action": "verify_code"
                            }
                        },
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "🔄 重新发送"
                            },
                            "type": "default",
                            "value": {
                                "action": "resend_code",
                                "phone": phone
                            }
                        }
                    ]
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "*验证码有效期 5 分钟，错误次数过多需重新获取*"
                    }
                }
            ]
        }
    }


def build_success_card(phone: str, expires_at: int) -> Dict[str, Any]:
    """构建登录成功卡片"""
    masked_phone = phone[:3] + "****" + phone[-4:]
    expires_date = datetime.fromtimestamp(expires_at / 1000).strftime('%Y-%m-%d')
    
    return {
        "schema": "2.0",
        "config": {
            "wide_screen_mode": True
        },
        "header": {
            "title": {
                "tag": "plain_text",
                "content": "✅ 登录成功！"
            },
            "template": "green"
        },
        "body": {
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**欢迎回来！**\n\n- 手机号：{masked_phone}\n- Token 有效期：7 天\n- 过期时间：{expires_date}\n\n现在可以调用 AiriLab API 了！"
                    }
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "🔑 查看 Token"
                            },
                            "type": "default",
                            "value": {
                                "action": "view_token"
                            }
                        },
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "🚪 退出登录"
                            },
                            "type": "default",
                            "value": {
                                "action": "logout"
                            }
                        }
                    ]
                }
            ]
        }
    }


def build_error_card(error_message: str, phone: Optional[str] = None) -> Dict[str, Any]:
    """构建错误提示卡片"""
    actions = [
        {
            "tag": "button",
            "text": {
                "tag": "plain_text",
                "content": "🔄 重试"
            },
            "type": "primary",
            "value": {
                "action": "retry"
            }
        }
    ]
    
    if phone:
        actions.append({
            "tag": "button",
            "text": {
                "tag": "plain_text",
                "content": "📱 更换手机号"
            },
            "type": "default",
            "value": {
                "action": "change_phone"
            }
        })
    
    return {
        "schema": "2.0",
        "config": {
            "wide_screen_mode": True
        },
        "header": {
            "title": {
                "tag": "plain_text",
                "content": "❌ 操作失败"
            },
            "template": "red"
        },
        "body": {
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**登录过程中遇到问题**\n\n错误信息：{error_message}"
                    }
                },
                {
                    "tag": "action",
                    "actions": actions
                }
            ]
        }
    }


# ==================== 认证功能 ====================

def load_auth_state() -> Dict[str, Any]:
    """加载认证状态"""
    if AUTH_STATE_FILE.exists():
        with open(AUTH_STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"loggedIn": False}


def save_auth_state(state: Dict[str, Any]):
    """保存认证状态"""
    AUTH_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(AUTH_STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def load_env_file() -> Dict[str, str]:
    """加载.env 文件内容"""
    env_vars = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars


def save_to_env(access_token: str, expires_at: int, phone: str):
    """保存 Token 到.env 文件"""
    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    env_vars = load_env_file()
    env_vars['AIRILAB_API_KEY'] = access_token
    env_vars['AIRILAB_TOKEN_EXPIRES'] = str(expires_at)
    env_vars['AIRILAB_PHONE'] = phone
    
    with open(ENV_FILE, 'w', encoding='utf-8') as f:
        f.write("# AiriLab API 凭证配置\n")
        f.write(f"AIRILAB_API_KEY={env_vars['AIRILAB_API_KEY']}\n")
        f.write(f"AIRILAB_TOKEN_EXPIRES={env_vars['AIRILAB_TOKEN_EXPIRES']}\n")
        f.write(f"AIRILAB_PHONE={env_vars['AIRILAB_PHONE']}\n")


def validate_phone(phone: str) -> bool:
    """验证手机号格式"""
    return phone.isdigit() and len(phone) == 11 and phone.startswith('1')


def validate_code(code: str) -> bool:
    """验证验证码格式"""
    return code.isdigit() and len(code) == 6


def send_otp(phone: str, country_code: str = "+86") -> Dict[str, Any]:
    """发送验证码"""
    if not validate_phone(phone):
        return {
            "success": False,
            "error": "手机号格式错误，请输入 11 位数字",
            "card": build_error_card("手机号格式错误，请输入 11 位数字")
        }
    
    payload = {
        "phoneNumber": phone,
        "email": "",
        "isAgreedToTerms": True,
        "role": 2,
        "code": "",
        "countryCode": country_code,
        "countryName": "China",
        "openId": "",
        "language": "chs"
    }
    
    headers = DEFAULT_HEADERS.copy()
    headers["origin"] = "http://localhost:3000"
    headers["referer"] = "http://localhost:3000/"
    
    try:
        response = requests.post(SEND_OTP_URL, headers=headers, json=payload, timeout=30)
        result = response.json()
        
        if result.get("status") == 200 and result.get("message") == "Otp sent":
            user_id = result.get("data")
            
            # 保存临时状态
            state = load_auth_state()
            state["pendingPhone"] = phone
            state["pendingUserId"] = user_id
            state["pendingCountryCode"] = country_code
            save_auth_state(state)
            
            return {
                "success": True,
                "userId": user_id,
                "card": build_code_input_card(phone)
            }
        else:
            error_msg = result.get('message', '未知错误')
            return {
                "success": False,
                "error": error_msg,
                "card": build_error_card(error_msg, phone)
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"网络错误：{str(e)}",
            "card": build_error_card(f"网络错误：{str(e)}", phone)
        }


def verify_code(phone: str, code: str, country_code: str = "+86") -> Dict[str, Any]:
    """校验验证码并获取 Token"""
    if not validate_code(code):
        return {
            "success": False,
            "error": "验证码格式错误，请输入 6 位数字",
            "card": build_error_card("验证码格式错误，请输入 6 位数字", phone)
        }
    
    payload = {
        "phoneNumber": phone,
        "email": "",
        "isAgreedToTerms": True,
        "role": 2,
        "code": code,
        "countryCode": country_code,
        "countryName": "China",
        "openId": "",
        "language": "chs"
    }
    
    headers = DEFAULT_HEADERS.copy()
    headers["origin"] = "https://cn.airilab.com"
    headers["referer"] = "https://cn.airilab.com/stdio/sign-in"
    
    try:
        response = requests.post(VERIFY_CODE_URL, headers=headers, json=payload, timeout=30)
        result = response.json()
        
        if result.get("status") == 200 and result.get("message") == "Success":
            data = result.get("data", {})
            access_token = data.get("accessToken")
            expires_in = data.get("expiresIn", 604800000)
            
            current_time = datetime.now()
            expires_at = int(current_time.timestamp() * 1000) + expires_in
            
            # 保存 Token
            save_to_env(access_token, expires_at, phone)
            
            # 更新认证状态
            state = {
                "loggedIn": True,
                "phone": phone,
                "email": data.get("email", phone),
                "userId": data.get("userId"),
                "expiresAt": expires_at,
                "expiresAtFormatted": datetime.fromtimestamp(expires_at / 1000).strftime('%Y-%m-%d %H:%M:%S')
            }
            save_auth_state(state)
            
            return {
                "success": True,
                "accessToken": access_token,
                "expiresAt": expires_at,
                "card": build_success_card(phone, expires_at)
            }
        else:
            error_msg = result.get('message', '验证码错误')
            return {
                "success": False,
                "error": error_msg,
                "card": build_error_card(error_msg, phone)
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"网络错误：{str(e)}",
            "card": build_error_card(f"网络错误：{str(e)}", phone)
        }


def check_status() -> Dict[str, Any]:
    """检查登录状态"""
    state = load_auth_state()
    
    if not state.get("loggedIn"):
        return {
            "loggedIn": False,
            "card": build_phone_input_card()
        }
    
    expires_at = state.get("expiresAt", 0)
    current_time = int(datetime.now().timestamp() * 1000)
    
    if current_time >= expires_at:
        state["loggedIn"] = False
        save_auth_state(state)
        return {
            "loggedIn": False,
            "expired": True,
            "card": build_phone_input_card()
        }
    
    env_vars = load_env_file()
    token_preview = env_vars.get("AIRILAB_API_KEY", "")[:20] + "..." if env_vars.get("AIRILAB_API_KEY") else "未找到"
    
    return {
        "loggedIn": True,
        "phone": state.get('phone'),
        "expiresAt": expires_at,
        "tokenPreview": token_preview
    }


def logout() -> Dict[str, Any]:
    """登出"""
    save_auth_state({"loggedIn": False})
    
    env_vars = load_env_file()
    if "AIRILAB_API_KEY" in env_vars:
        del env_vars["AIRILAB_API_KEY"]
    if "AIRILAB_TOKEN_EXPIRES" in env_vars:
        del env_vars["AIRILAB_TOKEN_EXPIRES"]
    if "AIRILAB_PHONE" in env_vars:
        del env_vars["AIRILAB_PHONE"]
    
    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ENV_FILE, 'w', encoding='utf-8') as f:
        f.write("# AiriLab API 凭证配置\n")
        f.write("# Token 已清除\n")
    
    return {
        "success": True,
        "card": build_phone_input_card()
    }


def handle_card_action(action: str, value: Dict[str, Any], user_message: Optional[str] = None) -> Dict[str, Any]:
    """
    处理飞书卡片动作
    
    参数:
        action: 动作类型
        value: 按钮的 value 数据
        user_message: 用户输入的内容（输入框内容）
    """
    # 处理用户输入的数字选择
    if user_message and user_message.strip() in ["1", "2"]:
        if user_message.strip() == "1":
            return {
                "success": True,
                "card": build_phone_input_card("+86", "China", "13113003231", 11)
            }
        elif user_message.strip() == "2":
            return {
                "success": True,
                "card": build_phone_input_card("+1", "United States", "2065551234", 10)
            }
    
    if action == "select_country":
        # 用户选择了国家/地区（通过按钮）
        country_code = value.get("countryCode", "+86")
        country_name = value.get("countryName", "China")
        phone_example = value.get("phoneExample", "13113003231")
        phone_length = value.get("phoneLength", 11)
        
        return {
            "success": True,
            "card": build_phone_input_card(country_code, country_name, phone_example, phone_length)
        }
    
    elif action == "change_country":
        # 用户要更换国家，返回国家选择卡片
        return {
            "success": True,
            "card": build_country_select_card()
        }
    
    elif action == "submit_phone" or action == "send_otp":
        # 用户输入手机号或点击发送验证码
        phone = user_message.strip() if user_message else value.get("phone", "")
        country_code = value.get("countryCode", "+86")
        country_name = value.get("countryName", "China")
        return send_otp(phone, country_code)
    
    elif action == "submit_code" or action == "verify_code":
        # 用户输入验证码或点击确认
        code = user_message.strip() if user_message else ""
        state = load_auth_state()
        phone = state.get("pendingPhone", value.get("phone", ""))
        country_code = state.get("pendingCountryCode", "+86")
        return verify_code(phone, code, country_code)
    
    elif action == "resend_code":
        # 重新发送验证码
        phone = value.get("phone", "")
        country_code = value.get("countryCode", "+86")
        return send_otp(phone, country_code)
    
    elif action == "retry":
        # 重试，返回手机号输入卡片
        return {"card": build_phone_input_card()}
    
    elif action == "change_phone":
        # 更换手机号
        return {"card": build_phone_input_card()}
    
    elif action == "view_token":
        # 查看 Token
        state = load_auth_state()
        env_vars = load_env_file()
        masked_phone = state.get("phone", "")[:3] + "****" + state.get("phone", "")[-4:]
        expires_date = datetime.fromtimestamp(state.get("expiresAt", 0) / 1000).strftime('%Y-%m-%d')
        
        return {
            "success": True,
            "message": f"Token: {env_vars.get('AIRILAB_API_KEY', '未找到')}\n过期时间：{expires_date}",
            "card": build_success_card(state.get("phone", ""), state.get("expiresAt", 0))
        }
    
    elif action == "logout":
        # 退出登录
        return logout()
    
    else:
        return {
            "success": False,
            "error": f"未知动作：{action}",
            "card": build_phone_input_card()
        }


# ==================== 命令行入口 ====================

def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="AiriLab 登录鉴权工具（支持飞书卡片）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 发送手机号输入卡片
  python login_with_card.py --action start
  
  # 处理卡片动作（用户点击按钮后）
  python login_with_card.py --action card-action --action-type send_otp --value '{"phone":"13113003231"}' --user-message "13113003231"
  
  # 检查登录状态
  python login_with_card.py --action check-status
  
  # 退出登录
  python login_with_card.py --action logout
        """
    )
    
    parser.add_argument(
        "--action",
        required=True,
        choices=["start", "card-action", "check-status", "logout"],
        help="操作类型"
    )
    parser.add_argument(
        "--action-type",
        help="卡片动作类型（用于 card-action）"
    )
    parser.add_argument(
        "--value",
        help="卡片按钮的 value JSON（用于 card-action）"
    )
    parser.add_argument(
        "--user-message",
        help="用户输入的内容（用于 card-action 的输入框）"
    )
    
    args = parser.parse_args()
    
    if args.action == "start":
        # 开始登录流程，返回手机号输入卡片
        result = {"card": build_phone_input_card()}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    
    elif args.action == "card-action":
        # 处理卡片动作
        if not args.action_type:
            print(json.dumps({"error": "缺少--action-type 参数"}, ensure_ascii=False))
            return 1
        
        value = {}
        if args.value:
            try:
                value = json.loads(args.value)
            except json.JSONDecodeError:
                print(json.dumps({"error": "无效的 JSON 格式"}, ensure_ascii=False))
                return 1
        
        result = handle_card_action(args.action_type, value, args.user_message)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("success", True) else 1
    
    elif args.action == "check-status":
        result = check_status()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("loggedIn", False) else 1
    
    elif args.action == "logout":
        result = logout()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0


if __name__ == "__main__":
    sys.exit(main())
