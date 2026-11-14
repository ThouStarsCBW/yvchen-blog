"""爬虫模块（对应课程第 10 章：爬虫实战）。

用 requests 发送 HTTP 请求，用 BeautifulSoup 解析 HTML，
抓取 quotes.toscrape.com 上的名言素材。单独成模块便于页面调用和测试。
"""

import requests
from bs4 import BeautifulSoup

QUOTES_URL = "https://quotes.toscrape.com/"


def fetch_quotes(url=QUOTES_URL, timeout=10):
    """请求页面并解析名言列表，返回 [{text, author, tags}, ...]。"""
    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": "Mozilla/5.0 (compatible; BlogHomework/1.0)"},
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    quotes = []
    for block in soup.select("div.quote"):
        text = block.select_one("span.text").get_text(strip=True)
        author = block.select_one("small.author").get_text(strip=True)
        tags = [tag.get_text(strip=True) for tag in block.select("a.tag")]
        quotes.append({"text": text, "author": author, "tags": tags})
    return quotes