"""图表与统计计算模块。

包含 2 张 Matplotlib 静态图、2 张 Pyecharts 交互图，
以及基于 numpy 的月度统计和「分类 × 月份」发文矩阵。
统计逻辑全部基于传入的 Pandas DataFrame。
"""

import json

import matplotlib

# 无界面后端，在 Streamlit 环境下更稳定
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pyecharts import options as opts
from pyecharts.charts import Bar, Pie

# 按优先级列出常见中文字体：Windows / macOS / Linux
CHINESE_FONTS = [
    "Microsoft YaHei",
    "SimHei",
    "PingFang SC",
    "Heiti SC",
    "WenQuanYi Zen Hei",
    "Arial Unicode MS",
]


def apply_chinese_font():
    """设置 Matplotlib 中文字体，避免图表里的中文显示成方块。"""
    matplotlib.rcParams["font.sans-serif"] = CHINESE_FONTS
    matplotlib.rcParams["axes.unicode_minus"] = False


def _category_counts(df):
    """按分类统计文章数量，返回 (分类列表, 数量列表)。"""
    counts = df["category"].value_counts()
    return counts.index.tolist(), [int(v) for v in counts.values]


def _month_counts(df):
    """按月份统计文章数量，返回 (月份列表, 数量列表)，月份升序排列。"""
    months = df["created_at"].astype(str)
    months = months.str.slice(0, 7)  # YYYY-MM-DD -> YYYY-MM
    counts = months.value_counts().sort_index()
    return counts.index.tolist(), [int(v) for v in counts.values]


def monthly_stats(df):
    """用 numpy 计算每月发文量的均值、标准差、最高/最低值和最近月环比。"""
    months, values = _month_counts(df)
    arr = np.array(values, dtype=float)

    growth = None
    if len(arr) >= 2 and arr[-2] > 0:
        growth = float((arr[-1] - arr[-2]) / arr[-2] * 100)

    return {
        "months": months,
        "values": values,
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "max": int(np.max(arr)),
        "min": int(np.min(arr)),
        "growth": growth,
    }


def category_month_matrix(df):
    """构造「分类 × 月份」发文数量矩阵。

    返回 (分类列表, 月份列表, numpy 二维数组)，数组每一行是一个分类，
    每一列是一个月份。页面会把矩阵转成表格展示。
    """
    months = df["created_at"].astype(str).str.slice(0, 7)
    categories = sorted(df["category"].unique().tolist())
    month_labels = sorted(months.unique().tolist())

    # 用 numpy 创建全 0 矩阵，再按分类和月份累加
    matrix = np.zeros((len(categories), len(month_labels)), dtype=int)
    category_index = {name: i for i, name in enumerate(categories)}
    month_index = {name: j for j, name in enumerate(month_labels)}

    for category, month in zip(df["category"], months):
        matrix[category_index[category], month_index[month]] += 1

    return categories, month_labels, matrix


def category_bar(df):
    """Matplotlib：各分类文章数量柱状图。"""
    apply_chinese_font()
    categories, values = _category_counts(df)

    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    bars = ax.bar(categories, values, color="#4C78A8", width=0.55)
    ax.bar_label(bars, padding=3)  # 在柱子上标出具体数量
    ax.set_title("各分类文章数量")
    ax.set_xlabel("分类")
    ax.set_ylabel("文章数量")
    ax.set_ylim(0, max(values) + 1)
    fig.tight_layout()
    return fig


def monthly_line(df):
    """Matplotlib：每月发布文章数量折线图。"""
    apply_chinese_font()
    months, values = _month_counts(df)

    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.plot(months, values, marker="o", color="#F58518", linewidth=2)
    ax.set_title("每月发布文章数量")
    ax.set_xlabel("月份")
    ax.set_ylabel("文章数量")
    ax.set_ylim(0, max(values) + 1)
    ax.tick_params(axis="x", rotation=45)
    ax.grid(linestyle="--", alpha=0.4)
    fig.tight_layout()
    return fig


def category_pie_options(df):
    """Pyecharts：各分类占比饼图（支持鼠标悬停查看 tooltip）。"""
    categories, values = _category_counts(df)
    data_pair = list(zip(categories, values))

    pie = (
        Pie(init_opts=opts.InitOpts(width="100%", height="380px"))
        .add(
            series_name="文章数量",
            data_pair=data_pair,
            radius=["35%", "65%"],
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="各分类文章占比", pos_left="center"),
            legend_opts=opts.LegendOpts(orient="vertical", pos_left="left"),
            tooltip_opts=opts.TooltipOpts(
                trigger="item", formatter="{b}：{c} 篇（{d}%）"
            ),
        )
        .set_series_opts(label_opts=opts.LabelOpts(formatter="{b} {d}%"))
    )
    return json.loads(pie.dump_options())


def monthly_bar_options(df):
    """Pyecharts：每月发布数量柱状图（带 datazoom，可拖动缩放）。"""
    months, values = _month_counts(df)

    bar = (
        Bar(init_opts=opts.InitOpts(width="100%", height="380px"))
        .add_xaxis(months)
        .add_yaxis("文章数量", values, bar_width="45%")
        .set_global_opts(
            title_opts=opts.TitleOpts(title="每月发布文章数量（可缩放）", pos_left="center"),
            xaxis_opts=opts.AxisOpts(name="月份"),
            yaxis_opts=opts.AxisOpts(name="篇数"),
            tooltip_opts=opts.TooltipOpts(
                trigger="axis", axis_pointer_type="shadow"
            ),
            datazoom_opts=[opts.DataZoomOpts(type_="slider")],
        )
    )
    return json.loads(bar.dump_options())