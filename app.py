"""首页：按发布时间倒序展示文章，支持分页查看。"""

import streamlit as st

import db
import pagination

st.set_page_config(page_title="我的博客", layout="wide")

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
    st.stop()

st.write(f"共 {len(articles)} 篇文章")


def reset_home_page():
    """切换每页条数后回到第一页。"""
    st.session_state["home_page"] = 1


page_size = st.selectbox(
    "每页显示",
    pagination.PAGE_SIZES,
    index=0,
    key="home_page_size",
    on_change=reset_home_page,
)

page, _ = pagination.render_pager("home", len(articles), page_size)
page_articles = pagination.paginate(articles, page, page_size)

for article in page_articles:
    # expander 标题展示标题 / 分类 / 日期，点开后显示正文
    with st.expander(
        f"{article['title']}（{article['category']} ｜ {article['created_at']}）"
    ):
        st.write(article["content"])