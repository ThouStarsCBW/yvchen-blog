"""文件操作模块（对应课程第 5 章：文件操作）。

集中处理三类文件读写：
1. 操作日志 blog.log：追加写入、读取最近日志。
2. 统计结果导出 exports/：文章 CSV、统计 JSON。
3. 数据导入：CSV / JSON / JSONL 解析成统一的文章记录。
"""

import csv
import io
import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, "blog.log")
EXPORT_DIR = os.path.join(BASE_DIR, "exports")

# 导入文件兼容的字段名：英文优先，其次中文
FIELD_ALIASES = {
    "title": ("title", "标题"),
    "content": ("content", "正文", "内容"),
    "category": ("category", "分类"),
    "created_at": ("created_at", "发布日期", "日期", "date"),
}


def append_log(action, detail=""):
    """向 blog.log 追加一行操作日志，追加模式不会覆盖旧内容。"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as file:
        file.write(f"{timestamp}\t{action}\t{detail}\n")


def read_recent_logs(limit=10):
    """读取最近 limit 行日志，按时间倒序返回；文件不存在时返回空列表。"""
    if not os.path.exists(LOG_PATH):
        return []
    with open(LOG_PATH, "r", encoding="utf-8") as file:
        lines = file.readlines()
    return [line.rstrip("\n") for line in lines[-limit:]][::-1]


def articles_to_csv(articles):
    """把文章列表转成 CSV 文本（用于页面下载）。"""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "标题", "分类", "发布日期", "正文"])
    for article in articles:
        writer.writerow(
            [
                article["id"],
                article["title"],
                article["category"],
                article["created_at"],
                article["content"],
            ]
        )
    return buffer.getvalue()


def export_articles_csv(articles, filename="articles.csv"):
    """把文章列表写成 CSV 文件，返回文件路径。utf-8-sig 便于 Excel 打开中文。"""
    os.makedirs(EXPORT_DIR, exist_ok=True)
    path = os.path.join(EXPORT_DIR, filename)
    with open(path, "w", encoding="utf-8-sig", newline="") as file:
        file.write(articles_to_csv(articles))
    append_log("导出", f"文章数据导出为 {filename}")
    return path


def export_stats_json(stats, filename="stats.json"):
    """把统计结果写成 JSON 文件，返回文件路径。"""
    os.makedirs(EXPORT_DIR, exist_ok=True)
    path = os.path.join(EXPORT_DIR, filename)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(stats, file, ensure_ascii=False, indent=2)
    append_log("导出", f"统计数据导出为 {filename}")
    return path


def parse_import_file(raw, filename):
    """把上传文件的字节内容解析成记录列表，支持 CSV / JSON / JSONL。"""
    name = filename.lower()

    # CSV：用 DictReader 把每行转成字典
    if name.endswith(".csv"):
        text = raw.decode("utf-8-sig")
        return list(csv.DictReader(io.StringIO(text)))

    # JSONL：每行一个 JSON 对象
    if name.endswith(".jsonl") or name.endswith(".ndjson"):
        text = raw.decode("utf-8")
        return [json.loads(line) for line in text.splitlines() if line.strip()]

    # JSON：支持数组，或 {"articles": [...]} / {"data": [...]}
    if name.endswith(".json"):
        data = json.loads(raw.decode("utf-8"))
        if isinstance(data, dict):
            data = data.get("articles", data.get("data", []))
        if not isinstance(data, list):
            raise ValueError("JSON 文件需要是数组，或包含 articles 数组")
        return data

    raise ValueError("只支持 .csv、.json、.jsonl 文件")


def _pick(record, field):
    """按中英文字段名从记录里取值，取不到返回空字符串。"""
    for key in FIELD_ALIASES[field]:
        if key in record and str(record[key]).strip():
            return str(record[key]).strip()
    return ""


def normalize_article_records(records, today=None):
    """把不同字段名的记录统一成文章格式，返回 (有效记录列表, 跳过条数)。"""
    today = today or datetime.now().strftime("%Y-%m-%d")
    articles = []
    skipped = 0

    for record in records:
        if not isinstance(record, dict):
            skipped += 1
            continue

        title = _pick(record, "title")
        content = _pick(record, "content")
        if not title or not content:
            skipped += 1
            continue

        category = _pick(record, "category") or "随笔"

        # 日期必须是 YYYY-MM-DD，否则用今天
        created_at = _pick(record, "created_at")
        try:
            datetime.strptime(created_at, "%Y-%m-%d")
        except ValueError:
            created_at = today

        articles.append(
            {
                "title": title,
                "category": category,
                "content": content,
                "created_at": created_at,
            }
        )

    return articles, skipped