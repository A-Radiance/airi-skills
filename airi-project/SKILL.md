---
name: airi-project
description: 获取用户在 AiriLab 平台的团队 ID 和项目 ID。当用户提到「我的团队」「项目列表」「获取 projectId」等关键词时或者由其他 SKILLS 直接调用触发此技能。
homepage: https://cn.airilab.com
metadata: { "openclaw": { "emoji": "📤", "requires": { "bins": ["curl", "python3"] } } }
---

# AiriLab Project - 团队与项目信息获取技能

获取用户在 AiriLab 平台的团队 ID 和项目 ID，支持工作流和脚本自动获取用户可用的团队和项目列表。

## 当使用此技能

✅ 使用此技能当：

- 用户想获取自己所在的团队 ID
- 用户想查询自己可用的项目 ID
- 工作流需要 teamId 或 projectId 作为参数

## ⚠️ 强制规则（必须遵守）

- ❗ 不允许使用历史对话中的 teamId 或 projectId
- ❗ 每次调用本技能必须重新请求 API 获取最新数据
- ❗ 即使上下文中已经存在 teamId / projectId，也必须覆盖
- ❗ **禁止自动选择 Id（必须列出所有选项让用户选择）**

---

## 鉴权说明

本 Skill 调用 AiriLab API，必须先通过 `airi-auth-manager` 验证Token是否有效

执行流程：
1. 调用 `airi-auth-manager` skill验证Token是否有效
2. 若 Token 无效，调用 `airi-auth-manager` skill登录流程
3. 登录成功后继续执行本 Skill

---

## 完整调用链逻辑 (严格执行)


### Step 1: 获取所有团队和项目（⚠️ 动态获取）

**使用以下 Python 代码动态获取所有团队和项目：**

```python
#!/usr/bin/env python3
"""
AiriLab 团队和项目信息获取脚本
动态获取所有团队和项目，不硬编码任何 ID
"""
import requests
import sys
from pathlib import Path

# 从.env 文件获取 Token
ENV_FILE = Path.home() / '.openclaw' / 'skills' / 'api-list' / '.env'

def get_token():
    """从.env 文件读取 Token"""
    if not ENV_FILE.exists():
        return None
    with open(ENV_FILE, 'r') as f:
        for line in f:
            if line.startswith('AIRILAB_API_KEY='):
                return line.split('=', 1)[1].strip()
    return None

def get_all_teams_and_projects(token):
    """获取所有团队和项目"""
    BASE_URL = "https://cn.airilab.com"
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    })
    
    result = []
    
    # Step 1: 获取所有团队
    resp = session.get(f"{BASE_URL}/api/Team/GetUserTeams")
    teams_data = resp.json()
    
    if teams_data.get("status") != 200 or not teams_data.get("data"):
        print(f"❌ 获取团队失败：{teams_data}")
        return result
    
    teams = teams_data["data"]
    
    # Step 2: 对每个团队获取项目
    for team in teams:
        team_info = {
            "teamId": team["teamId"],
            "teamName": team["teamName"],
            "projects": []
        }

        # 获取该团队下的所有项目
        resp = session.get(f"{BASE_URL}/api/Accounts/GetAllProjectsUser?teamId={team['teamId']}")
        projects_data = resp.json()

        if projects_data.get("status") == 200:
            # 优先取 userData，如果没有则取 teamData
            project_data = projects_data.get("userData", projects_data.get("teamData", {}))
            projects = project_data.get("projectModel", [])

            for proj in projects:
                team_info["projects"].append({
                    "projectId": proj["id"],
                    "projectName": proj["name"]
                })

        result.append(team_info)
    
    return result

def display_teams_and_projects(teams_projects):
    """格式化展示所有团队和项目"""
    if not teams_projects:
        print("❌ 没有找到任何团队")
        return
    
    print("📁 AiriLab 团队和项目列表：")
    print("=" * 60)
    
    for i, team in enumerate(teams_projects, 1):
        print(f"\n【团队{i}】{team['teamName']} (teamId: {team['teamId']})")

        if team["projects"]:
            for j, proj in enumerate(team["projects"], 1):
                print(f"  ├─ 【项目{j}】{proj['projectName']} (projectId: {proj['projectId']})")
        else:
            print(f"  ⚠️ 该团队下暂无项目")
    
    print("\n" + "=" * 60)
    print("💡 提示：请用以下方式之一选择：")
    print("   - 序号：'选择 团队 1 项目 2'")
    print("   - projectId: '用 170923'")
    print("   - 项目名称：'用 My Project 1'")

def main():
    token = get_token()
    if not token:
        print("❌ 未找到 Token，请先登录")
        sys.exit(1)
    
    teams_projects = get_all_teams_and_projects(token)
    display_teams_and_projects(teams_projects)
    
    # 返回 JSON 结果（可选）
    import json
    print("\n📄 JSON 结果:")
    print(json.dumps(teams_projects, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

---

### Step 2: 展示结果（⚠️ 强制要求）

**展示格式：**

```
📁 AiriLab 团队和项目列表：
============================================================

