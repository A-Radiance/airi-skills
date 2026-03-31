#!/usr/bin/env python3
"""
AiriLab 统一鉴权管理器
- 检查 Token 状态
- 自动刷新过期 Token
- 支持 Skill 挂起/恢复
"""

import os
import sys
import json
import time
import requests
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime

# 配置路径
HOME_DIR = Path.home()
OPENCLAW_DIR = HOME_DIR / '.openclaw'
SKILLS_DIR = OPENCLAW_DIR / 'skills'

TOKEN_FILE = SKILLS_DIR / 'api-list' / '.env'
AUTH_STATE_FILE = SKILLS_DIR / 'airilab-auth' / '.auth_state'
PENDING_FILE = SKILLS_DIR / 'airi-auth-manager' / '.pending_skills.json'

# API 端点
GET_USER_API = "https://cn.airilab.com/api/Accounts/GetCurrentUser"


class AuthManager:
    """统一鉴权管理器（单例模式）"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.pending_skills = self._load_pending_skills()
        
        # 日志回调（可选）
        self.log_callback = None
    
    def set_logger(self, callback: Callable[[str], None]):
        """设置日志回调"""
        self.log_callback = callback
    
    def _log(self, message: str, level: str = "INFO"):
        """输出日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] [{level}] {message}"
        
        if self.log_callback:
            self.log_callback(log_msg)
        else:
            print(log_msg)
    
    # ==================== Token 管理 ====================
    
    def get_cached_token(self) -> Optional[str]:
        """获取本地缓存的 Token"""
        if not TOKEN_FILE.exists():
            return None
        
        try:
            with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('AIRILAB_API_KEY='):
                        token = line.split('=', 1)[1].strip()
                        if token:
                            return token
        except Exception as e:
            self._log(f"读取 Token 失败：{e}", "ERROR")
        
        return None
    
    def save_token(self, token: str, phone: str = "", expires_at: int = 0):
        """保存 Token 到本地"""
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
            f.write("# AiriLab API 凭证配置\n")
            f.write(f"AIRILAB_API_KEY={token}\n")
            f.write(f"AIRILAB_TOKEN_EXPIRES={expires_at}\n")
            f.write(f"AIRILAB_PHONE={phone}\n")
        
        self._log("✅ Token 已保存到本地")
    
    def check_token_valid(self, token: str) -> bool:
        """通过 API 验证 Token 是否有效"""
        if not token:
            return False
        
        try:
            response = requests.get(
                GET_USER_API,
                headers={
                    "Authorization": f"Bearer {token}",
                    "accept": "text/plain",
                    "content-type": "application/json"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                self._log("✅ Token 验证通过")
                return True
            elif response.status_code in [401, 403]:
                self._log(f"❌ Token 无效或过期 (HTTP {response.status_code})", "WARN")
                return False
            else:
                self._log(f"⚠️  Token 验证异常 (HTTP {response.status_code})", "WARN")
                return True  # 保守处理
                
        except requests.exceptions.RequestException as e:
            self._log(f"⚠️  Token 验证网络错误：{e}", "WARN")
            return True  # 保守处理，不阻止执行
    
    def get_token_info(self, token: str) -> Optional[Dict]:
        """解析 JWT Token 获取信息"""
        try:
            import base64
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            # 解码 payload
            payload = parts[1]
            payload += '=' * (4 - len(payload) % 4)
            decoded = base64.urlsafe_b64decode(payload)
            data = json.loads(decoded)
            
            return {
                'userId': data.get('userId'),
                'userName': data.get('userName'),
                'role': data.get('role'),
                'iat': data.get('iat'),
                'exp': data.get('exp'),
                'expires_at': datetime.fromtimestamp(data.get('exp', 0)) if data.get('exp') else None
            }
        except Exception as e:
            self._log(f"Token 解析失败：{e}", "ERROR")
            return None
    
    # ==================== 挂起的 Skill 管理 ====================
    
    def _load_pending_skills(self) -> Dict:
        """加载挂起的 Skills"""
        if not PENDING_FILE.exists():
            return {}
        
        try:
            with open(PENDING_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_pending_skills(self):
        """保存挂起的 Skills"""
        PENDING_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PENDING_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.pending_skills, f, indent=2, ensure_ascii=False)
    
    def require_auth(self, 
                     skill_name: str, 
                     skill_params: Dict, 
                     callback_id: str,
                     token: Optional[str] = None) -> Dict[str, Any]:
        """
        要求鉴权（如果 Token 无效则挂起 Skill）
        
        参数:
            skill_name: Skill 名称
            skill_params: Skill 调用参数
            callback_id: 回调标识（用于恢复）
            token: 可选的 Token（不提供则从缓存读取）
        
        返回:
            dict: {
                'status': 'ok' | 'pending_auth',
                'token': str | None,
                'message': str
            }
        """
        # 获取 Token
        if not token:
            token = self.get_cached_token()
        
        if not token:
            self._log(f"⚠️  未找到 Token，挂起 Skill: {skill_name}", "WARN")
            self._pend_skill(skill_name, skill_params, callback_id)
            return {
                'status': 'pending_auth',
                'token': None,
                'message': '未找到 Token，请先登录'
            }
        
        # 验证 Token
        if not self.check_token_valid(token):
            self._log(f"⚠️  Token 无效，挂起 Skill: {skill_name}", "WARN")
            self._pend_skill(skill_name, skill_params, callback_id)
            return {
                'status': 'pending_auth',
                'token': None,
                'message': 'Token 已过期，请重新登录'
            }
        
        # Token 有效
        self._log(f"✅ Token 有效，执行 Skill: {skill_name}")
        return {
            'status': 'ok',
            'token': token,
            'message': '鉴权通过'
        }
    
    def _pend_skill(self, skill_name: str, params: Dict, callback_id: str):
        """挂起 Skill"""
        self.pending_skills[callback_id] = {
            'skill_name': skill_name,
            'params': params,
            'callback_id': callback_id,
            'timestamp': time.time(),
            'created_at': datetime.now().isoformat()
        }
        self._save_pending_skills()
        self._log(f"💤 已挂起 Skill: {skill_name} (id={callback_id})")
    
    def get_pending_skill(self, callback_id: str) -> Optional[Dict]:
        """获取挂起的 Skill"""
        return self.pending_skills.get(callback_id)
    
    def clear_pending_skill(self, callback_id: str):
        """清除挂起的 Skill"""
        if callback_id in self.pending_skills:
            del self.pending_skills[callback_id]
            self._save_pending_skills()
            self._log(f"✅ 已清除挂起的 Skill: {callback_id}")
    
    def list_pending_skills(self) -> List[Dict]:
        """列出所有挂起的 Skills"""
        return list(self.pending_skills.values())
    
    # ==================== 触发鉴权刷新 ====================
    
    def trigger_auth_refresh(self, message: str = "") -> bool:
        """
        触发 airi-auth 刷新流程
        
        参数:
            message: 提示信息（可选）
        
        返回:
            bool: 是否成功触发
        """
        try:
            login_script = SKILLS_DIR / 'airilab-auth' / 'scripts' / 'login_with_card.py'
            
            if not login_script.exists():
                self._log("❌ 找不到登录脚本", "ERROR")
                return False
            
            # 启动登录流程
            self._log("🚀 触发登录流程...")
            subprocess.run([
                'python3', str(login_script),
                '--action', 'start'
            ], check=True)
            
            return True
            
        except subprocess.CalledProcessError as e:
            self._log(f"❌ 触发登录失败：{e}", "ERROR")
            return False
        except Exception as e:
            self._log(f"❌ 触发登录异常：{e}", "ERROR")
            return False
    
    # ==================== 鉴权成功回调 ====================
    
    def on_auth_success(self, token: str, phone: str = "", expires_at: int = 0):
        """
        鉴权成功后的回调（由 airi-auth 调用）
        
        参数:
            token: 新的 Token
            phone: 手机号
            expires_at: 过期时间戳
        """
        self._log("✅ 鉴权成功，保存 Token...")
        
        # 1. 保存 Token
        self.save_token(token, phone, expires_at)
        
        # 2. 恢复所有挂起的 Skills
        if self.pending_skills:
            self._log(f"🔄 恢复 {len(self.pending_skills)} 个挂起的 Skills...")
            
            for callback_id, context in list(self.pending_skills.items()):
                skill_name = context['skill_name']
                self._log(f"  → 恢复：{skill_name} ({callback_id})")
            
            # 注意：实际恢复由各个 Skill 自己处理
            # 这里只负责通知
            
            # 3. 清空挂起队列
            self.pending_skills.clear()
            self._save_pending_skills()
        else:
            self._log("ℹ️  没有挂起的 Skills")
        
        self._log("✅ 鉴权流程完成")
    
    # ==================== 工具函数 ====================
    
    def status(self) -> Dict[str, Any]:
        """获取鉴权状态"""
        token = self.get_cached_token()
        
        if not token:
            return {
                'logged_in': False,
                'message': '未登录'
            }
        
        token_info = self.get_token_info(token)
        is_valid = self.check_token_valid(token)
        
        return {
            'logged_in': True,
            'token_valid': is_valid,
            'token_info': token_info,
            'pending_count': len(self.pending_skills),
            'message': '已登录' if is_valid else 'Token 已过期'
        }


# ==================== 全局单例 ====================

auth_manager = AuthManager()


def get_auth_manager() -> AuthManager:
    """获取全局 AuthManager 实例"""
    return auth_manager


# ==================== 命令行入口 ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AiriLab 鉴权管理器")
    parser.add_argument('--action', required=True, 
                       choices=['status', 'check-token', 'trigger-login', 'list-pending'])
    parser.add_argument('--token', help='Token（用于 check-token）')
    
    args = parser.parse_args()
    
    auth = get_auth_manager()
    
    if args.action == 'status':
        status = auth.status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
    
    elif args.action == 'check-token':
        if not args.token:
            args.token = auth.get_cached_token()
        
        if not args.token:
            print("❌ 未找到 Token")
            sys.exit(1)
        
        is_valid = auth.check_token_valid(args.token)
        print(f"Token {'✅ 有效' if is_valid else '❌ 无效'}")
        sys.exit(0 if is_valid else 1)
    
    elif args.action == 'trigger-login':
        success = auth.trigger_auth_refresh()
        sys.exit(0 if success else 1)
    
    elif args.action == 'list-pending':
        pending = auth.list_pending_skills()
        if pending:
            print(f"挂起的 Skills ({len(pending)}):")
            for item in pending:
                print(f"  - {item['skill_name']} (id={item['callback_id']})")
        else:
            print("没有挂起的 Skills")
