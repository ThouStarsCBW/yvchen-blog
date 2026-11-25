"""智能问答页面（基于 RAG 检索）：检索博客文章并生成回答。

配置大模型后，会把全部博客文章一次性作为上下文交给模型；
未配置大模型时，使用本地检索结果生成回答。
"""

import hashlib

import streamlit as st

import db
import rag

st.set_page_config(page_title="智能问答", layout="wide")

db.init_db()

st.title("智能问答")
st.caption("配置大模型后，会把全部博客文章作为上下文交给模型；未配置时使用本地检索回答")

articles = db.get_all_articles()

if not articles:
    st.info("还没有文章，先导入或发布一些文章再来提问。")
    st.stop()

if rag.llm_configured():
    st.success(
        f"已检测到大模型配置，提问时会把全部 {len(articles)} 篇文章交给大模型。"
    )
else:
    st.info(
        "当前为本地检索模式。配置环境变量 `OPENAI_API_KEY`、`OPENAI_BASE_URL`、"
        "`OPENAI_MODEL` 后，可用大模型基于全部文章生成回答。"
    )


@st.cache_resource(show_spinner=False)
def build_rag_index(signature):
    """按文章内容缓存检索索引，用于展示参考文章和本地回退。"""
    return rag.build_index(db.get_all_articles())


signature = hashlib.md5(
    "\n".join(
        f"{article['id']}|{article['title']}|{article['content']}"
        for article in articles
    ).encode("utf-8")
).hexdigest()
index = build_rag_index(signature)

with st.form("rag_form"):
    question = st.text_input(
        "请输入问题", placeholder="例如：博客里有哪些关于时间管理的文章？"
    )
    submitted = st.form_submit_button("提问", type="primary")

if submitted:
    question = question.strip()
    if not question:
        st.warning("问题不能为空。")
        st.stop()

    # 检索结果只用于展示参考文章，以及大模型调用失败时的本地回退
    results = rag.search(question, articles, index, top_k=3)

    st.subheader("回答")

    if rag.llm_configured():
        with st.spinner("正在把全部博客文章交给大模型，请稍候..."):
            try:
                answer, info = rag.llm_answer_all(question, articles, timeout=120)
                prompt_tokens = info["usage"].get("prompt_tokens", "未知")
                st.caption(
                    f"回答来源：大模型（使用 {info['used_articles']} / "
                    f"{info['total_articles']} 篇文章，约 {info['chars']} 字，"
                    f"输入 tokens：{prompt_tokens}）"
                )
                if info["used_articles"] < info["total_articles"]:
                    st.warning("文章总量超过上下文预算，已优先保留较新的文章。")
            except Exception as exc:
                st.warning(f"大模型调用失败，已回退到本地检索回答：{exc}")
                answer = rag.local_answer(question, results)
                st.caption("回答来源：本地检索（回退）")
    else:
        answer = rag.local_answer(question, results)
        st.caption("回答来源：本地检索")

    st.markdown(answer)

    if results:
        st.subheader("参考文章（检索命中的前 3 篇）")
        st.caption("大模型生成回答时使用的是全部文章，这里只展示检索命中的前几篇。")
        for score, article in results:
            with st.expander(
                f"《{article['title']}》（相关度 {score:.0%}）"
            ):
                st.caption(f"{article['category']} ｜ {article['created_at']}")
                st.write(article["content"])