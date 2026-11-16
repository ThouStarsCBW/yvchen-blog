"""数据统计页面。

对应课程内容：
- 第 7 章：Pandas 读取数据、分组统计
- 第 6 章：numpy 均值 / 标准差 / 二维矩阵
- 第 9 章：Matplotlib 静态图
- 第 5 章：统计结果导出为 CSV / JSON 文件
"""

import json
import os

import pandas as pd
import streamlit as st
from streamlit_echarts import st_echarts

import charts
import db
import file_ops

st.set_page_config(page_title="数据统计", layout="wide")

db.init_db()

st.title("数据统计")
st.caption("Pandas 读数据、numpy 做统计、Matplotlib 与 Pyecharts 绘图、文件导出")

df = db.load_dataframe()

if df.empty:
    st.info("还没有文章数据，先去「写文章」页面发一篇吧。")
    st.stop()

# 统一日期格式，方便取最新日期
df["created_at"] = df["created_at"].astype(str)
dates = df["created_at"].apply(lambda x: x[:10])

# ---------- 顶部统计卡片 ----------
col1, col2, col3 = st.columns(3)
col1.metric("总文章数", len(df))
col2.metric("分类数量", df["category"].nunique())
col3.metric("最近一篇发布日期", dates.max())

st.divider()

# ---------- numpy 月度统计（第 6 章） ----------
st.subheader("numpy 月度统计")
stats = charts.monthly_stats(df)

col_mean, col_std, col_max, col_growth = st.columns(4)
col_mean.metric("月均发文量", f"{stats['mean']:.2f} 篇")
col_std.metric("标准差", f"{stats['std']:.2f}")
col_max.metric("单月最高", f"{stats['max']} 篇")
if stats["growth"] is None:
    col_growth.metric("较上月", "—")
else:
    col_growth.metric("较上月", f"{stats['growth']:+.1f}%")

st.caption("较上月 =（本月发文量 - 上月发文量）÷ 上月发文量；只有一个月数据时显示 —。")

# 分类 × 月份发文矩阵：numpy 二维数组转成表格展示
categories, months, matrix = charts.category_month_matrix(df)
matrix_df = pd.DataFrame(matrix, index=categories, columns=months)
matrix_df["合计"] = matrix.sum(axis=1)  # numpy 按行求和

st.write("分类 × 月份发文矩阵（numpy 二维数组）")
st.dataframe(matrix_df, width="stretch")

st.divider()

# ---------- Matplotlib 静态图（第 9 章） ----------
st.subheader("Matplotlib 静态图表")
col_bar, col_line = st.columns(2)
with col_bar:
    st.pyplot(charts.category_bar(df), width="stretch")
with col_line:
    st.pyplot(charts.monthly_line(df), width="stretch")

st.divider()

# ---------- Pyecharts 交互图 ----------
st.subheader("Pyecharts 交互图表")
col_pie, col_month = st.columns(2)
with col_pie:
    st_echarts(
        options=charts.category_pie_options(df), height="380px", key="category_pie"
    )
with col_month:
    st_echarts(
        options=charts.monthly_bar_options(df), height="380px", key="monthly_bar"
    )

st.caption("提示：鼠标悬停在图形上可查看具体数值，柱状图下方滑块可拖动缩放。")

st.divider()

# ---------- 文件导出（第 5 章） ----------
st.subheader("导出统计结果")
st.caption("下载按钮在浏览器中直接保存；点击下方按钮会把文件真正写入项目里的 exports/ 目录。")

articles = db.get_all_articles()
stats_payload = {
    "总文章数": len(df),
    "分类数量": int(df["category"].nunique()),
    "最近发布日期": dates.max(),
    "月均发文量": round(stats["mean"], 2),
    "标准差": round(stats["std"], 2),
    "单月最高": stats["max"],
    "较上月变化": None if stats["growth"] is None else round(stats["growth"], 2),
}

col_csv, col_json = st.columns(2)
with col_csv:
    st.download_button(
        "下载文章 CSV",
        data=file_ops.articles_to_csv(articles).encode("utf-8-sig"),
        file_name="articles.csv",
        mime="text/csv",
    )
with col_json:
    st.download_button(
        "下载统计 JSON",
        data=json.dumps(stats_payload, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name="stats.json",
        mime="application/json",
    )

if st.button("把文件写入 exports/ 目录"):
    csv_path = file_ops.export_articles_csv(articles)
    json_path = file_ops.export_stats_json(stats_payload)
    st.success(f"已写入：{os.path.relpath(csv_path)}")
    st.success(f"已写入：{os.path.relpath(json_path)}")