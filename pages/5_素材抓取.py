"""素材抓取页面（对应课程第 10 章：爬虫实战）。

页面负责交互，具体的请求与解析逻辑放在 crawler.py 中，
抓取结果可以保存为文章草稿。
"""

import datetime

import streamlit as st

import crawler
import db
import file_ops

st.set_page_config(page_title="素材抓取", layout="wide")

db.init_db()

st.title("素材抓取")
st.caption("requests + BeautifulSoup 抓取名言素材，可直接保存为文章草稿")

# 抓取结果放在 session_state 里，避免页面每次刷新都重新请求网站
if "quotes" not in st.session_state:
    st.session_state.quotes = []

if st.button("开始抓取", type="primary"):
    try:
        with st.spinner("正在请求网站并解析页面..."):
            st.session_state.quotes = crawler.fetch_quotes()
        st.success(f"抓取成功，共 {len(st.session_state.quotes)} 条名言")
        file_ops.append_log("爬虫", f"抓取素材 {len(st.session_state.quotes)} 条")
    except Exception as exc:
        st.error(f"抓取失败：{exc}")
        st.info("请检查网络后重试，或直接去「写文章」页面手动记录。")

quotes = st.session_state.quotes

if not quotes:
    st.info("点击上面的「开始抓取」按钮，从练习网站抓取名人名言素材。")
else:
    st.subheader("抓取结果")
    for index, quote in enumerate(quotes[:10], start=1):
        with st.expander(f"{index}. {quote['author']}：{quote['text'][:40]}..."):
            st.write(quote["text"])
            tags = "、".join(quote["tags"]) if quote["tags"] else "无"
            st.caption(f"作者：{quote['author']} ｜ 标签：{tags}")

    st.divider()
    st.subheader("保存为文章")

    index = st.selectbox(
        "选择一条素材",
        options=range(len(quotes)),
        format_func=lambda i: f"{i + 1}. {quotes[i]['author']}",
    )
    quote = quotes[index]

    title = st.text_input("文章标题", value=f"名言摘录：{quote['author']}")
    category = st.selectbox(
        "分类", db.CATEGORIES, index=db.CATEGORIES.index("随笔")
    )
    tags = "、".join(quote["tags"]) if quote["tags"] else "无"
    content = st.text_area(
        "正文",
        value=f"{quote['text']}\n\n—— {quote['author']}\n标签：{tags}",
        height=160,
    )

    if st.button("保存为文章"):
        if not title.strip() or not content.strip():
            st.warning("标题和正文不能为空。")
        else:
            db.add_article(
                title.strip(),
                category,
                content.strip(),
                datetime.date.today().strftime("%Y-%m-%d"),
            )
            st.success(f"已保存《{title.strip()}》，可以到首页查看。")