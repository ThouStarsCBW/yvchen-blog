# 个人博客文章管理与数据统计可视化系统

大一 Python 课程大作业。一个基于 Streamlit 多页面的个人博客，覆盖文章增删改查、数据统计、数据导入和智能问答。

## 功能

- **首页**：按发布日期倒序展示文章，支持每页 10 / 20 / 50 / 100 条分页，点击标题展开查看正文
- **写文章**：填写标题、分类、发布日期、正文，提交后写入 SQLite 并返回首页；分类下拉自动包含数据库里的全部标签，也可以手动输入新标签
- **文章管理**：按分类（标签）和日期范围筛选，支持分页查看；勾选后可批量删除（可跨页），也支持逐篇编辑、删除和查看最近 10 条操作日志
- **数据统计**：
  - 统计卡片：总文章数、分类数量、最近一篇发布日期
  - numpy 月度统计：月均发文量、标准差、单月最高、较上月变化
  - 分类 × 月份发文矩阵（numpy 二维数组转换为表格）
  - Matplotlib 静态图：各分类文章数量柱状图、每月发布数量折线图
  - Pyecharts 交互图：各分类占比饼图、每月发布数量柱状图（可缩放）

  - 文件导出：下载文章 CSV / 统计 JSON，或写入项目 `exports/` 目录
- **数据导入**：上传 CSV / JSON / JSONL 文件批量导入文章，支持中英文字段名，自动跳过重复标题和无效记录，标签数量不受限制
- **智能问答**：先按问题调用 DB 查询/统计函数，再用本地规则或 OpenAI 兼容大模型生成回答

## 运行方法

环境要求：Python 3.10 及以上（推荐 3.12，已实测）。使用 Pyecharts 交互图时需要联网。

```bash
# 1. 安装依赖（建议先创建虚拟环境）
pip install -r requirements.txt

# 2. 启动应用
streamlit run app.py
```

如果电脑上装了 uv，也可以这样运行（`.venv` 已存在时可跳过第一行）：

```bash
uv venv --python 3.12
uv pip install -r requirements.txt --python .venv/Scripts/python.exe
.venv/Scripts/streamlit run app.py
```

启动后浏览器自动打开 `http://localhost:8501`。首次运行（数据库文件不存在时）会自动创建 `blog.db` 并建表，但**不会自动导入任何数据**；需要数据时使用「数据导入」页导入 `blog-data/articles.jsonl`，或在「写文章」页手动发布。

## 项目结构

```
yvchen-blog/
├── app.py                # 首页（文章列表 + 分页）
├── pagination.py         # 首页与管理页共用的分页工具
├── blog-data/
│   ├── articles.jsonl    # 可供导入的数据文件（不会自动导入）
│   ├── articles_2.jsonl  # 不会自动导入
│   └── merge.py
├── db.py                 # 数据库封装：建表、增删改查、批量导入导出、动态标签
├── charts.py             # numpy 统计、Matplotlib、Pyecharts
├── file_ops.py           # 文件操作：操作日志、CSV / JSON 导出与导入解析
├── text_utils.py         # 中文停用词
├── db_tools.py           # 按问题意图调用 DB 查询/统计函数
├── rag.py                # 检索与可选大模型回答
├── pages/
│   ├── 1_写文章.py        # 写文章（支持动态标签与自定义标签）
│   ├── 2_文章管理.py      # 筛选、分页、批量删除、编辑、日志
│   ├── 3_数据统计.py      # 统计指标、numpy 统计、四张图表、导出
│   ├── 4_数据导入.py      # CSV / JSON / JSONL 批量导入
│   └── 5_智能问答.py      # 检索博客文章并生成回答
├── .streamlit/
│   └── config.toml       # 关闭文件监视、关闭匿名统计，提升页面响应速度
├── requirements.txt
├── README.md
├── blog.db               # 首次运行时自动生成
├── blog.log              # 操作日志，自动生成
└── exports/              # 导出的 CSV / JSON，自动生成
```

## 智能问答说明

每次提问会先根据问题内容调用 `db.py` 中的查询/统计函数，把返回结果作为上下文，再调用大模型生成回答；未配置大模型时使用本地检索。

- **DB 查询路由**（`db_tools.py`）：
  - 统计类问题：调用 `db.load_dataframe()` 统计总文章数、各标签数量、每月发文量
  - 指定标签问题：调用 `db.get_available_categories()` 并按分类过滤文章
  - 内容类问题：调用 `rag.search()` 检索最相关的文章
  - 查询结果和最多 6 篇相关文章会作为 AI 上下文
