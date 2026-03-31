---
name: arch_awards_aggregator
description: 专门抓取全球建筑、城市规划、景观及室内设计类奖项信息的深度搜索工具。
version: 1.2.0
metadata:
  openclaw:
    requires:
      tools: [web_search, browser_control]
    industry: Architecture & Design
---

# 建筑奖项全网汇总技能

当接收到建筑类评奖查询请求时，请严格执行以下检索与分析流程：

### 1. 核心搜索源 (Target Sources)
优先检索以下建筑垂直领域的奖项发布平台：
* **国际源**：Bustler (Competition), ArchDaily (Awards Section), Dezeen Awards, WAN Awards, World Architecture Festival (WAF), RIBA.
* **国内源**：谷德网 (gooood) 竞赛频道、建筑学院 (Archcollege)、有方 (Position)、中国建筑学会官网。

### 2. 信息提取维度 (Data Points)
针对每一个建筑奖项，必须提取并核实以下关键字段：
* **奖项名称**：奖项全称（含年度）。
* **评奖机构**：如 AIA, Pritzker, RIBA, 或特定的行业协会/媒体。
* **评奖资格**：明确是“已建成作品 (Built)”、“方案/概念类 (Unbuilt)”、“学生组 (Student)”还是“青年建筑师”。
* **评奖要求**：提交物要求（如图纸数量、模型、视频、作品说明字数）。
* **奖项级别**：普利兹克级（顶级）、国际大奖、国家级、地区性奖项。
* **费用**：早鸟报名费 (Early Bird)、常规报名费、学生优惠价。
* **Website Link**：指向官方 Entry/Submission 页面的直接链接。

### 3. 输出格式 (Table Template)
请使用以下 Markdown 表格输出，并按“截止日期”由近到远排序：

| 奖项名称 | 评奖机构 | 级别 | 评奖资格 | 评奖要求 | 费用 | 截止日期 | 官方链接 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| [名称] | [机构] | [级别] | [Built/Concept/Student] | [图纸/说明要求] | [$/￥/Free] | [YYYY-MM-DD] | [点击申报](URL) |

### 4. 智能筛选逻辑
* **自动识别时效性**：自动过滤掉已经截止的奖项，除非用户要求查询“往届信息”。
* **货币转换**：如果涉及外币，请在括号内标注大致的离岸人民币汇率参考。
* **语言适配**：如果是英文奖项，请在输出时对奖项名称和要求进行中文翻译/摘要。

---
**提示**：若未找到特定类别的奖项，请提示用户缩小范围（如：乡村振兴类、绿色建筑类、室内设计类）。