My Space (teamId: 0)
  ├─ 【项目 1】Project A (projectId: 1)
  ├─ 【项目 2】Project B (projectId: 2)
  └─ 【项目 3】Project C (projectId: 3)

Team A (teamId: 333)
  ├─ 【项目 1】Project A (projectId: 44)
  └─ 【项目 2】Project B (projectId: 45)

============================================================
💡 提示：请用以下方式之一选择：
   - 序号：'选择 Team A 项目 Project A'
   - projectId: '用 170923'
   - 项目名称：'用 My Project 1'
```

**如果某个团队下没有项目：**
```
【团队 X】XXX Team (teamId: 999)
  ⚠️ 该团队下暂无项目
```

---

### Step 3: 等待用户选择（⚠️ 强制要求）

**⚠️ 必须等待用户明确指定，禁止自动选择！**

**支持的选择方式：**

| 选择方式 | 用户输入示例 | 解析结果 |
|---------|------------|---------|
| 序号选择 | "选择 团队 1 项目 2" | teamId=0, projectId=1 |
| projectId 选择 | "用 1" | projectId=1 |
| 项目名称选择 | "用 Test Project" | projectName="Project" |
| 团队 + 项目名 | "My Space 的 Project A" | teamName="My Space", projectName="Project A" |

---

### Step 4: 返回最终结果

根据用户选择返回：

```json
{
  "teamId": 0,
  "projectId": 0,
  "projectName": ""
}
```

---

## 命令行快速调用

### 方式 1: 直接运行 Python 脚本

```bash
python3 ~/.openclaw/skills/airi-project/get_projects.py
```

### 方式 2: 一行命令获取列表

```bash
TOKEN=$(grep AIRILAB_API_KEY ~/.openclaw/skills/api-list/.env | cut -d'=' -f2) && \
python3 -c "
import requests,json
BASE='https://cn.airilab.com'
s=requests.Session()
s.headers={'Authorization':f'Bearer $TOKEN','Accept':'application/json'}
teams=s.get(f'{BASE}/api/Team/GetUserTeams').json()
print('📁 团队列表:')
for i,t in enumerate(teams.get('data',[]),1):
    print(f'【团队{i}】{t[\"teamName\"]} (teamId:{t[\"teamId\"]})')
    projs=s.get(f'{BASE}/api/Accounts/GetAllProjectsUser?teamId={t[\"teamId\"]}').json()
    ps=projs.get('userData',projs.get('teamData',{})).get('projectModel',[])
    for j,p in enumerate(ps,1):
        print(f'  ├─【项目{j}】{p[\"name\"]} (projectId:{p[\"id\"]})')
    if not ps: print('  ⚠️ 该团队下暂无项目')
"
```

---

## 相关文件

- 认证技能：`~/.openclaw/skills/airilab-auth/SKILL.md`
- API 调用清单：`~/.openclaw/skills/api-list/SKILL.md`
- Token 配置：`~/.openclaw/skills/api-list/.env`
