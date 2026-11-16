"""分页工具：首页和文章管理页共用。"""

import streamlit as st

# 每页条数选项
PAGE_SIZES = [10, 20, 50, 100]


def total_pages_for(total_items, page_size):
    """计算总页数，至少 1 页。"""
    return max(1, (total_items + page_size - 1) // page_size)


def get_page(key, total_pages):
    """读取并修正当前页码，保证在 1 ~ 总页数之间。"""
    page = st.session_state.get(key, 1)
    page = min(max(int(page), 1), total_pages)
    st.session_state[key] = page
    return page


def render_pager(key_prefix, total_items, page_size):
    """渲染上一页 / 下一页和页码信息，返回 (当前页, 总页数)。"""
    total_pages = total_pages_for(total_items, page_size)
    page = get_page(f"{key_prefix}_page", total_pages)

    col_prev, col_info, col_next = st.columns([1, 2, 1])
    if col_prev.button("上一页", key=f"{key_prefix}_prev", disabled=page <= 1):
        st.session_state[f"{key_prefix}_page"] = page - 1
        st.rerun()
    col_info.write(f"第 {page} / {total_pages} 页，共 {total_items} 条")
    if col_next.button("下一页", key=f"{key_prefix}_next", disabled=page >= total_pages):
        st.session_state[f"{key_prefix}_page"] = page + 1
        st.rerun()

    return page, total_pages


def paginate(items, page, page_size):
    """按页码切出当前页的数据。"""
    start = (page - 1) * page_size
    return items[start:start + page_size]