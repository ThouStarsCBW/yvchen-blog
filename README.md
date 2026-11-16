# 个人博客文章管理与数据统计可视化系统

大一 Python 课程大作业。一个基于 Streamlit 多页面的个人博客，覆盖文章增删改查、数据统计、文件导出与数据导入。

## 功能

- **首页**：按发布日期倒序展示文章，支持每页 10 / 20 / 50 / 100 条分页，点击标题展开查看正文
- **写文章**：填写标题、分类、发布日期、正文，提交后写入 SQLite 并返回首页；分类下拉自动包含数据库里的全部标签，也可以手动输入新标签
- **文章管理**：按分类（标签）和日期范围筛选，支持分页查看；勾选后可批量删除（可跨页），也支持逐篇编辑、删除和查看最近 10 条操作日志
- **数据统计**：
  - 统计卡片：总文章数、分类数量、最近一篇发布日期
  - numpy 月度统计：月均发文量、标准差、单月最高、最近月环比
  - 分类 × 月份发文矩阵（numpy 二维数组转换为表格）
  - Matplotlib 静态图：各分类文章数量柱状图、每月发布数量折线图
  - Pyecharts 交互图：各分类占比饼图、每月发布数量柱状图（可缩放）
  - 文件导出：下载文章 CSV / 统计 JSON，或写入项目 `exports/` 目录
- **数据导入**：上传 CSV / JSON / JSONL 文件批量导入文章，支持中英文字段名，自动跳过重复标题和无效记录，标签数量不受限制

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

启动后浏览器自动打开 `http://localhost:8501`。首次运行（数据库文件不存在时）会自动创建 `blog.db` 并写入 12 条示例文章，方便直接查看统计效果。

## 项目结构

```
yvchen-blog/
├── app.py                # 首页（文章列表 + 分页）
├── pagination.py         # 首页与管理页共用的分页工具
├── db.py                 # 数据库封装：建表、增删改查、批量导入导出、动态标签
├── charts.py             # numpy 统计计算、Matplotlib 静态图、Pyecharts 交互图
├── file_ops.py           # 文件操作：操作日志、CSV / JSON 导出与导入解析
├── pages/
│   ├── 1_写文章.py        # 写文章（支持动态标签与自定义标签）
│   ├── 2_文章管理.py      # 筛选、分页、批量删除、编辑、日志
│   ├── 3_数据统计.py      # 统计指标、numpy 统计、四张图表、文件导出
│   └── 4_数据导入.py      # CSV / JSON / JSONL 批量导入
├── .streamlit/
│   └── config.toml       # 关闭文件监视、关闭匿名统计，提升页面响应速度
├── requirements.txt
├── README.md
├── blog.db               # 首次运行时自动生成
├── blog.log              # 操作日志，自动生成
└── exports/              # 导出的 CSV / JSON，自动生成
```

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
| 3. 列表、元组、字典、集合、字符串 | `CATEGORIES` 列表、`SAMPLE_ARTICLES` 元组、Pyecharts `options` 字典、集合去重、`zip` 与字符串切片 |
| 4. 选择、循环、函数 | 各页面 `if / for`、`db.py` 与 `charts.py` 的函数定义、参数与返回值 |
| 5. 文件操作 | `file_ops.py`：`open(..., "a")` 追加日志、CSV / JSON 文件导出、读取与解析导入文件 |
| 6. numpy 数组与矩阵运算 | 月均 / 标准差 / 最大值、`np.zeros` 构造分类 × 月份二维矩阵、按行求和 |
| 7. Pandas 数据分析 | `read_sql_query`、`value_counts`、`sort_index`、`DataFrame`、矩阵转表格 |
| 9. matplotlib 可视化 | 分类柱状图、月度折线图、中文字体设置、`bar_label`、`tight_layout` |

说明：第 8 章 sklearn 机器学习、第 10 章爬虫未包含在本项目中。

## 说明

- 数据库操作全部封装在 `db.py`，页面中不直接写 SQL。
- 中文支持：`charts.py` 会按 微软雅黑 → 黑体 → 苹方 → 文泉驿 的顺序自动匹配系统中文字体，Windows / macOS 均能正常显示中文图表标题。
- 页面全部使用 Streamlit 原生组件，没有自定义 HTML/CSS。
- 示例数据只在数据库文件不存在（首次运行）时写入；清空文章后刷新页面不会自动补回，方便先清空再导入自己的数据。
- `.streamlit/config.toml` 关闭了文件监视，修改 Python 代码后需要重启服务才会生效。
- `blog.db`、`blog.log`、`exports/` 都是运行时生成的文件，不纳入 git。