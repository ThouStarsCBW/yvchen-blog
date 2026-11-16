"""数据导入页面：读取 CSV / JSON / JSONL 文件并批量写入数据库。"""

import streamlit as st

import db
import file_ops

st.set_page_config(page_title="数据导入", layout="wide")

db.init_db()

flash = st.session_state.pop("import_flash", None)
if flash:
    st.success(flash)

st.title("数据导入")
st.caption(
    "支持 CSV、JSON、JSONL 文件；字段可用英文 title / content / category / created_at，"
    "也可用中文 标题 / 正文 / 分类 / 发布日期"
)

uploaded = st.file_uploader(
    "选择文件",
    type=["csv", "json", "jsonl", "ndjson"],
)

if uploaded is None:
    st.info(
        "还没有选择文件。可以先在「数据统计」页下载文章 CSV，修改后在这里导入；"
        "也可以直接上传自己准备的数据文件。"
    )
    st.stop()

raw = uploaded.getvalue()
try:
    records = file_ops.parse_import_file(raw, uploaded.name)
except Exception as exc:
    st.error(f"文件解析失败：{exc}")
    st.stop()

articles, skipped = file_ops.normalize_article_records(records)

if not articles:
    st.warning("没有解析到有效文章，请检查字段名，以及标题和正文是否为空。")
    st.stop()

# 标题重复的记录会跳过，避免重复导入
existing_titles = db.get_existing_titles()
new_articles = [a for a in articles if a["title"] not in existing_titles]
duplicate_count = len(articles) - len(new_articles)

col1, col2, col3 = st.columns(3)
col1.metric("解析记录", len(records))
col2.metric("可导入", len(new_articles))
col3.metric("跳过（重复/缺字段）", skipped + duplicate_count)

st.subheader("数据预览（前 10 条）")
st.dataframe(articles[:10], width="stretch")

if duplicate_count:
    st.caption(f"其中有 {duplicate_count} 条与现有文章标题重复，导入时会自动跳过。")

if st.button("确认导入", type="primary", disabled=not new_articles):
    count = db.bulk_add_articles(new_articles)
    st.session_state["import_flash"] = f"成功导入 {count} 篇文章，可到首页查看。"
    st.rerun()

if not new_articles:
    st.info("当前没有可导入的新文章。")