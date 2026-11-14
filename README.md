# 个人博客文章管理与数据统计可视化系统

大一 Python 课程大作业。一个基于 Streamlit 多页面的简单个人博客，支持文章发布、编辑、删除，并用 Pandas + Matplotlib + Pyecharts 做数据统计可视化。

## 功能

- **首页**：按发布日期倒序展示全部文章，点击标题展开查看正文
- **写文章**：填写标题、分类、发布日期、正文，提交后写入 SQLite 并返回首页
- **文章管理**：逐篇编辑或删除，删除前需要二次确认
- **数据统计**：
  - 统计卡片：总文章数、分类数量、最近一篇发布日期
  - Matplotlib 静态图：各分类文章数量柱状图、每月发布数量折线图
  - Pyecharts 交互图：各分类占比饼图、每月发布数量柱状图（可缩放）

## 运行方法

环境要求：Python 3.9 及以上，首次运行需要联网加载一次 Pyecharts 使用的 ECharts 脚本。

```bash
# 1. 安装依赖（建议先创建虚拟环境）
pip install -r requirements.txt

# 2. 启动应用
streamlit run app.py
```

启动后浏览器自动打开 `http://localhost:8501`。首次运行会自动创建 `blog.db`，并写入 7 条示例文章，可以直接查看统计效果。

## 项目结构

```
yvchen-blog/
├── app.py                # 首页（文章列表）
├── db.py                 # 数据库封装：建表、增删改查、读取 DataFrame
├── charts.py             # 图表生成：Matplotlib 静态图、Pyecharts 交互图
├── pages/
│   ├── 1_写文章.py        # 写文章
│   ├── 2_文章管理.py      # 编辑 / 删除
│   └── 3_数据统计.py      # 统计指标与图表
├── requirements.txt
├── README.md
└── blog.db               # 首次运行时自动生成
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

## 说明

- 数据库操作全部封装在 `db.py`，页面中不直接写 SQL。
- 中文支持：`charts.py` 会按 微软雅黑 → 黑体 → 苹方 → 文泉驿 的顺序自动匹配系统中文字体，Windows / macOS 均能正常显示中文图表标题。
- 页面全部使用 Streamlit 原生组件，没有自定义 HTML/CSS。
- 示例数据只在表为空时写入一次；删除全部文章后不会自动补回。