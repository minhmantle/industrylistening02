import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import feedparser
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

st.set_page_config(page_title="Crypto Narrative Dashboard", layout="wide")
st.title("🚀 Crypto Market Narrative & Alpha Dashboard")
st.markdown("**Hybrid: News + X (Free 100%) • Real-time**")

# Sidebar Filters
st.sidebar.header("🔍 Filters")
days = st.sidebar.slider("Time Range (ngày gần nhất)", 1, 30, 7)
query = st.sidebar.text_input("Focus Keywords", "mantle OR rwa OR defi OR altseason OR hack OR funding OR ai")

# Fetch News (Primary - ổn định)
@st.cache_data(ttl=180)
def fetch_news():
    df_list = []
    # Primary API
    try:
        resp = requests.get("https://cryptocurrency.cv/api/news?limit=100", timeout=12)
        if resp.ok:
            articles = resp.json().get('articles', [])
            df = pd.DataFrame(articles)
            if not df.empty:
                for col in ['published_at', 'pubDate', 'date']:
                    if col in df.columns:
                        df['posted_at'] = pd.to_datetime(df[col], errors='coerce')
                        break
                df_list.append(df)
    except:
        pass

    # RSS Fallback
    if not df_list or df_list[0].empty:
        rss_list = ["https://cointelegraph.com/rss", "https://www.coindesk.com/arc/outboundfeeds/rss/"]
        for url in rss_list:
            try:
                feed = feedparser.parse(url)
                entries = []
                for e in feed.entries[:30]:
                    entries.append({
                        'title': e.get('title', ''),
                        'summary': e.get('summary') or e.get('description', ''),
                        'url': e.get('link'),
                        'posted_at': pd.to_datetime(e.get('published'), errors='coerce')
                    })
                df_list.append(pd.DataFrame(entries))
            except:
                continue

    if df_list:
        full = pd.concat(df_list, ignore_index=True).drop_duplicates(subset=['title'])
        full['posted_at'] = pd.to_datetime(full['posted_at'], errors='coerce')
        return full.dropna(subset=['posted_at'])
    return pd.DataFrame()

df = fetch_news()

# Filter
if not df.empty:
    cutoff = datetime.now() - timedelta(days=days)
    df['posted_at'] = df['posted_at'].dt.tz_localize(None)
    df = df[df['posted_at'] >= cutoff]

# Narrative Clustering
if not df.empty and st.button("🔄 Phân tích Key Narratives & Alpha Signals"):
    with st.spinner("Đang detect narratives..."):
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        texts = (df.get('title', '') + " " + df.get('summary', '')).fillna('').tolist()
        
        if len(texts) >= 6:
            embeddings = embedder.encode(texts, show_progress_bar=False)
            n = min(8, max(3, len(texts)//5))
            kmeans = KMeans(n_clusters=n, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embeddings)
            
            vectorizer = TfidfVectorizer(ngram_range=(1,2), stop_words='english', max_features=100)
            cluster_labels = []
            for i in range(n):
                c_texts = [texts[j] for j in range(len(texts)) if labels[j] == i]
                if len(c_texts) > 2:
                    tfidf = vectorizer.fit_transform(c_texts)
                    top = [vectorizer.get_feature_names_out()[idx] for idx in tfidf.sum(axis=0).A1.argsort()[-5:][::-1]]
                    cluster_labels.append(" | ".join(top[:4]))
                else:
                    cluster_labels.append("Other")
            
            summary = pd.DataFrame({'count': pd.Series(labels).value_counts()})
            summary['narrative'] = cluster_labels
            summary['percentage'] = (summary['count'] / len(df) * 100).round(1)
            
            st.subheader("🔥 Top Key Narratives")
            fig = px.pie(summary, names='narrative', values='count')
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(summary.sort_values('count', ascending=False))

# Top Content + Crises
st.subheader("📌 Top Articles & Potential Events")
if not df.empty:
    for _, row in df.sort_values('posted_at', ascending=False).head(15).iterrows():
        title = row.get('title', 'No title')
        with st.expander(f"**{title[:80]}...**"):
            st.write(row.get('summary', ''))
            st.caption(f"{row.get('source', 'News')} | {row.get('posted_at')}")
            if row.get('url'):
                st.markdown(f"[Đọc đầy đủ]({row['url']})")
else:
    st.warning("Chưa load được data, thử refresh.")

st.caption("Built for Minh Anh - Mantle Squad | 100% Free Hybrid Dashboard 🔥")
