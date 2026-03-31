#!/usr/bin/env python3
"""
AiriLab 登录鉴权工具
支持手机号验证码登录/自动注册，Token 管理与存储
"""

import os
import sys
import json
import argparse
import requests
from pathlib import Path
from datetime import datetime

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
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,fr;q=0.7",
    "content-type": "application/json",
    "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
}


def load_auth_state():
    """加载认证状态"""
    if AUTH_STATE_FILE.exists():
        with open(AUTH_STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"loggedIn": False}


def save_auth_state(state):
    """保存认证状态"""
    AUTH_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(AUTH_STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def load_env_file():
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


def save_to_env(access_token, expires_at, phone):
    """保存 Token 到.env 文件"""
    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # 加载现有内容
    env_vars = load_env_file()
    
    # 更新 Token 相关变量
    env_vars['AIRILAB_API_KEY'] = access_token
    env_vars['AIRILAB_TOKEN_EXPIRES'] = str(expires_at)
    env_vars['AIRILAB_PHONE'] = phone
    
    # 写回文件
    with open(ENV_FILE, 'w', encoding='utf-8') as f:
        f.write("# AiriLab API 凭证配置\n")
        f.write(f"AIRILAB_API_KEY={env_vars['AIRILAB_API_KEY']}\n")
        f.write(f"AIRILAB_TOKEN_EXPIRES={env_vars['AIRILAB_TOKEN_EXPIRES']}\n")
        f.write(f"AIRILAB_PHONE={env_vars['AIRILAB_PHONE']}\n")
    
    print(f"[INFO] Token 已保存到 {ENV_FILE}")


def send_otp(phone: str, country_code: str = "+86"):
    """
    发送验证码
    
    参数:
        phone: 手机号
        country_code: 国家代码（默认 +86）
    """
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
    
    print(f"[INFO] 正在发送验证码到 {country_code}{phone}...")
    
    try:
        response = requests.post(
            SEND_OTP_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        result = response.json()
        print(f"[INFO] API 响应：{json.dumps(result, ensure_ascii=False)}")
        
        if result.get("status") == 200 and result.get("message") == "Otp sent":
            user_id = result.get("data")
            print(f"✅ 验证码已发送！")
            print(f"   用户 ID: {user_id}")
            print(f"   请在 5-10 分钟内输入收到的验证码")
            
            # 保存临时状态
            state = load_auth_state()
            state["pendingPhone"] = phone
            state["pendingUserId"] = user_id
            state["pendingCountryCode"] = country_code
            save_auth_state(state)
            
            return {"success": True, "userId": user_id}
        else:
            print(f"❌ 发送失败：{result.get('message', '未知错误')}")
            return {"success": False, "error": result.get('message', '未知错误')}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络错误：{str(e)}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        print(f"❌ 错误：{str(e)}")
        return {"success": False, "error": str(e)}


def verify_code(phone: str, code: str, country_code: str = "+86"):
    """
    校验验证码并获取 Token
    
    参数:
        phone: 手机号
        code: 验证码
        country_code: 国家代码（默认 +86）
    """
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
    
    print(f"[INFO] 正在校验验证码...")
    
    try:
        response = requests.post(
            VERIFY_CODE_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        result = response.json()
        print(f"[INFO] API 响应：{json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get("status") == 200 and result.get("message") == "Success":
            data = result.get("data", {})
            access_token = data.get("accessToken")
            expires_in = data.get("expiresIn", 604800000)
            user_id = data.get("userId")
            email = data.get("email", phone)
            
            # 计算过期时间戳
            current_time = datetime.now()
            expires_at = int(current_time.timestamp() * 1000) + expires_in
            
            print(f"✅ 登录成功！")
            print(f"   用户：{email}")
            print(f"   Token 有效期：7 天")
            print(f"   过期时间：{datetime.fromtimestamp(expires_at / 1000).strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 保存 Token 到.env 文件
            save_to_env(access_token, expires_at, phone)
            
            # 更新认证状态
            state = {
                "loggedIn": True,
                "phone": phone,
                "email": email,
                "userId": user_id,
                "expiresAt": expires_at,
                "expiresAtFormatted": datetime.fromtimestamp(expires_at / 1000).strftime('%Y-%m-%d %H:%M:%S')
            }
            save_auth_state(state)
            
            # 清理待处理状态
            if "pendingPhone" in state:
                del state["pendingPhone"]
            if "pendingUserId" in state:
                del state["pendingUserId"]
            
            print(f"\n[INFO] Token 已保存，可用于 AiriLab API 调用")
            return {"success": True, "accessToken": access_token, "expiresAt": expires_at}
        else:
            print(f"❌ 验证失败：{result.get('message', '验证码错误')}")
            return {"success": False, "error": result.get('message', '验证码错误')}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络错误：{str(e)}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        print(f"❌ 错误：{str(e)}")
        return {"success": False, "error": str(e)}


def check_status():
    """检查登录状态"""
    state = load_auth_state()
    
    if not state.get("loggedIn"):
        print("❌ 未登录")
        print("   请先执行登录流程：")
        print("   1. python login.py --action send-otp --phone <手机号>")
        print("   2. python login.py --action verify-code --phone <手机号> --code <验证码>")
        return {"loggedIn": False}
    
    expires_at = state.get("expiresAt", 0)
    current_time = int(datetime.now().timestamp() * 1000)
    
    if current_time >= expires_at:
        print("⚠️  Token 已过期")
        print("   请重新登录")
        # 更新状态为未登录
        state["loggedIn"] = False
        save_auth_state(state)
        return {"loggedIn": False, "expired": True}
    
    expires_in_days = (expires_at - current_time) / (1000 * 60 * 60 * 24)
    
    print("✅ 已登录")
    print(f"   手机号：{state.get('phone')}")
    print(f"   用户 ID: {state.get('userId')}")
    print(f"   Token 过期时间：{state.get('expiresAtFormatted')}")
    print(f"   剩余有效期：{expires_in_days:.1f} 天")
    
    # 检查.env 文件
    env_vars = load_env_file()
    if env_vars.get("AIRILAB_API_KEY"):
        token_preview = env_vars["AIRILAB_API_KEY"][:20] + "..."
        print(f"   Token 已配置：{token_preview}")
    else:
        print("   ⚠️  .env 文件中未找到 Token")
    
    return {"loggedIn": True, "expiresInDays": expires_in_days}


def logout():
    """登出"""
    # 清除认证状态
    save_auth_state({"loggedIn": False})
    
    # 清除.env 中的 Token
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
    
    print("✅ 已登出")
    print("   Token 已清除")
    return {"success": True}


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="AiriLab 登录鉴权工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 发送验证码
  python login.py --action send-otp --phone 13113003231
  
  # 校验验证码
  python login.py --action verify-code --phone 13113003231 --code 743065
  
  # 检查登录状态
  python login.py --action check-status
  
  # 登出
  python login.py --action logout
        """
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["send-otp", "verify-code", "check-status", "logout"],
        help="操作类型"
    )
    parser.add_argument("--phone", help="手机号")
    parser.add_argument("--code", help="验证码")
    parser.add_argument("--country-code", default="+86", help="国家代码（默认 +86）")
    
    args = parser.parse_args()
    
    if args.action == "send-otp":
        if not args.phone:
            print("❌ 错误：--phone 参数必需")
            return 1
        result = send_otp(args.phone, args.country_code)
        return 0 if result.get("success") else 1
        
    elif args.action == "verify-code":
        if not args.phone or not args.code:
            print("❌ 错误：--phone 和 --code 参数必需")
            return 1
        result = verify_code(args.phone, args.code, args.country_code)
        return 0 if result.get("success") else 1
        
    elif args.action == "check-status":
        result = check_status()
        return 0 if result.get("loggedIn") else 1
        
    elif args.action == "logout":
        result = logout()
        return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