- **默认模式：本地检索**，不需要联网或 API Key，直接返回检索到的文章摘要。
- **可选模式：大模型 + 流式输出**，设置以下环境变量后，调用 OpenAI 兼容接口；模型只接收 DB 查询结果和相关文章，不再一次性发送全部文章：
  ```bash
  # DeepSeek 示例
  set OPENAI_API_KEY=你的Key
  set OPENAI_BASE_URL=https://api.deepseek.com/v1
  set OPENAI_MODEL=deepseek-chat

  # 火山引擎 Ark 示例
  set OPENAI_API_KEY=你的ArkKey
  set OPENAI_BASE_URL=https://ark.cn-beijing.volces.com/api/coding/v3
  set OPENAI_MODEL=ark-code-latest
  ```
  PowerShell 写法为 `$env:OPENAI_API_KEY="你的Key"`，其他两个变量同理。
  代码不会发送 `temperature` 参数，以兼容只允许默认值的模型（如 Ark coding 模型）。
- 页面为多轮对话框形式，回答逐段流式输出；只把最近 8 条对话历史传给模型，右上角「清空对话」可以重置会话。
- 聊天记录保存在本地 `chat_history.json`，切换页面、刷新或重启服务后会自动恢复；点击「清空对话」会删除该文件。该文件不纳入 git。
- 大模型调用超时或失败时，会先尝试一次性回答，再回退到本地检索。
- 调用大模型时，DB 查询结果和相关文章会发送给所配置的模型服务，请确认数据可以外发。


## 标签说明

- 默认标签为 8 个：生活、技术、随笔、读书、职场、美食、旅行、影音
- 写文章页和编辑页会自动读取数据库中实际出现的标签，导入新标签后无需改代码
- 导入文件里的分类不受默认列表限制，统计图表和管理页筛选会自动识别新标签
- 分类为空时默认归为「随笔」

## 数据导入说明

支持三种文件：

| 格式 | 说明 |
| --- | --- |
| `.csv` | 第一行为表头，字段可用 `title, content, category, created_at` 或 `标题, 正文, 分类, 发布日期` |
| `.json` | JSON 数组，或 `{"articles": [...]}`、`{"data": [...]}` |
| `.jsonl` | 每行一个 JSON 对象（适合分批生成的大数据量文件） |

规则：

- 标题或正文为空的行会被跳过
- 标题与数据库中已有文章重复时会自动跳过
- 分类为空时默认归为「随笔」
- 日期不是 `YYYY-MM-DD` 格式时，自动使用当天日期
- 额外字段（如 `index`、`batch`）会被忽略，不影响导入

## 数据库设计

一张 `articles` 表：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER | 主键，自增 |
| title | TEXT | 文章标题 |
| content | TEXT | 文章内容 |
| category | TEXT | 标签（默认 8 类，也支持导入其他标签） |
| created_at | TEXT | 发布日期，格式 `YYYY-MM-DD` |

## 对应课程知识点

| 章节 | 项目中的体现 |
| --- | --- |
| 1. 开发环境与编码规范 | `.venv` / `requirements.txt` 依赖管理、模块分层、PEP8 命名与函数注释 |
| 2. 数据类型、运算符、内置函数 | 字符串、整数、布尔、日期、比较与逻辑运算、`len` / `max` / `int`、f-string |
| 3. 列表、元组、字典、集合、字符串 | `CATEGORIES` 列表、Pyecharts `options` 字典、`zip` 元组、集合去重、字符串切片 |
| 4. 选择、循环、函数 | 各页面 `if / for`、`db.py` / `db_tools.py` / `charts.py` / `rag.py` 的函数定义、参数与返回值 |
| 5. 文件操作 | `file_ops.py`：`open(..., "a")` 追加日志、CSV / JSON 文件导出、读取与解析导入文件 |
| 6. numpy 数组与矩阵运算 | 月均 / 标准差 / 最大值、`np.zeros` 构造分类 × 月份二维矩阵、按行求和 |
| 7. Pandas 数据分析 | `read_sql_query`、`value_counts`、`sort_index`、`DataFrame`、矩阵转表格、`db_tools` 按问题调用统计函数 |
| 9. matplotlib 可视化 | 分类柱状图、月度折线图、中文字体设置、`bar_label`、`tight_layout` |

说明：第 8 章 sklearn 机器学习、第 10 章爬虫未包含在本项目中；智能问答的检索使用 jieba + 手写 TF-IDF，不依赖 sklearn。

## 说明

- 数据库操作全部封装在 `db.py`，页面中不直接写 SQL。
- 中文支持：图表会自动匹配系统中文字体（微软雅黑 / 黑体 / 苹方等）。
- 页面全部使用 Streamlit 原生组件，没有自定义 HTML/CSS。
- 首次运行只创建 `blog.db` 空表，不自动导入任何数据；需要数据时通过「数据导入」页导入文件，或在「写文章」页手动发布。
- `.streamlit/config.toml` 关闭了文件监视，修改 Python 代码后需要重启服务才会生效。
- `blog.db`、`blog.log`、`exports/` 都是运行时生成的文件，不纳入 git。