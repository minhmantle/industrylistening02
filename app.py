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
import re

st.set_page_config(page_title="Crypto Narrative Dashboard", layout="wide")
st.title("🚀 Crypto Market Narrative & Alpha Dashboard (Crypto-Focused)")
st.markdown("**Hybrid News + Filter Crypto Only • 100% Free**")

# Sidebar
st.sidebar.header("🔍 Filters")
days = st.sidebar.slider("Time Range (ngày)", 1, 30, 7)
min_crypto_score = st.sidebar.slider("Crypto Focus Level", 1, 10, 5)

# Crypto keywords mạnh
CRYPTO_KEYWORDS = ["crypto", "bitcoin", "btc", "ethereum", "eth", "solana", "mantle", "rwa", "defi", "altcoin", "token", "blockchain", "web3", "onchain", "stablecoin", "ai agent", "prediction market", "quantum", "zk", "perps", "depin"]

def is_crypto_relevant(text):
    if not text:
        return False
    text_lower = text.lower()
    score = sum(1 for kw in CRYPTO_KEYWORDS if kw in text_lower)
    return score >= min_crypto_score

# Fetch data (giữ nguyên)
@st.cache_data(ttl=180)
def fetch_news():
    # ... (giữ code fetch_news cũ của mày, tao rút gọn)
    df_list = []
    try:
        resp = requests.get("https://cryptocurrency.cv/api/news?limit=100", timeout=10)
        if resp.ok:
            articles = resp.json().get('articles', [])
            df = pd.DataFrame(articles)
            df_list.append(df)
    except:
        pass
    # RSS fallback...
    return pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()

df = fetch_news()

if not df.empty:
    cutoff = datetime.now() - timedelta(days=days)
    df['posted_at'] = pd.to_datetime(df.get('published_at') or df.get('pubDate'), errors='coerce').dt.tz_localize(None)
    df = df[df['posted_at'] >= cutoff]

    # Filter crypto only
    df['combined_text'] = (df.get('title', '') + " " + df.get('summary', '')).fillna('')
    df = df[df['combined_text'].apply(is_crypto_relevant)].copy()

# Clustering
if not df.empty and st.button("🔄 Phân tích Key Narratives (Crypto Focused)"):
    with st.spinner("Clustering crypto narratives..."):
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        texts = df['combined_text'].tolist()
        
        if len(texts) >= 5:
            embeddings = embedder.encode(texts, show_progress_bar=False)
            n_clusters = min(8, max(3, len(texts)//5))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embeddings)
            
            vectorizer = TfidfVectorizer(ngram_range=(1,3), stop_words='english', max_features=200)
            cluster_labels = []
            for i in range(n_clusters):
                cluster_texts = [texts[j] for j in range(len(texts)) if labels[j] == i]
                if len(cluster_texts) > 2:
                    tfidf = vectorizer.fit_transform(cluster_texts)
                    words = vectorizer.get_feature_names_out()
                    top = [words[idx] for idx in tfidf.sum(axis=0).A1.argsort()[-6:][::-1]]
                    label = " | ".join(top[:5])
                    cluster_labels.append(label)
                else:
                    cluster_labels.append("Other")
            
            summary = pd.DataFrame({'count': pd.Series(labels).value_counts()})
            summary['narrative'] = [cluster_labels[i] for i in summary.index]
            summary['percentage'] = (summary['count'] / len(df) * 100).round(1)
            
            st.subheader("🔥 Top Crypto Narratives")
            fig = px.pie(summary, names='narrative', values='count')
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(summary.sort_values('count', ascending=False))

# Top content
st.subheader("📌 Top Crypto Articles")
if not df.empty:
    for _, row in df.sort_values('posted_at', ascending=False).head(12).iterrows():
        with st.expander(row.get('title', 'No title')[:100]):
            st.write(row.get('summary', ''))
            if row.get('url'):
                st.markdown(f"[Read]({row['url']})")
else:
    st.info("Không có content crypto mạnh trong khoảng thời gian này. Thử giảm 'Crypto Focus Level' hoặc tăng days.")

st.caption("Built for Minh Anh - Mantle Squad | Crypto-Focused Dashboard 🔥")
