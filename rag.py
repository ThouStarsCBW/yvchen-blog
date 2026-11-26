"""智能问答模块（RAG）：把博客文章作为上下文交给大模型回答。

两种模式：
1. 本地检索模式：没有配置大模型时，用 jieba + TF-IDF 检索最相关的文章并给出摘要。
2. 全量上下文模式：配置 OPENAI_API_KEY 后，把全部文章一次性作为上下文交给大模型，
   由模型基于所有博客内容生成回答，而不是只发送检索到的前几篇。
"""

import json
import math
import os
import urllib.request
from collections import Counter
from pathlib import Path

try:
    from dotenv import load_dotenv

    # 优先读取项目根目录的 .env；命令行已有的环境变量不会被覆盖
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

import jieba

from text_utils import STOPWORDS

# 全量上下文的最大字符数，防止文章过多时超过模型上下文窗口
MAX_CONTEXT_CHARS = 100000


def tokenize(text):
    """中文分词，并过滤停用词、单字和纯数字。"""
    tokens = []
    for word in jieba.cut(str(text)):
        word = word.strip()
        if len(word) > 1 and word not in STOPWORDS and not word.isdigit():
            tokens.append(word)
    return tokens


def build_index(articles):
    """基于文章标题和正文构建轻量 TF-IDF 索引。"""
    docs = [tokenize(f"{article['title']} {article['content']}") for article in articles]

    doc_freq = Counter()
    for tokens in docs:
        doc_freq.update(set(tokens))

    total = len(docs)
    idf = {
        term: math.log((total + 1) / (count + 1)) + 1
        for term, count in doc_freq.items()
    }

    vectors = []
    for tokens in docs:
        term_freq = Counter(tokens)
        vector = {
            term: (1 + math.log(count)) * idf.get(term, 1.0)
            for term, count in term_freq.items()
        }
        norm = math.sqrt(sum(value * value for value in vector.values())) or 1.0
        vectors.append((vector, norm))

    return {"idf": idf, "vectors": vectors}


def search(question, articles, index, top_k=3):
    """按余弦相似度返回最相关的文章列表 [(相似度, 文章), ...]。"""
    query_tokens = tokenize(question)
    if not query_tokens:
        return []

    term_freq = Counter(query_tokens)
    idf = index["idf"]
    query_vector = {
        term: (1 + math.log(count)) * idf.get(term, 1.0)
        for term, count in term_freq.items()
    }
    query_norm = math.sqrt(sum(value * value for value in query_vector.values())) or 1.0

    scored = []
    for article, (vector, norm) in zip(articles, index["vectors"]):
        dot = sum(
            query_vector.get(term, 0.0) * vector.get(term, 0.0)
            for term in query_vector
        )
        if dot <= 0:
            continue
        scored.append((dot / (query_norm * norm), article))

    scored.sort(key=lambda item: -item[0])
    return scored[:top_k]


def local_answer(question, results):
    """没有配置大模型时，用检索到的文章拼出回答。"""
    if not results:
        return "博客里没有找到和这个问题相关的文章，可以换个关键词再试试。"

    lines = ["根据博客中的相关文章，可以这样回答："]
    for score, article in results:
        summary = " ".join(article["content"].split())[:120]
        lines.append(
            f"- 《{article['title']}》（{article['category']}，"
            f"{article['created_at']}，相关度 {score:.0%}）：{summary}..."
        )
    return "\n".join(lines)


def llm_configured():
    """是否配置了可用的大模型 API Key。"""
    return bool(os.environ.get("OPENAI_API_KEY"))


def build_full_context(articles, max_chars=MAX_CONTEXT_CHARS):
    """把全部文章拼接成上下文文本。

    文章按传入顺序（数据库里是发布日期倒序）拼接；超过 max_chars 时
    保留靠前（较新）的文章，返回实际使用的文章列表和字符数。
    """
    parts = []
    used_articles = []
    total_chars = 0

    for article in articles:
        block = (
            f"《{article['title']}》（{article['category']}，{article['created_at']}）\n"
            f"{article['content']}"
        )
        if parts and total_chars + len(block) > max_chars:
            break
        parts.append(block)
        used_articles.append(article)
        total_chars += len(block)

    return "\n\n".join(parts), used_articles, total_chars


