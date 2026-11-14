"""文章管理页面：列出所有文章，可编辑或删除（删除前需二次确认）。"""

import streamlit as st

import db

st.set_page_config(page_title="文章管理", layout="wide")

db.init_db()

flash = st.session_state.pop("flash", None)
if flash:
    st.success(flash)

st.title("文章管理")
st.caption("点击「编辑」修改文章，点击「删除」后需要再确认一次")

# 记录当前正在编辑 / 正在确认删除的文章 id
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None
if "delete_id" not in st.session_state:
    st.session_state.delete_id = None

articles = db.get_all_articles()

if not articles:
    st.info("还没有文章，去左侧「写文章」页面发布第一篇吧。")
else:
    for article in articles:
        article_id = article["id"]
        is_editing = st.session_state.edit_id == article_id
        is_deleting = st.session_state.delete_id == article_id

        # 编辑或删除时自动展开这一条，方便直接操作
        with st.expander(
            f"{article['title']}（{article['category']} ｜ {article['created_at']}）",
            expanded=is_editing or is_deleting,
        ):
            # ---------- 编辑模式 ----------
            if is_editing:
                options = list(db.CATEGORIES)
                if article["category"] not in options:
                    options.append(article["category"])

                with st.form(f"edit_form_{article_id}"):
                    new_title = st.text_input("标题", value=article["title"])
                    new_category = st.selectbox(
                        "分类",
                        options,
                        index=options.index(article["category"]),
                    )
                    new_content = st.text_area(
                        "正文", value=article["content"], height=240
                    )
                    col_save, col_cancel = st.columns(2)
                    save = col_save.form_submit_button("保存修改", type="primary")
                    cancel = col_cancel.form_submit_button("取消")

                if save:
                    if not new_title.strip() or not new_content.strip():
                        st.warning("标题和正文都不能为空。")
                    else:
                        db.update_article(
                            article_id,
                            new_title.strip(),
                            new_category,
                            new_content.strip(),
                        )
                        st.session_state.edit_id = None
                        st.session_state["flash"] = "文章已更新。"
                        st.rerun()

                if cancel:
                    st.session_state.edit_id = None
                    st.rerun()

            # ---------- 浏览模式 ----------
            else:
                st.write(article["content"])
                col_edit, col_delete = st.columns(2)
                if col_edit.button("编辑", key=f"edit_{article_id}"):
                    st.session_state.edit_id = article_id
                    st.session_state.delete_id = None
                    st.rerun()
                if col_delete.button("删除", key=f"delete_{article_id}"):
                    st.session_state.delete_id = article_id
                    st.session_state.edit_id = None
                    st.rerun()

            # ---------- 删除确认 ----------
            if is_deleting:
                st.warning(
                    f"确定要删除《{article['title']}》吗？删除后无法恢复。"
                )
                col_yes, col_no = st.columns(2)
                if col_yes.button(
                    "确认删除", key=f"confirm_{article_id}", type="primary"
                ):
                    db.delete_article(article_id)
                    st.session_state.delete_id = None
                    st.session_state["flash"] = "文章已删除。"
                    st.rerun()
                if col_no.button("取消删除", key=f"cancel_{article_id}"):
                    st.session_state.delete_id = None
                    st.rerun()