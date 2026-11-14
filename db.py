"""数据库操作模块。

所有对 articles 表的读写都集中在这里，页面里只调用这些函数。
数据库文件 blog.db 固定在项目根目录，首次运行会自动建表并写入示例数据。
增删改操作会通过 file_ops 追加到 blog.log（文件操作示例）。
"""

import os
import sqlite3
from contextlib import closing

import file_ops

# 注意：Pandas 只在 load_dataframe() 里延迟导入。
# 首页、写文章、文章管理页不需要 Pandas，这样能明显缩短首次打开页面时的等待时间。

# blog.db 放在本项目目录下，不受启动目录影响
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blog.db")

# 文章分类下拉选项（写文章、编辑文章共用）
CATEGORIES = ["生活", "技术", "随笔", "读书"]

# 首次运行时写入的示例文章：(标题, 分类, 正文, 发布日期)
# 每个分类各 3 篇，分布在 2026 年 6-11 月，方便直接查看统计和分类预测效果。
SAMPLE_ARTICLES = [
    (
        "开始写博客的第一天",
        "生活",
        "今天正式开通了这个博客。\n\n"
        "以后会在这里记录学习的笔记、生活里的小事，还有一些看完书之后的想法。"
        "希望自己能坚持写下去。",
        "2026-06-08",
    ),
    (
        "用 Streamlit 十分钟做一个网页",
        "技术",
        "Streamlit 是 Python 里非常简单好用的 Web 框架，只要会写 Python 就能做出网页。\n\n"
        "今天试了一下多页面功能，把文件放进 pages 目录就能自动生成左侧导航，比想象中省事。",
        "2026-07-15",
    ),
    (
        "Pandas 数据清洗的几个常用操作",
        "技术",
        "课程作业里用到了 Pandas，记录几个常用操作：\n\n"
        "read_sql 从数据库读表，groupby 分组统计，value_counts 快速计数，"
        "to_datetime 转换日期格式。",
        "2026-08-03",
    ),
    (
        "秋天的校园散步",
        "生活",
        "傍晚在校园里走了一圈，银杏叶开始变黄了。\n\n"
        "绕着操场走了三圈，风很凉快，回来路上买了一杯热奶茶。",
        "2026-09-12",
    ),
    (
        "读《活着》有感",
        "读书",
        "用了三个晚上读完《活着》。福贵的一生苦难不断，但他仍然平静地活了下来。\n\n"
        "合上书之后想了很久：活着本身就是一件需要勇气的事。",
        "2026-10-05",
    ),
    (
        "关于坚持写周记这件小事",
        "随笔",
        "坚持写周记半年了，翻回去看，发现很多当时觉得过不去的坎，现在都变成了普通的一行字。\n\n"
        "大概记录本身就是一种整理。",
        "2026-11-02",
    ),
    (
        "给博客加一个数据统计页面",
        "技术",
        "用 Pandas 从 SQLite 读出文章数据，再用 Matplotlib 和 Pyecharts 画图。\n\n"
        "静态图适合放进作业报告，交互图可以悬停查看数值、拖动缩放，两种方式各有各的好。",
        "2026-11-09",
    ),
    (
        "周末第一次自己做晚饭",
        "生活",
        "跟着视频做了番茄炒蛋和可乐鸡翅，味道居然还不错。\n\n"
        "收拾厨房花的时间比做饭还长，下次争取动作快一点。",
        "2026-10-18",
    ),
    (
        "重读《小王子》",
        "读书",
        "小时候只觉得这是一个关于星球和玫瑰的童话，长大后再读，才明白书里写的其实是告别和牵挂。\n\n"
        "真正重要的东西，用眼睛是看不见的。",
        "2026-09-25",
    ),
    (
        "《人类简史》读书笔记",
        "读书",
        "作者把人类的历史分成认知革命、农业革命和科学革命三个阶段。\n\n"
        "最打动我的一句话是：人类靠讲故事把陌生人组织起来，这可能是文明最重要的能力。",
        "2026-08-20",
    ),
    (
        "关于时间管理的一点想法",
        "随笔",
        "以前总喜欢把时间表排得满满的，结果一项没完成就不想继续。\n\n"
        "最近试着每天只定三件最重要的事，反而完成得更多，心里也没那么慌。",
        "2026-09-30",
    ),
    (
        "写在大一结束前",
        "随笔",
        "再过几天就放暑假了。这一年学会了写 Python，也认识了很多新同学。\n\n"
        "希望大二能继续保持好奇心，多读书，多动手做项目。",
        "2026-06-30",
    ),
]


def get_conn():
    """创建数据库连接，row_factory 让查询结果可以按列名取值。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """建表并保证表里有初始数据，可以重复调用（每个页面开头都会调用一次）。"""
    with closing(get_conn()) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                title      TEXT NOT NULL,
                content    TEXT NOT NULL,
                category   TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        if total == 0:
            conn.executemany(
                "INSERT INTO articles (title, category, content, created_at) "
                "VALUES (?, ?, ?, ?)",
                SAMPLE_ARTICLES,
            )
        conn.commit()


def add_article(title, category, content, created_at):
    """新增一篇文章，created_at 格式为 YYYY-MM-DD。"""
    with closing(get_conn()) as conn:
        conn.execute(
            "INSERT INTO articles (title, category, content, created_at) "
            "VALUES (?, ?, ?, ?)",
            (title, category, content, created_at),
        )
        conn.commit()
    # 把这次操作写入文本日志（第 5 章：文件操作）
    file_ops.append_log("新增文章", f"《{title}》 分类：{category}")


def get_all_articles():
    """返回全部文章，按发布日期倒序（同一天按 id 倒序）。"""
    with closing(get_conn()) as conn:
        return conn.execute(
            "SELECT id, title, content, category, created_at "
            "FROM articles ORDER BY created_at DESC, id DESC"
        ).fetchall()


def update_article(article_id, title, category, content):
    """修改文章的标题、分类和正文。"""
    with closing(get_conn()) as conn:
        conn.execute(
            "UPDATE articles SET title = ?, category = ?, content = ? WHERE id = ?",
            (title, category, content, article_id),
        )
        conn.commit()
    file_ops.append_log("修改文章", f"id={article_id} 标题改为《{title}》")


def delete_article(article_id):
    """按 id 删除文章。"""
    with closing(get_conn()) as conn:
        row = conn.execute(
            "SELECT title FROM articles WHERE id = ?", (article_id,)
        ).fetchone()
        conn.execute("DELETE FROM articles WHERE id = ?", (article_id,))
        conn.commit()
    # 删除后日志里保留标题，方便以后查看
    file_ops.append_log(
        "删除文章", f"《{row['title']}》" if row else f"id={article_id}"
    )


def load_dataframe():
    """用 Pandas 把 articles 表读成 DataFrame，供统计页面分析使用。"""
    import pandas as pd

    with closing(get_conn()) as conn:
        return pd.read_sql_query(
            "SELECT id, title, category, created_at FROM articles", conn
        )