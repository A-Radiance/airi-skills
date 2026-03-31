#!/usr/bin/env python3
"""测试 Token 验证功能"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from upload_to_s3 import validate_token_by_api

# 测试用例
test_cases = [
    {
        "name": "有效 Token",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjExOTUsInVzZXJOYW1lIjoi6Zi_5omT77yBIiwicm9sZSI6MiwiaWF0IjoxNzc0NDkzOTM3LCJleHAiOjE3NzUwOTg3Mzd9.47cvGU7Sk2k9XomxTzf4LGqqirmnfx7BUkT-H6G0XVw",
        "expected": True
    },
    {
        "name": "无效 Token（格式错误）",
        "token": "invalid_token_12345",
        "expected": False
    },
    {
        "name": "无效 Token（过期）",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjExOTUsInVzZXJOYW1lIjoi6Zi_5omT77yBIiwicm9sZSI6MiwiaWF0IjoxNzc0NDkzOTM3LCJleHAiOjE3NzUwOTg3Mzd9.expired_signature",
        "expected": False
    }
]

print("=" * 60)
print("🔐 Token 验证功能测试")
print("=" * 60)
print()

for i, case in enumerate(test_cases, 1):
    print(f"测试 {i}: {case['name']}")
    print(f"Token: {case['token'][:30]}...")
    
    result = validate_token_by_api(case['token'])
    status = "✅" if result == case['expected'] else "❌"
    
    print(f"{status} 验证结果：{'有效' if result else '无效'}")
    print(f"   预期：{'有效' if case['expected'] else '无效'}")
    print()

print("=" * 60)
print("测试完成")
print("=" * 60)
