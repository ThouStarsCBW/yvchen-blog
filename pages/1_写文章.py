"""写文章页面：填写表单，提交后写入数据库并跳回首页。"""

import datetime

import streamlit as st

import db

st.set_page_config(page_title="写文章", layout="centered")

db.init_db()

st.title("写文章")
st.caption("标题、分类、正文都填好后点击「发布文章」")

# 标签从数据库动态读取，导入的新标签会自动出现在下拉里
categories = db.get_available_categories()

with st.form("write_form"):
    title = st.text_input("标题", max_chars=60)
    selected = st.selectbox("分类", categories + ["自定义新标签"])
    custom = ""
    if selected == "自定义新标签":
        custom = st.text_input("新标签名称", max_chars=20)
    created_at = st.date_input("发布日期", value=datetime.date.today())
    content = st.text_area("正文", height=280)
    submitted = st.form_submit_button("发布文章", type="primary")

if submitted:
    category = custom.strip() if selected == "自定义新标签" else selected

    if not title.strip() or not content.strip():
        st.warning("标题和正文都不能为空。")
    elif not category:
        st.warning("新标签名称不能为空。")
    else:
        # 日期统一存成 YYYY-MM-DD 字符串，方便排序和统计
        db.add_article(
            title.strip(),
            category,
            content.strip(),
            created_at.strftime("%Y-%m-%d"),
        )
        # 跳转后由首页读取这条提示并展示
        st.session_state["flash"] = f"文章《{title.strip()}》发布成功！"
        st.switch_page("app.py")