def _call_llm(question, context, timeout):
    """调用 OpenAI 兼容接口，返回 (回答, usage)。"""
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    prompt = (
        "你是博客助手。请只根据下面的博客文章回答问题；"
        "如果资料里没有答案，就直接说没有找到，不要编造。\n\n"
        f"博客文章：\n{context}\n\n问题：{question}\n回答："
    )
    # 不传 temperature：部分模型（如火山 Ark coding 模型）只允许默认值
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))

    return data["choices"][0]["message"]["content"].strip(), data.get("usage", {})


def llm_answer(question, results, timeout=60):
    """用检索到的少量文章生成回答（保留给本地回退或少量上下文场景）。"""
    context = "\n\n".join(
        f"《{article['title']}》（{article['category']}，{article['created_at']}）\n"
        f"{article['content']}"
        for _, article in results
    )
    answer, _ = _call_llm(question, context, timeout)
    return answer


def llm_answer_all(question, articles, max_chars=MAX_CONTEXT_CHARS, timeout=120):
    """把全部文章作为上下文交给大模型，返回 (回答, 上下文信息)。"""
    context, used_articles, total_chars = build_full_context(articles, max_chars)
    answer, usage = _call_llm(question, context, timeout)
    return answer, {
        "used_articles": len(used_articles),
        "total_articles": len(articles),
        "chars": total_chars,
        "usage": usage,
    }

def _stream_completion(messages, timeout=180):
    """调用 OpenAI 兼容接口的流式接口，逐段 yield 文本内容。"""
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    payload = {"model": model, "messages": messages, "stream": True}
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8", errors="ignore").strip()
            if not line or not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
            except json.JSONDecodeError:
                continue
            choices = chunk.get("choices") or []
            if not choices:
                continue
            # 只取最终回答内容，忽略部分模型返回的 reasoning_content
            content = (choices[0].get("delta") or {}).get("content")
            if content:
                yield content


def stream_chat_answer(
    question, articles, history, max_chars=MAX_CONTEXT_CHARS, timeout=180
):
    """多轮对话 + 全量上下文：把全部文章作为 system 消息，流式生成回答。

    history 是之前的对话消息列表（不含当前问题），只带最近 8 条，
    避免对话历史把上下文撑爆。
    """
    context, _, _ = build_full_context(articles, max_chars)
    messages = [
        {
            "role": "system",
            "content": (
                "你是博客助手。请只根据下面的博客文章回答用户问题；"
                "如果资料里没有答案，就直接说没有找到，不要编造。\n\n"
                f"博客文章：\n{context}"
            ),
        }
    ]
    for message in history[-8:]:
        messages.append({"role": message["role"], "content": message["content"]})
    messages.append({"role": "user", "content": question})

    got_content = False
    for chunk in _stream_completion(messages, timeout=timeout):
        got_content = True
        yield chunk
    if not got_content:
        raise RuntimeError("模型没有返回流式内容")

def stream_chat_answer_with_context(question, context, history=None, timeout=180):
    """用外部传入的上下文（来自 DB 查询函数）流式生成回答。

    context 由 db_tools.collect_db_context() 根据问题调用数据库函数后生成。
    """
    history = history or []
    messages = [
        {
            "role": "system",
            "content": (
                "你是博客助手。请只根据下面的数据库查询结果回答用户问题；"
                "如果资料里没有答案，就直接说没有找到，不要编造。\n\n"
                f"{context}"
            ),
        }
    ]
    for message in history[-8:]:
        messages.append({"role": message["role"], "content": message["content"]})
    messages.append({"role": "user", "content": question})

    got_content = False
    for chunk in _stream_completion(messages, timeout=timeout):
        got_content = True
        yield chunk
    if not got_content:
        raise RuntimeError("模型没有返回流式内容")


def llm_answer_with_context(question, context, history=None, timeout=120):
    """用外部上下文一次性生成回答（流式失败时回退）。"""
    chunks = list(
        stream_chat_answer_with_context(
            question, context, history, timeout=timeout
        )
    )
    return "".join(chunks), {}