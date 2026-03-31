#!/usr/bin/env python3
"""
AiriLab 后台轮询守护进程

职责：
1. 定期查询 pending 状态的任务
2. 检查任务状态
3. 完成后获取结果并通知用户

运行方式：
- 手动：python3 ~/.openclaw/skills/api-list/scheduler/worker.py
- 后台：nohup python3 worker.py > worker.log 2>&1 &
- systemd: 创建 systemd 服务（推荐）

依赖：
- airi-auth (强依赖，必须安装)
"""

import sqlite3
import json
import time
import sys
import subprocess
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


# ==================== 配置 ====================

SCRIPTS_DIR = Path(__file__).parent.parent / 'scripts'
DATA_DIR = Path(__file__).parent
DB_PATH = DATA_DIR / 'jobs.db'
POLL_INTERVAL = 5  # 轮询间隔（秒）
MAX_ATTEMPTS = 120  # 最大轮询次数（约 10 分钟）

# 状态常量
STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"


def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            chat_id TEXT NOT NULL,
            tool TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            submitted_at TEXT,
            started_at TEXT,
            completed_at TEXT,
            input_params TEXT,
            output_url TEXT,
            thumbnail_url TEXT,
            error_message TEXT,
            attempts INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_status ON jobs(status)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_user ON jobs(user_id)
    ''')
    
    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成")


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def save_job(job_id: str, user_id: str, chat_id: str, tool: str, input_params: dict):
    """保存新任务"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO jobs 
        (job_id, user_id, chat_id, tool, status, submitted_at, input_params)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        job_id, user_id, chat_id, tool, STATUS_PENDING,
        datetime.now().isoformat(), json.dumps(input_params)
    ))
    
    conn.commit()
    conn.close()
    print(f"💾 任务已保存：{job_id}")


def get_pending_jobs():
    """获取所有 pending 状态的任务"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM jobs 
        WHERE status IN (?, ?) 
        ORDER BY submitted_at ASC
        LIMIT 50
    ''', (STATUS_PENDING, STATUS_PROCESSING))
    
    jobs = cursor.fetchall()
    conn.close()
    
    return jobs


def update_job_status(job_id: str, status: str, output_url: str = None, 
                      thumbnail_url: str = None, error_message: str = None):
    """更新任务状态"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if status == STATUS_COMPLETED:
        cursor.execute('''
            UPDATE jobs 
            SET status = ?, completed_at = ?, output_url = ?, thumbnail_url = ?
            WHERE job_id = ?
        ''', (status, datetime.now().isoformat(), output_url, thumbnail_url, job_id))
    
    elif status == STATUS_FAILED:
        cursor.execute('''
            UPDATE jobs 
            SET status = ?, completed_at = ?, error_message = ?
            WHERE job_id = ?
        ''', (status, datetime.now().isoformat(), error_message, job_id))
    
    else:
        cursor.execute('''
            UPDATE jobs 
            SET status = ?, attempts = attempts + 1
            WHERE job_id = ?
        ''', (status, job_id))
    
    conn.commit()
    conn.close()


def check_job_status(job_id: str) -> str:
    """检查任务状态"""
    script_path = SCRIPTS_DIR / 'check_status.py'
    
    result = subprocess.run(
        ['python3', str(script_path), '--job-id', job_id],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    # 检查是否有鉴权错误
    if '需要鉴权' in result.stdout or '未找到 Token' in result.stdout:
        print(f"🔐 鉴权错误：Token 可能过期")
        return "auth_error"
    
    # 解析输出
    for line in result.stdout.split('\n'):
        if '状态:' in line:
            status = line.split(':')[1].strip()
            return status
    
    return "unknown"


def fetch_result(job_id: str) -> dict:
    """获取任务结果"""
    script_path = SCRIPTS_DIR / 'fetch.py'
    
    result = subprocess.run(
        ['python3', str(script_path), '--job-id', job_id],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    # 检查是否有鉴权错误
    if '需要鉴权' in result.stdout or '未找到 Token' in result.stdout:
        print(f"🔐 鉴权错误：Token 可能过期")
        return {'error': 'auth_required'}
    
    # 解析输出
    output = {}
    for line in result.stdout.split('\n'):
        if '输出 URL:' in line:
            output['output_url'] = line.split(':')[1].strip()
        elif '缩略图:' in line:
            output['thumbnail_url'] = line.split(':')[1].strip()
        elif '工具:' in line:
            output['toolset'] = line.split(':')[1].strip()
    
    return output


def notify_user(user_id: str, chat_id: str, job_id: str, status: str, 
                output_url: str = None, error_message: str = None):
    """
    通知用户任务完成
    
    注意：这里使用 OpenClaw 的内部通知机制
    实际实现需要根据 OpenClaw 的 API 调整
    """
    if status == STATUS_COMPLETED:
        message = f"""
