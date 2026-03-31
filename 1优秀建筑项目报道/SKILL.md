---
name: daily_project_report
description: 获取每日优秀建筑项目报道，并提取关键信息用于快速浏览
version: 1.0.0
---

inputs:
  - name: date
    type: string
    required: false
    description: 指定日期，默认今天

outputs:
  - name: reports
    type: array
    description: 项目列表

steps:
  - name: fetch_projects
    type: llm
    prompt: |
      请从以下网站获取最新的优秀项目报道，并整理信息：
      
      网站：
      - ArchDaily
      - Dezeen
      - Designboom
      - 谷德
      - 有方
      - 观筑
      
      要求：
      1. 只返回最近1天内的项目
      2. 每个项目提取：
         - 项目名称
         - 项目类型（住宅 / 商业 / 公共等）
         - 设计师/事务所
         - 地点（城市 + 国家）
         - 官方链接
         - 一句话描述
      
      输出 JSON 格式：
      [
        {
          "name": "",
          "type": "",
          "designer": "",
          "location": "",
          "link": "",
          "summary": ""
        }
      ]

  - name: format_output
    type: llm
    prompt: |
      将以下JSON整理成简洁速查格式：

      要求：
      - 每个项目一行
      - 用emoji增强可读性
      - 保留link
      - 中文输出

      示例格式：
      项目名 | 类型 | 设计师 | 地点  
      🔗 link

      数据：
      {{fetch_projects}}