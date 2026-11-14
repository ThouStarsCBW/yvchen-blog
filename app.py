"""首页：按发布时间倒序展示全部文章，点击标题展开正文。"""

import streamlit as st

import db

st.set_page_config(page_title="我的博客", layout="wide")

# 建表并保证有示例数据
db.init_db()

# 写文章 / 管理页面跳转回来时，展示一次操作成功的提示
flash = st.session_state.pop("flash", None)
if flash:
    st.success(flash)

st.title("我的博客")
st.caption("记录生活、技术与读书笔记（首页 · 按发布时间倒序）")

articles = db.get_all_articles()

if not articles:
    st.info("还没有文章，去左侧「写文章」页面发布第一篇吧。")
else:
    st.write(f"共 {len(articles)} 篇文章")
    for article in articles:
        # expander 标题展示标题 / 分类 / 日期，点开后显示正文
        with st.expander(
            f"{article['title']}（{article['category']} ｜ {article['created_at']}）"
        ):
            st.write(article["content"])