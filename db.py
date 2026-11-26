"""数据库操作模块。

所有对 articles 表的读写都集中在这里，页面里只调用这些函数。
数据库文件 blog.db 固定在项目根目录，首次运行只建表，不自动导入任何数据。
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

# 默认标签（写文章下拉、编辑页共用）
# 导入时如果出现其他标签，页面会自动补充显示。
CATEGORIES = ["生活", "技术", "随笔", "读书", "职场", "美食", "旅行", "影音"]


def get_conn():
    """创建数据库连接，row_factory 让查询结果可以按列名取值。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_available_categories():
    """返回默认标签和数据库中实际出现的标签，去重后排序。"""
    with closing(get_conn()) as conn:
        rows = conn.execute("SELECT DISTINCT category FROM articles").fetchall()
    categories = set(CATEGORIES) | {row["category"] for row in rows}
    return sorted(categories)


def init_db():
    """建表；首次运行只创建空表，不自动导入任何数据。"""
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


def get_existing_titles():
    """返回数据库中已有的全部标题，用于导入时查重。"""
    with closing(get_conn()) as conn:
        rows = conn.execute("SELECT title FROM articles").fetchall()
    return {row["title"] for row in rows}


def bulk_add_articles(articles):
    """批量插入文章，返回实际插入数量（articles 为字典列表）。"""
    if not articles:
        return 0

    with closing(get_conn()) as conn:
        conn.executemany(
            "INSERT INTO articles (title, category, content, created_at) "
            "VALUES (?, ?, ?, ?)",
            [
                (a["title"], a["category"], a["content"], a["created_at"])
                for a in articles
            ],
        )
        conn.commit()

    file_ops.append_log("批量导入", f"导入 {len(articles)} 篇文章")
    return len(articles)


def bulk_delete_articles(article_ids):
    """批量删除文章，返回删除数量。"""
    article_ids = list(article_ids)
    if not article_ids:
        return 0

    # 只拼接问号占位符，具体 id 仍然通过参数传入，避免 SQL 注入
    placeholders = ",".join("?" for _ in article_ids)
    with closing(get_conn()) as conn:
        conn.execute(
            f"DELETE FROM articles WHERE id IN ({placeholders})", article_ids
        )
        conn.commit()

    file_ops.append_log("批量删除", f"删除 {len(article_ids)} 篇文章")
    return len(article_ids)