"""数据库函数路由（智能问答用）。

根据用户问题选择 db.py 中的查询/统计函数，把返回结果整理成给大模型的上下文：
- 统计类问题：调用 db.load_dataframe() 做分类 / 月度统计
- 标签 / 分类问题：调用 db.get_available_categories()，把全部标签和数量交给模型
- 指定标签问题：按分类过滤文章
- 内容类问题：调用 rag.search() 检索相关文章
"""

import db
import rag

# 统计类问题的关键词
STAT_KEYWORDS = (
    "多少", "数量", "统计", "几篇", "分布", "占比", "平均", "最高", "最低", "总数",
)
# 标签 / 分类类问题的关键词
TAG_KEYWORDS = (
    "标签", "分类", "几个标签", "多少标签", "哪些标签", "标签数", "分类数",
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
    wants_tags = any(keyword in question for keyword in TAG_KEYWORDS)

    # 无论什么问题，都先告诉模型完整的标签总数和标签列表
    lines = [
        "以下是数据库查询结果：",
        f"- 总文章数：{len(articles)}",
        f"- 标签总数：{len(categories)}",
    ]
    if categories:
        lines.append("- 全部标签：" + "、".join(categories))
    else:
        lines.append("- 全部标签：无")

    details = []

    # 统计 / 日期 / 标签类问题：调用 Pandas 统计函数
    if wants_stats or wants_date or wants_tags:
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

        # 统计 / 日期类问题附带最近几篇摘要；标签问题不需要附加文章
        if wants_stats or wants_date:
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
    elif not (wants_stats or wants_date or wants_tags):
        # 内容类问题：调用检索函数返回最相关的文章
        results = rag.search(question, articles, index, top_k=MAX_ARTICLES)
        if results:
            lines.append(
                "- 与问题最相关的文章："
                + "、".join(article["title"] for _, article in results)
            )
            details = [article for _, article in results]

    if details:
        lines.append("\n以下是相关文章内容：")
        for article in details:
            lines.append(_detail(article))

    return "\n".join(lines), {
        "matched_categories": matched,
        "stats": wants_stats or wants_date,
        "tags": wants_tags,
        "articles": len(details),
    }