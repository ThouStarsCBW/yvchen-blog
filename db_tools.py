"""数据库函数路由（智能问答用）。

根据用户问题选择 db.py 中的查询/统计函数，把返回结果整理成给大模型的上下文：
- 统计类问题：调用 db.load_dataframe() 做分类 / 月度统计
- 指定标签问题：调用 db.get_available_categories() 和文章列表过滤
- 内容类问题：调用 rag.search() 检索相关文章
"""

import db
import rag

# 统计类问题的关键词
STAT_KEYWORDS = (
    "多少", "数量", "统计", "几篇", "分布", "占比", "平均", "最高", "最低", "总数",
)
# 日期 / 时间类问题的关键词
DATE_KEYWORDS = ("月份", "每月", "哪个月", "日期", "时间", "最近", "今年", "去年")

MAX_ARTICLES = 6
ARTICLE_PREVIEW_CHARS = 500
SUMMARY_CHARS = 120


def _plain_text(content):
    return " ".join(str(content).split())


def _summary(article, limit=SUMMARY_CHARS):
    text = _plain_text(article["content"])
    return text[:limit] + ("..." if len(text) > limit else "")


def _detail(article, limit=ARTICLE_PREVIEW_CHARS):
    text = _plain_text(article["content"])
    if len(text) > limit:
        text = text[:limit] + "..."
    return f"《{article['title']}》（{article['category']}，{article['created_at']}）\n{text}"


def collect_db_context(question, articles, index):
    """按问题意图调用数据库函数，返回 (上下文文本, 查询概要)。"""
    question = str(question)
    categories = db.get_available_categories()
    matched = [category for category in categories if category and category in question]

    wants_stats = any(keyword in question for keyword in STAT_KEYWORDS)
    wants_date = any(keyword in question for keyword in DATE_KEYWORDS)

    lines = ["以下是数据库查询结果：", f"- 总文章数：{len(articles)}"]
    details = []

    # 统计 / 日期类问题：调用 Pandas 统计函数
    if wants_stats or wants_date:
        df = db.load_dataframe()
        if not df.empty:
            counts = df["category"].value_counts()
            lines.append(
                "- 各标签文章数："
                + "、".join(f"{name} {count} 篇" for name, count in counts.items())
            )
            lines.append(f"- 最近发布日期：{df['created_at'].max()}")

            if wants_date or "月" in question:
                months = df["created_at"].astype(str).str.slice(0, 7)
                monthly = months.value_counts().sort_index()
                lines.append(
                    "- 每月发文数："
                    + "、".join(
                        f"{month} {count} 篇" for month, count in monthly.items()
                    )
                )

        # 统计类问题只附带最近几篇摘要，不附加全文
        for article in articles[:3]:
            lines.append(
                f"- 最近文章：《{article['title']}》（{article['category']}，"
                f"{article['created_at']}）：{_summary(article, 100)}"
            )

    # 指定标签问题：按分类过滤文章
    if matched:
        for category in matched:
            category_articles = [
                article for article in articles if article["category"] == category
            ]
            lines.append(f"- 标签【{category}】共 {len(category_articles)} 篇")
            details.extend(category_articles[:MAX_ARTICLES])

        # 多个标签时去重并限制条数
        unique = []
        seen_ids = set()
        for article in details:
            if article["id"] in seen_ids:
                continue
            seen_ids.add(article["id"])
            unique.append(article)
        details = unique[:MAX_ARTICLES]
    else:
        # 内容类问题：调用检索函数返回最相关的文章
        results = rag.search(question, articles, index, top_k=MAX_ARTICLES)
        if results:
            lines.append(
                "- 与问题最相关的文章："
                + "、".join(article["title"] for _, article in results)
            )
            details = [article for _, article in results]
        elif wants_stats or wants_date:
            details = articles[:3]

    if details:
        lines.append("\n以下是相关文章内容：")
        for article in details:
            lines.append(_detail(article))

    return "\n".join(lines), {
        "matched_categories": matched,
        "stats": wants_stats or wants_date,
        "articles": len(details),
    }