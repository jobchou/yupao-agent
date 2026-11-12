# 鱼泡科技 · 数产助手机器人（Data Product Assistant）

> 面向「查数据、看指标、理解报表、圈选用户」的智能数据助手，基于 LangChain / LangGraph 构建，接入特征知识库、业务数据库、数据资产目录与报表解析能力。

---

## 一、项目背景

鱼泡科技内部沉淀了大量特征口径与指标定义，它们散落在特征知识库（`features.json`）、业务数据库 Schema 与数据资产清单中。业务与运营同学在做数据分析、指标解读以及**用户人群圈选**时，常面临：

- 不知道某个指标/字段的**口径定义**是什么、来自哪张表、对应怎样的 SQL 逻辑；
- 想圈选某一类用户（如"近期有活跃但在流失边缘的工人"）时，**不知道该组合哪些特征**；
- 收到一张报表，但**不理解结构与业务含义**；
- 需要快速定位数据库结果，却要跨多个系统反复查找。

本项目用 Agent 将上述能力统一收敛到一个自然语言对话入口，让用户"**用大白话提问，拿专业结果**"。

---

## 二、项目目标

- **查数据**：通过自然语言查询业务数据库，安全地执行只读 `SELECT`。
- **看指标 / 理解报表**：读取并解析报表文件（CSV / Excel / JSON），解释其结构、字段与业务含义。
- **特征知识库检索**：按**关键词、主题、时效性、分页**多维度检索特征，给出字段中文名、口径描述与对应 SQL 逻辑。
- **用户群体圈选建议**：基于用户描述的群体特征，从知识库推荐"特征组合 + 圈选 SQL"方案。
- **数据资产检索**：根据业务需求推荐相关数据表、字段或指标。

---

## 三、技术方案

### 3.1 总体架构

```
用户提问
   │
   ▼
┌─────────────────────────────────────────────┐
│           Agent（LangChain create_agent）      │
│  系统提示词（System Prompt / config JSON）      │
│    ├─ 强调口径溯源 + 圈选建议                    │
│  工具层（LangChain @tool）                     │
│    ├─ query_features     特征知识库检索          │
│    ├─ query_database     数据库只读查询          │
│    ├─ understand_report  报表文件解析            │
│    ├─ query_data_assets  数据资产检索            │
│    └─ list_data_assets   数据资产列表            │
└─────────────────────────────────────────────┘
   │
   ├─► 特征知识库  assets/features.json（151 个特征）
   ├─► 业务数据库  PostgreSQL（仅 SELECT）
   ├─► 数据资产    assets/数据资产.xlsx
   └─► 报表文件    assets/sample_report.csv 等
```

### 3.2 核心模块

| 模块 | 文件 | 能力 | 说明 |
|------|------|------|------|
| Agent 主逻辑 | `src/agents/agent.py` | 工具编排、模型对话 | 使用 `create_agent` + 短期记忆（开发环境内存记忆） |
| 特征知识库检索 | `src/tools/feature_query_tool.py` | 多关键词 / 多主题 / 多时效性 / 分页检索 | 关键词 AND 逻辑，主题/时效性 OR 逻辑 |
| 数据库查询 | `src/tools/database_query_tool.py` | 只读 SQL 查询 | 仅允许 `SELECT`，保证数据安全 |
| 报表理解 | `src/tools/report_understanding_tool.py` | CSV / Excel / JSON 解析 | 输出列名、类型、行数与示例数据 |
| 数据资产检索 | `src/tools/data_asset_query_tool.py` | 关键词检索资产目录 | 从 Excel（`数据资产.xlsx`）匹配表/字段/指标 |
| 模型配置 | `config/agent_llm_config.json` | LLM 参数与系统提示词 | 含 `model` / `temperature` / `top_p` 等及 `sp`、`tools` 声明 |

### 3.3 特征知识库（核心资产）

文件：`assets/features.json`

- **结构**：每个特征对象包含 6 个字段：`字段名称`、`字段中文`、`主题`、`时效性`、`特征描述`、`涉及sql逻辑`。
- **规模**：**151 个特征**
  - 主题分布：`用户`(143) / `招工`(8)
  - 时效性分布：`实时`(80) / `离线`(71)
  - **118 条**特征带有可直接执行的 SQL 逻辑，可一键转化为圈选查询。

```json
{
  "字段名称": "role_type_2c",
  "字段中文": "二分类角色标签（只有老板和工人）",
  "时效性": "离线",
  "主题": "用户",
  "特征描述": "基于用户在平台行为模型进行判断用户角色是老板还是工人",
  "涉及sql逻辑": "SELECT user_id, role_type_2c FROM yuapo.ods_user_role_label WHERE p_date = MAX_PT('yuapo.ods_user_role_label')"
}
```

