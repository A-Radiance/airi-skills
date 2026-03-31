#!/usr/bin/env python3
"""
AiriLab S3 文件上传工具
支持图片、视频等多种媒体类型上传到 AWS S3

集成 airi-auth-manager 实现自动鉴权
"""

import os
import sys
import json
import time
import requests
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

# 导入 AuthManager
sys.path.insert(0, str(Path.home() / '.openclaw' / 'skills' / 'airi-auth-manager'))
from auth_manager import get_auth_manager

# 配置
BASE_URL = "https://cn.airilab.com"
UPLOAD_ENDPOINT = "/api/Workflow/UploadMedia"
VIDEO_UPLOAD_ENDPOINT = "/api/GenerateWorkflow/UploadMediaForVideo"

# Token 存储路径
API_LIST_DIR = Path.home() / '.openclaw' / 'skills' / 'api-list'
ENV_FILE = API_LIST_DIR / '.env'
AUTH_STATE_FILE = Path.home() / '.openclaw' / 'skills' / 'airilab-auth' / '.auth_state'


def get_auth_token() -> Optional[str]:
    """从 airilab-auth 获取 Token"""
    # 尝试从.env 文件读取
    if ENV_FILE.exists():
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('AIRILAB_API_KEY='):
                    return line.split('=', 1)[1].strip()
    
    # 尝试从认证状态文件读取
    if AUTH_STATE_FILE.exists():
        with open(AUTH_STATE_FILE, 'r', encoding='utf-8') as f:
            state = json.load(f)
            if state.get('loggedIn'):
                # 需要重新读取.env 文件获取实际 token
                pass
    
    return None


def check_token_expiry() -> bool:
    """检查 Token 是否过期（已废弃，改用 API 验证）"""
    # 这个方法不再使用，改为 validate_token_by_api()
    return True


def validate_token_by_api(token: str) -> bool:
    """
    通过 API 调用验证 Token 是否有效
    
    参数:
        token: Bearer Token
    
    返回:
        bool: True 表示 Token 有效，False 表示无效或过期
    """
    url = "https://cn.airilab.com/api/Accounts/GetCurrentUser"
    headers = {
        "Authorization": f"Bearer {token}",
        "accept": "text/plain",
        "content-type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        # 200 表示 Token 有效
        if response.status_code == 200:
            return True
        
        # 401/403 表示 Token 无效或过期
        elif response.status_code in [401, 403]:
            print(f"[WARN] Token 验证失败：HTTP {response.status_code}")
            return False
        
        # 其他错误可能是网络问题
        else:
            print(f"[WARN] Token 验证请求异常：HTTP {response.status_code}")
            return True  # 保守处理，不阻止上传
            
    except requests.exceptions.RequestException as e:
        print(f"[WARN] Token 验证网络错误：{str(e)}")
        return True  # 保守处理，不阻止上传


def upload_file(
    file_path: str,
    image_part: str = "base-image",
    team_id: int = 0,
    token: Optional[str] = None,
    is_video: bool = False
) -> Dict[str, Any]:
    """
    上传文件到 AiriLab S3
    
    参数:
        file_path: 文件路径
        image_part: 图片类型 (base-image, reference-image, mask-image, video-thumbnail, etc.)
        team_id: 团队 ID
        token: AiriLab 访问 Token（可选，不提供则自动从配置文件读取）
        is_video: 是否为视频上传
    
    返回:
        dict: 上传结果
            - success: bool
            - data: dict (上传成功时的数据)
            - file_url: str (文件 URL)
            - error: str (失败时的错误信息)
            - status: int (HTTP 状态码)
    """
    # 获取 Token
    if not token:
        token = get_auth_token()
        if not token:
            return {
                "success": False,
                "error": "未找到认证 Token，请先登录 AiriLab",
                "status": 401
            }
    
    # 验证 Token 是否有效（通过 API 调用）
    # print(f"[INFO] 正在验证 Token...")  # 静默验证，减少输出
    if not validate_token_by_api(token):
        return {
            "success": False,
            "error": "Token 无效或已过期，请重新登录",
            "status": 401
        }
    # print(f"[INFO] ✅ Token 验证通过")
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return {
            "success": False,
            "error": f"文件不存在：{file_path}",
            "status": 400
        }
    
    # 确定端点
    endpoint = VIDEO_UPLOAD_ENDPOINT if is_video else UPLOAD_ENDPOINT
    url = f"{BASE_URL}{endpoint}"
    
    # 准备文件
    file_name = os.path.basename(file_path)
    file_ext = os.path.splitext(file_name)[1].lower()
    
    # 确定 MIME 类型
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.webp': 'image/webp',
        '.gif': 'image/gif',
        '.mp4': 'video/mp4',
        '.webm': 'video/webm',
        '.mov': 'video/quicktime'
    }
    mime_type = mime_types.get(file_ext, 'application/octet-stream')
    
    # 准备请求
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    with open(file_path, 'rb') as f:
        files = {
            'myFile': (file_name, f, mime_type)
        }
        data = {
            'imagePart': image_part,
            'teamId': team_id
        }
        
        # print(f"[INFO] 正在上传文件：{file_name}")  # 静默上传，减少输出
        # print(f"[INFO] 类型：{image_part}")
        # print(f"[INFO] 大小：{os.path.getsize(file_path) / 1024:.2f} KB")
        # print(f"[INFO] 端点：{url}")
        
        try:
            response = requests.post(url, headers=headers, files=files, data=data, timeout=60)
            result = response.json()
            
            # print(f"[INFO] 响应状态：{result.get('status')}")  # 静默处理
            
            if result.get("status") == 200:
                data = result.get("data", {})
                # API 返回的字段是 path 而不是 fileUrl
                file_url = data.get("fileUrl") or data.get("path", "")
                
                # print(f"[INFO] ✅ 上传成功！")  # 静默处理
                # print(f"[INFO] 文件 URL: {file_url}")
                
                return {
                    "success": True,
                    "data": data,
                    "file_url": file_url,
                    "status": 200
                }
            else:
                error_msg = result.get("message", "上传失败")
                status = result.get("status", response.status_code)
                
                # print(f"[ERROR] ❌ 上传失败：{error_msg}")  # 静默处理
                return {
                    "success": False,
                    "error": error_msg,
                    "status": status
                }
                
        except requests.exceptions.RequestException as e:
            error_msg = f"网络错误：{str(e)}"
            # print(f"[ERROR] ❌ {error_msg}")  # 静默处理
            return {
                "success": False,
                "error": error_msg,
                "status": 0
            }
        except Exception as e:
            error_msg = f"错误：{str(e)}"
            # print(f"[ERROR] ❌ {error_msg}")  # 静默处理
            return {
                "success": False,
                "error": error_msg,
                "status": 0
            }