✅ 任务完成！

📋 Job ID: {job_id}
🖼️  结果：{output_url}

点击查看完整结果。
"""
    else:
        message = f"""
❌ 任务失败

📋 Job ID: {job_id}
⚠️  错误：{error_message}

请重试或联系管理员。
"""
    
    # TODO: 调用 OpenClaw 的通知 API
    # 这里先打印日志
    print(f"📬 通知用户 {user_id} ({chat_id}): {message.strip()}")
    
    # 示例：保存到通知日志
    log_file = DATA_DIR / 'notifications.log'
    with open(log_file, 'a') as f:
        f.write(f"{datetime.now().isoformat()} | {user_id} | {chat_id} | {job_id} | {status}\n")


def process_job(job):
    """处理单个任务"""
    job_id = job['job_id']
    user_id = job['user_id']
    chat_id = job['chat_id']
    attempts = job['attempts']
    
    # 检查是否超过最大轮询次数
    if attempts >= MAX_ATTEMPTS:
        print(f"⚠️  任务超时：{job_id}")
        update_job_status(job_id, STATUS_FAILED, error_message="轮询超时")
        notify_user(user_id, chat_id, job_id, STATUS_FAILED, 
                   error_message="任务处理超时，请重试")
        return
    
    # 检查任务状态
    print(f"🔍 检查任务：{job_id} (尝试 {attempts + 1}/{MAX_ATTEMPTS})")
    status = check_job_status(job_id)
    
    if status == "completed":
        print(f"✅ 任务完成：{job_id}")
        
        # 获取结果
        result = fetch_result(job_id)
        output_url = result.get('output_url', '')
        thumbnail_url = result.get('thumbnail_url', '')
        
        # 更新数据库
        update_job_status(job_id, STATUS_COMPLETED, output_url, thumbnail_url)
        
        # 通知用户
        notify_user(user_id, chat_id, job_id, STATUS_COMPLETED, output_url)
        
    elif status == "failed" or status == "error" or status == "auth_error":
        print(f"❌ 任务失败：{job_id} (状态：{status})")
        
        error_msg = "Token 过期，请重新登录" if status == "auth_error" else f"API 返回状态：{status}"
        update_job_status(job_id, STATUS_FAILED, error_message=error_msg)
        notify_user(user_id, chat_id, job_id, STATUS_FAILED, error_message=error_msg)
    
    elif status in ["queued", "sending_now", "processing"]:
        # 仍在处理中
        new_status = STATUS_PROCESSING if status != "queued" else STATUS_PENDING
        update_job_status(job_id, new_status)
        print(f"⏳ 处理中：{job_id} ({status})")
    
    else:
        print(f"⚠️  未知状态：{job_id} ({status})")
        update_job_status(job_id, STATUS_PENDING)


def run():
    """主循环"""
    print("=" * 60)
    print("🚀 AiriLab 后台轮询守护进程")
    print("=" * 60)
    print(f"📂 数据目录：{DATA_DIR}")
    print(f"💾 数据库：{DB_PATH}")
    print(f"⏱️  轮询间隔：{POLL_INTERVAL}秒")
    print(f"🔄 最大尝试：{MAX_ATTEMPTS}次")
    print()
    print("按 Ctrl+C 停止...")
    print()
    
    # 初始化数据库
    init_db()
    
    try:
        while True:
            # 获取 pending 任务
            pending_jobs = get_pending_jobs()
            
            if pending_jobs:
                print(f"📋 发现 {len(pending_jobs)} 个待处理任务")
                
                for job in pending_jobs:
                    try:
                        process_job(job)
                    except Exception as e:
                        print(f"❌ 处理任务失败 {job['job_id']}: {e}")
            else:
                print("💤 无待处理任务，休眠中...")
            
            # 休眠
            time.sleep(POLL_INTERVAL)
            
    except KeyboardInterrupt:
        print()
        print("👋 守护进程已停止")


if __name__ == "__main__":
    run()
