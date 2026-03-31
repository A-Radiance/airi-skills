#!/usr/bin/env python3
"""
AiriLab MJ 创意渲染任务提交脚本（完整版）

用法:
    python3 submit_mj.py --prompt "现代建筑" --style contemporary
"""

import requests
import json
import sys
import time
import argparse
from pathlib import Path
from dotenv import load_dotenv
import os

# 加载 .env 配置
load_dotenv(Path.home() / '.openclaw' / 'skills' / 'api-list' / '.env')

TOKEN = os.getenv('AIRILAB_API_KEY')
USER_ID = "22577"

def submit_mj_task(prompt, style="contemporary", aspect_ratio="16:9"):
    """提交 MJ 创意渲染任务"""
    
    url = "https://cn.airilab.com/api/toolset/call"
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "Origin": "https://cn.airilab.com",
        "Referer": "https://cn.airilab.com/"
    }
    
    payload = {
        "toolsetId": 2,
        "baseModelId": 4,
        "userId": int(USER_ID),
        "teamId": 3110,
        "params": {
            "prompt": prompt,
            "style": style,
            "aspect_ratio": aspect_ratio
        }
    }
    
    print(f"📤 提交任务...")
    print(f"   Prompt: {prompt}")
    print(f"   Style: {style}")
    print(f"   Aspect Ratio: {aspect_ratio}")
    print()
    
    response = requests.post(url, headers=headers, json=payload)
    
    print(f"📊 HTTP 状态码：{response.status_code}")
    print(f"📄 响应内容：{response.text[:500]}")
    
    try:
        result = response.json()
        if result.get('status') == 200:
            print()
            print("✅ 任务提交成功！")
            print(f"📋 Job ID: {result.get('data', {}).get('jobId', 'N/A')}")
            return result
        else:
            print(f"❌ 提交失败：{result.get('message', 'Unknown error')}")
            return None
    except json.JSONDecodeError:
        print(f"❌ 无法解析响应：{response.text}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='提交 MJ 创意渲染任务')
    parser.add_argument('--prompt', type=str, required=True, help='提示词')
    parser.add_argument('--style', type=str, default='contemporary', help='风格')
    parser.add_argument('--aspect-ratio', type=str, default='16:9', help='宽高比')
    
    args = parser.parse_args()
    
    submit_mj_task(args.prompt, args.style, args.aspect_ratio)