def upload_with_retry(
    file_path: str,
    max_retries: int = 2,
    delay_ms: int = 1000,
    **kwargs
) -> Dict[str, Any]:
    """
    带重试的上传
    
    参数:
        file_path: 文件路径
        max_retries: 最大重试次数
        delay_ms: 重试间隔（毫秒）
        **kwargs: 传递给 upload_file 的其他参数
    
    返回:
        dict: 上传结果
    """
    last_result = None
    
    for attempt in range(max_retries + 1):
        try:
            result = upload_file(file_path, **kwargs)
            
            if result["success"]:
                return result
            
            # 可重试的错误
            status = result.get("status", 0)
            is_retryable = status >= 500 or status in [203, 0]  # 服务器错误或网络错误
            
            if is_retryable and attempt < max_retries:
                print(f"[WARN] 上传失败，{delay_ms}ms 后重试 ({attempt + 1}/{max_retries})...")
                time.sleep(delay_ms / 1000)
                last_result = result
                continue
            
            return result
            
        except Exception as e:
            if attempt < max_retries:
                print(f"[WARN] 发生错误，{delay_ms}ms 后重试 ({attempt + 1}/{max_retries}): {str(e)}")
                time.sleep(delay_ms / 1000)
                continue
            raise e
    
    return last_result or {
        "success": False,
        "error": "Max retries exceeded",
        "status": 0
    }


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="AiriLab S3 文件上传工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 上传基础图片
  python upload_to_s3.py --file /path/to/image.jpg
  
  # 上传参考图
  python upload_to_s3.py --file /path/to/image.jpg --image-part reference-image
  
  # 上传视频
  python upload_to_s3.py --file /path/to/video.mp4 --is-video
  
  # 指定团队 ID
  python upload_to_s3.py --file /path/to/image.jpg --team-id 123
  
  # 带重试上传
  python upload_to_s3.py --file /path/to/image.jpg --max-retries 3
        """
    )
    
    parser.add_argument(
        "--file",
        required=True,
        help="要上传的文件路径"
    )
    parser.add_argument(
        "--image-part",
        default="base-image",
        help="图片类型 (default: base-image)"
    )
    parser.add_argument(
        "--team-id",
        type=int,
        default=0,
        help="团队 ID (default: 0)"
    )
    parser.add_argument(
        "--token",
        help="AiriLab Token（不提供则从配置文件读取）"
    )
    parser.add_argument(
        "--is-video",
        action="store_true",
        help="是否为视频上传"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="最大重试次数 (default: 2)"
    )
    parser.add_argument(
        "--delay-ms",
        type=int,
        default=1000,
        help="重试间隔毫秒数 (default: 1000)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出结果"
    )
    
    args = parser.parse_args()
    
    # 执行上传
    result = upload_with_retry(
        file_path=args.file,
        image_part=args.image_part,
        team_id=args.team_id,
        token=args.token,
        is_video=args.is_video,
        max_retries=args.max_retries,
        delay_ms=args.delay_ms
    )
    
    # 输出结果
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        if result["success"]:
            file_url = result['file_url']
            width = result['data'].get('width', '')
            height = result['data'].get('height', '')
            
            # 构建 Markdown 格式输出（支持飞书渲染图片）
            output = f"\n✅ 上传成功！\n\n"
            output += f"![上传的图片]({file_url})\n\n"
            output += f"**文件信息：**\n"
            output += f"- URL: {file_url}\n"
            if width and height:
                output += f"- 尺寸：{width} x {height} px\n"
            output += f"- 类型：{args.image_part}\n"
            
            print(output)
            sys.exit(0)
        else:
            print(f"\n❌ 上传失败：{result['error']}")
            print(f"   状态码：{result['status']}")
            sys.exit(1)


if __name__ == "__main__":
    main()