### 3.4 特征检索工具能力（`query_features`）

| 参数 | 含义 | 逻辑 |
|------|------|------|
| `keyword` | 搜索关键词 | 空格分隔多个关键词，**跨字段 AND 匹配**（字段名/中文/描述/SQL 全覆盖） |
| `theme` | 主题筛选 | 逗号分隔多主题，任意命中即通过（OR） |
| `timeliness` | 时效性筛选 | 逗号分隔多时效性，任意命中即通过（OR） |
| `limit` / `offset` | 分页 | 控制返回数量，避免结果过长 |

示例：

```
query_features(keyword="登录 实时 用户", theme="用户", timeliness="实时")
```

### 3.5 系统提示词设计要点

- **角色**：鱼泡科技数据产品助手，专注查数据、看指标、理解报表、圈选用户。
- **过程**：理解需求 → 选对工具 → 调用取数 → 分析呈现 → 需求不清时主动澄清。
- **输出**：数据用表格、特征列出详情、圈选给出**特征组合 + 组合逻辑**；全程中文、少术语。
- **工具声明**：在 `config/agent_llm_config.json` 的 `tools` 字段中同步所有可用工具及用途，供模型知晓能力边界。

---

## 四、目录结构

```
.
├── config/                        # 模型配置（含 system prompt、模型参数）
│   └── agent_llm_config.json
├── assets/                        # 数据与资源
│   ├── features.json              # 特征知识库（151 个特征）
│   ├── 数据资产.xlsx              # 数据资产目录
│   └── sample_report.csv          # 报表样例
├── src/
│   ├── agents/agent.py            # Agent 主逻辑
│   ├── tools/                     # Agent 工具层
│   │   ├── feature_query_tool.py
│   │   ├── database_query_tool.py
│   │   ├── report_understanding_tool.py
│   │   └── data_asset_query_tool.py
│   ├── storage/                   # 数据库 / 对象存储封装
│   │   ├── database/              # PostgreSQL 查询封装
│   │   └── s3/                    # 对象存储封装
│   └── main.py                    # 运行主入口
├── scripts/                       # 运行 / 打包脚本
└── pyproject.toml                 # 依赖与项目配置（uv 管理）
```

---

## 五、环境与依赖

- **Python 依赖**：由 `pyproject.toml` 声明，使用 **uv** 管理（LangChain、LangGraph、Pandas、OpenAI SDK、FastAPI 等）。
- **LLM**：火山方舟（火山引擎方舟大语言模型服务，支持豆包等前沿模型）。
- **数据库**：PostgreSQL，工具层仅执行只读 `SELECT`。
- **对象存储**：S3 兼容存储，用于文件落盘与下载链接。

> 环境变量：`COZE_WORKSPACE_PATH` 指向项目根目录；模型调用所需的鉴权密钥通过运行环境注入，**不硬编码于仓库**。

---

## 六、运行方式

### 6.1 依赖安装

```bash
# 安装/同步依赖（uv）
uv sync
```

### 6.2 运行 Flow（整条任务流）

```bash
bash scripts/local_run.sh -m flow
```

### 6.3 运行单个节点

```bash
bash scripts/local_run.sh -m node -n <node_name>
```

### 6.4 启动 HTTP 服务

```bash
bash scripts/http_run.sh -m http -p 5000
```

---

## 七、典型使用场景示例

1. **查指标口径**
   > "用户注册时间这个指标是怎么定义的？" → 检索特征知识库，返回 `reg_time` / `register_ts` 的口径描述与 SQL。

2. **圈选用户群体**
   > "想圈出近期活跃、但集中在某级工种的工人群体" → 组合 `role_type_2c` + 工种标签 + 活跃特征，给出**特征组合 + 圈选 SQL**。

3. **看指标 / 理解报表**
   > "帮我看一下 `sample_report.csv` 里有什么" → 报表解析工具返回列名、类型、行数与示例数据。

4. **查数据**
   > "最近一周每个登录用户的行为次数" → 数据库只读查询返回结果并以表格呈现。

5. **找数据资产**
   > "有没有跟招工相关的数据表？" → 数据资产检索返回匹配的表 / 字段 / 指标。

---

## 八、注意事项

- 数据库工具**仅支持 `SELECT`**，从接口层规避数据被篡改的风险。
- `features.json` 中约 33 条特征**未提供 SQL 逻辑**（`涉及sql逻辑` 为空），此类特征仅用于口径理解，不用于直接圈选。
- 若需接入新的特征，按既有 JSON 结构追加对象即可，检索工具无需改动。