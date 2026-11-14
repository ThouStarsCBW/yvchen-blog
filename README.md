# 个人博客文章管理与数据统计可视化系统

大一 Python 课程大作业。一个基于 Streamlit 多页面的个人博客，覆盖文章增删改查、数据统计、机器学习分类、爬虫抓取与文件操作。

## 功能

- **首页**：按发布日期倒序展示全部文章，点击标题展开查看正文
- **写文章**：填写标题、分类、发布日期、正文，提交后写入 SQLite 并返回首页
- **文章管理**：逐篇编辑或删除，删除前需要二次确认，底部可查看最近 10 条操作日志
- **数据统计**：
  - 统计卡片：总文章数、分类数量、最近一篇发布日期
  - numpy 月度统计：月均发文量、标准差、单月最高、最近月环比
  - 分类 × 月份发文矩阵（numpy 二维数组转换为表格）
  - Matplotlib 静态图：各分类文章数量柱状图、每月发布数量折线图
  - Pyecharts 交互图：各分类占比饼图、每月发布数量柱状图（可缩放）
  - 文件导出：下载文章 CSV / 统计 JSON，或写入项目 `exports/` 目录
- **分类预测**：用 sklearn 的 TF-IDF + 逻辑回归，根据标题和正文预测文章分类
- **素材抓取**：用 requests + BeautifulSoup 抓取 `quotes.toscrape.com` 的名言，可一键保存为文章草稿

## 运行方法

环境要求：Python 3.10 及以上（推荐 3.12，已实测）。使用 Pyecharts 图表和爬虫功能时需要联网。

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

启动后浏览器自动打开 `http://localhost:8501`。首次运行会自动创建 `blog.db`，并写入 12 条示例文章（每类 3 篇），可以直接查看统计和分类预测效果。

## 项目结构

```
yvchen-blog/
├── app.py                # 首页（文章列表）
├── db.py                 # 数据库封装：建表、增删改查、读取 DataFrame、写操作日志
├── charts.py             # numpy 统计计算、Matplotlib 静态图、Pyecharts 交互图
├── file_ops.py           # 文件操作：操作日志、CSV / JSON 导出
├── pages/
│   ├── 1_写文章.py        # 写文章
│   ├── 2_文章管理.py      # 编辑 / 删除 / 查看操作日志
│   ├── 3_数据统计.py      # 统计指标、numpy 统计、四张图表、文件导出
│   ├── 4_分类预测.py      # sklearn 文本分类预测
│   └── 5_素材抓取.py      # requests + BeautifulSoup 爬虫
├── requirements.txt
├── README.md
├── blog.db               # 首次运行时自动生成
├── blog.log              # 操作日志，自动生成
└── exports/              # 导出的 CSV / JSON，自动生成
```

## 数据库设计

一张 `articles` 表：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER | 主键，自增 |
| title | TEXT | 文章标题 |
| content | TEXT | 文章内容 |
| category | TEXT | 分类（生活 / 技术 / 随笔 / 读书） |
| created_at | TEXT | 发布日期，格式 `YYYY-MM-DD` |

## 对应课程知识点

| 章节 | 项目中的体现 |
| --- | --- |
| 1. 开发环境与编码规范 | `.venv` / `requirements.txt` 依赖管理、模块分层、PEP8 命名与函数注释 |
| 2. 数据类型、运算符、内置函数 | 字符串、整数、布尔、日期、比较与逻辑运算、`len` / `max` / `int`、f-string |
| 3. 列表、元组、字典、集合、字符串 | `CATEGORIES` 列表、`SAMPLE_ARTICLES` 元组、Pyecharts `options` 字典、`zip` 与字符串切片 |
| 4. 选择、循环、函数 | 各页面 `if / for`、`db.py` 与 `charts.py` 的函数定义、参数与返回值 |
| 5. 文件操作 | `file_ops.py`：`open(..., "a")` 追加日志、CSV / JSON 文件导出、读取日志 |
| 6. numpy 数组与矩阵运算 | 月均 / 标准差 / 最大值、`np.zeros` 构造分类 × 月份二维矩阵、按行求和 |
| 7. Pandas 数据分析 | `read_sql_query`、`value_counts`、`sort_index`、`DataFrame`、矩阵转表格 |
| 8. sklearn 机器学习 | `TfidfVectorizer` + `LogisticRegression`、`train_test_split`、准确率评估 |
| 9. matplotlib 可视化 | 分类柱状图、月度折线图、中文字体设置、`bar_label`、`tight_layout` |
| 10. 爬虫实战 | `requests.get` 请求、`BeautifulSoup` 解析 HTML、抓取结果保存为文章 |

## 说明

- 数据库操作全部封装在 `db.py`，页面中不直接写 SQL。
- 中文支持：`charts.py` 会按 微软雅黑 → 黑体 → 苹方 → 文泉驿 的顺序自动匹配系统中文字体，Windows / macOS 均能正常显示中文图表标题。
- 页面全部使用 Streamlit 原生组件，没有自定义 HTML/CSS。
- 示例数据只在表为空时写入一次；删除全部文章后不会自动补回。
- 爬虫使用的是专门供练习的网站 `quotes.toscrape.com`，无需登录，也不会对真实站点造成压力。
- `blog.db`、`blog.log`、`exports/` 都是运行时生成的文件，不纳入 git。