"""分类预测页面（对应课程第 8 章：sklearn 机器学习实战）。

用 TF-IDF 把文章标题和正文转成特征向量，再用逻辑回归预测文章分类。
模型训练结果用 st.cache_resource 缓存，避免页面每次交互都重新训练。
"""

import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

import db

st.set_page_config(page_title="分类预测", layout="wide")

db.init_db()

st.title("分类预测")
st.caption("sklearn 实战：TF-IDF + 逻辑回归，根据标题和正文预测文章分类")


@st.cache_resource(show_spinner=False)
def train_model(version):
    """训练模型；version 变化（文章增删改）时缓存自动失效。"""
    articles = db.get_all_articles()
    texts = [f"{article['title']} {article['content']}" for article in articles]
    labels = [article["category"] for article in articles]

    # 字符级 n-gram 对中文友好，不需要先分词
    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(1, 2), max_features=5000)
    features = vectorizer.fit_transform(texts)

    # 固定随机种子，保证每次演示结果一致
    X_train, X_test, y_train, y_test = train_test_split(
        features, labels, test_size=0.3, random_state=42
    )
    model = LogisticRegression(max_iter=1000).fit(X_train, y_train)

    train_acc = accuracy_score(y_train, model.predict(X_train))
    test_acc = accuracy_score(y_test, model.predict(X_test)) if len(y_test) else 0.0
    return model, vectorizer, train_acc, test_acc, len(y_train)


articles = db.get_all_articles()

if len(articles) < 4:
    st.info("文章数量太少（至少 4 篇）才能训练模型，先去「写文章」页面多写几篇吧。")
    st.stop()

# 用文章内容作为缓存版本，任何增删改都会让模型重新训练
version = tuple(
    (article["id"], article["title"], article["category"], article["content"])
    for article in articles
)
model, vectorizer, train_acc, test_acc, train_size = train_model(version)

col1, col2, col3 = st.columns(3)
col1.metric("训练样本数", train_size)
col2.metric("训练集准确率", f"{train_acc:.0%}")
col3.metric("测试集准确率", f"{test_acc:.0%}")

st.caption("当前示例数据只有十几条，准确率仅供演示；文章越多，模型越可靠。")

st.divider()
st.subheader("输入一篇文章试试")

title = st.text_input("标题", value="记录今天的一件小事")
content = st.text_area(
    "正文",
    value="今天去图书馆借了两本书，晚上读了几页，感觉很不错。",
    height=180,
)

if st.button("预测分类", type="primary"):
    sample = vectorizer.transform([f"{title} {content}"])
    predicted = model.predict(sample)[0]
    probabilities = model.predict_proba(sample)[0]

    st.success(f"预测结果：{predicted}")

    # 按概率从高到低展示各分类的置信度
    pairs = sorted(zip(model.classes_, probabilities), key=lambda item: -item[1])
    for category, probability in pairs:
        st.write(f"{category}：{probability:.1%}")
        st.progress(float(probability))