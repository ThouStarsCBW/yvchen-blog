"""文章管理页面：按分类（标签）/日期筛选，支持批量删除、逐篇编辑与删除。"""

import streamlit as st

import db
import file_ops

st.set_page_config(page_title="文章管理", layout="wide")

db.init_db()

flash = st.session_state.pop("flash", None)
if flash:
    st.success(flash)

st.title("文章管理")
st.caption("先按分类（标签）和日期筛选，勾选后可批量删除；也可以逐篇编辑或删除")

# 各种交互状态都放在 session_state 里
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None
if "delete_id" not in st.session_state:
    st.session_state.delete_id = None
if "bulk_delete_ids" not in st.session_state:
    st.session_state.bulk_delete_ids = None

articles = db.get_all_articles()

if not articles:
    st.info("还没有文章，去左侧「写文章」页面发布第一篇吧。")
    st.stop()

# ---------- 筛选区 ----------
st.subheader("筛选文章")
col_category, col_start, col_end = st.columns(3)

# 用集合去重得到数据库里实际出现的分类
all_categories = sorted({article["category"] for article in articles})
selected_categories = col_category.multiselect("按分类（标签）筛选", all_categories)
start_date = col_start.date_input("开始日期（可留空）", value=None)
end_date = col_end.date_input("结束日期（可留空）", value=None)

filtered = articles
if selected_categories:
    filtered = [a for a in filtered if a["category"] in selected_categories]
if start_date:
    start = start_date.strftime("%Y-%m-%d")
    filtered = [a for a in filtered if a["created_at"] >= start]
if end_date:
    end = end_date.strftime("%Y-%m-%d")
    filtered = [a for a in filtered if a["created_at"] <= end]

st.write(f"共 {len(articles)} 篇文章，当前筛选出 {len(filtered)} 篇")

if not filtered:
    st.info("当前筛选条件下没有文章，换个条件试试。")
    st.stop()

# ---------- 全选 / 取消全选 ----------
col_all, col_none, _ = st.columns([1, 1, 3])
if col_all.button("全选当前结果"):
    for article in filtered:
        st.session_state[f"select_{article['id']}"] = True
    st.rerun()
if col_none.button("取消全选"):
    for article in filtered:
        st.session_state[f"select_{article['id']}"] = False
    st.rerun()

# ---------- 文章列表 ----------
selected_ids = []

for article in filtered:
    article_id = article["id"]
    is_editing = st.session_state.edit_id == article_id
    is_deleting = st.session_state.delete_id == article_id

    col_check, col_body = st.columns([0.1, 0.9])
    checked = col_check.checkbox(
        "选择", key=f"select_{article_id}", label_visibility="collapsed"
    )
    if checked:
        selected_ids.append(article_id)

    with col_body:
        # 编辑或删除时自动展开这一条，方便直接操作
        with st.expander(
            f"{article['title']}（{article['category']} ｜ {article['created_at']}）",
            expanded=is_editing or is_deleting,
        ):
            # ---------- 编辑模式 ----------
            if is_editing:
                options = db.get_available_categories()
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

            # ---------- 单篇删除确认 ----------
            if is_deleting:
                st.warning(
                    f"确定要删除《{article['title']}》吗？删除后无法恢复。"
                )
                col_yes, col_no = st.columns(2)
                if col_yes.button(
                    "确认删除", key=f"confirm_{article_id}", type="primary"
                ):
                    db.delete_article(article_id)
                    st.session_state.pop(f"select_{article_id}", None)
                    st.session_state.delete_id = None
                    st.session_state["flash"] = "文章已删除。"
                    st.rerun()
                if col_no.button("取消删除", key=f"cancel_{article_id}"):
                    st.session_state.delete_id = None
                    st.rerun()

st.divider()

# ---------- 批量删除 ----------
if selected_ids:
    st.info(f"已选中 {len(selected_ids)} 篇文章")
    if st.button(f"批量删除选中的 {len(selected_ids)} 篇", type="primary"):
        st.session_state.bulk_delete_ids = selected_ids
        st.rerun()
else:
    st.caption("勾选文章后可以批量删除。")

if st.session_state.bulk_delete_ids:
    ids = st.session_state.bulk_delete_ids
    st.warning(f"确定删除选中的 {len(ids)} 篇文章吗？删除后无法恢复。")
    col_yes, col_no = st.columns(2)
    if col_yes.button("确认批量删除", type="primary"):
        count = db.bulk_delete_articles(ids)
        for article_id in ids:
            st.session_state.pop(f"select_{article_id}", None)
        st.session_state.bulk_delete_ids = None
        st.session_state["flash"] = f"已删除 {count} 篇文章。"
        st.rerun()
    if col_no.button("取消批量删除"):
        st.session_state.bulk_delete_ids = None
        st.rerun()

st.divider()

# ---------- 操作日志（第 5 章：读取文件） ----------
with st.expander("最近的操作日志（blog.log）"):
    logs = file_ops.read_recent_logs(10)
    if logs:
        st.code("\n".join(logs), language="text")
    else:
        st.info("还没有操作日志，新增或修改文章后会自动记录。")