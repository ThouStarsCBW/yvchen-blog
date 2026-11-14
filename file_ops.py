"""文件操作模块（对应课程第 5 章：文件操作）。

集中处理两类文件读写：
1. 操作日志 blog.log：用追加模式 "a" 写入，记录新增 / 修改 / 删除 / 抓取 / 导出。
2. 统计结果导出 exports/：文章 CSV 与统计 JSON，用 open() + csv / json 模块写文件。
"""

import csv
import io
import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, "blog.log")
EXPORT_DIR = os.path.join(BASE_DIR, "exports")


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