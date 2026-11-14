"""数据统计页面：用 Pandas 做统计，Matplotlib 与 Pyecharts 画图。"""

import streamlit as st
from streamlit_echarts import st_echarts

import charts
import db

st.set_page_config(page_title="数据统计", layout="wide")

db.init_db()

st.title("数据统计")
st.caption("用 Pandas 从 blog.db 读取文章数据后统计并绘图")

df = db.load_dataframe()

if df.empty:
    st.info("还没有文章数据，先去「写文章」页面发一篇吧。")
    st.stop()

# 把发布日期转成日期类型，方便求最大值和按月分组
df["created_at"] = df["created_at"].astype(str)
dates = df["created_at"].apply(lambda x: x[:10])

# ---------- 顶部统计卡片 ----------
col1, col2, col3 = st.columns(3)
col1.metric("总文章数", len(df))
col2.metric("分类数量", df["category"].nunique())
col3.metric("最近一篇发布日期", dates.max())

st.divider()

# ---------- Matplotlib 静态图 ----------
st.subheader("Matplotlib 静态图表")
col_bar, col_line = st.columns(2)
with col_bar:
    st.pyplot(charts.category_bar(df), use_container_width=True)
with col_line:
    st.pyplot(charts.monthly_line(df), use_container_width=True)

st.divider()

# ---------- Pyecharts 交互图 ----------
st.subheader("Pyecharts 交互图表")
col_pie, col_month = st.columns(2)
with col_pie:
    st_echarts(options=charts.category_pie_options(df), height="380px")
with col_month:
    st_echarts(options=charts.monthly_bar_options(df), height="380px")

st.caption("提示：鼠标悬停在图形上可查看具体数值，柱状图下方滑块可拖动缩放。")