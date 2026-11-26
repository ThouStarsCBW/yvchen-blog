"""智能问答页面：先调用数据库函数查询数据，再让 AI 生成回答。"""

import hashlib

import streamlit as st

import db
import db_tools
import file_ops
import rag

st.set_page_config(page_title="智能问答", layout="wide")

db.init_db()

st.title("智能问答")
st.caption("多轮对话 + 流式输出；回答前会先调用数据库函数查询博客数据")

articles = db.get_all_articles()

if not articles:
    st.info("还没有文章，先导入或发布一些文章再来提问。")
    st.stop()

# 聊天记录优先从本地文件恢复，切换页面 / 刷新 / 重启后都不会丢失
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = file_ops.load_chat_history()

_, col_clear = st.columns([5, 1])
with col_clear:
    if st.button("清空对话"):
        st.session_state.chat_messages = []
        file_ops.clear_chat_history()
        st.rerun()


@st.cache_resource(show_spinner=False)
def build_rag_index(signature):
    """按文章内容缓存检索索引，供 DB 查询函数做内容检索。"""
    return rag.build_index(db.get_all_articles())


signature = hashlib.md5(
    "\n".join(
        f"{article['id']}|{article['title']}|{article['content']}"
        for article in articles
    ).encode("utf-8")
).hexdigest()
index = build_rag_index(signature)

# ---------- 渲染历史对话 ----------
if not st.session_state.chat_messages:
    st.caption("可以试试：博客里一共有多少篇文章？")
for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---------- 输入框（固定在页面底部） ----------
prompt = st.chat_input("请输入问题，按回车发送")
if prompt:
    question = prompt.strip()
    if not question:
        st.stop()

    # 当前问题加入历史前，先保存之前的对话作为模型上下文
    history = list(st.session_state.chat_messages)
    st.session_state.chat_messages.append({"role": "user", "content": question})
    file_ops.save_chat_history(st.session_state.chat_messages)

    with st.chat_message("user"):
        st.markdown(question)

    # 先根据用户问题调用 DB 查询 / 统计函数，得到给模型的上下文
    context, _ = db_tools.collect_db_context(question, articles, index)

    answer = ""

    with st.chat_message("assistant"):
        if rag.llm_configured():
            try:
                answer = st.write_stream(
                    rag.stream_chat_answer_with_context(
                        question, context, history, timeout=180
                    )
                )
                if not answer:
                    raise RuntimeError("模型没有返回内容")
            except Exception:
                # 流式失败时静默改为一次性回答，再失败则本地检索
                try:
                    answer, _ = rag.llm_answer_with_context(
                        question, context, history, timeout=180
                    )
                    st.markdown(answer)
                except Exception:
                    results = rag.search(question, articles, index, top_k=3)
                    answer = rag.local_answer(question, results)
                    st.markdown(answer)
        else:
            results = rag.search(question, articles, index, top_k=3)
            answer = rag.local_answer(question, results)
            st.markdown(answer)

    st.session_state.chat_messages.append(
        {"role": "assistant", "content": answer}
    )
    file_ops.save_chat_history(st.session_state.chat_messages)