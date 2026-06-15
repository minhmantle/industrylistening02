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
st.title("🚀 Crypto Market Narrative & Alpha Dashboard (Crypto-Focused)")
st.markdown("**Hybrid News + Strong Crypto Filter • 100% Free**")

# Sidebar
st.sidebar.header("🔍 Filters")
days = st.sidebar.slider("Time Range (ngày)", 1, 30, 7)
min_crypto_score = st.sidebar.slider("Crypto Focus Level (thấp hơn = nhiều data hơn)", 1, 10, 3)

# Crypto keywords mạnh & rộng
CRYPTO_KEYWORDS = [
    "crypto", "bitcoin", "btc", "ethereum", "eth", "solana", "sol", "mantle", "rwa", "defi", 
    "altcoin", "token", "blockchain", "web3", "onchain", "stablecoin", "ai agent", "prediction market",
    "quantum", "zk", "perps", "depin", "altseason", "hack", "funding", "tokenized", "layer2", "l2"
]

def is_crypto_relevant(text):
    if not isinstance(text, str) or len(text) < 10:
        return False
    text_lower = text.lower()
    score = sum(1 for kw in CRYPTO_KEYWORDS if kw in text_lower)
    return score >= min_crypto_score

# Fetch News - ĐÃ FIX HOÀN CHỈNH
@st.cache_data(ttl=180)
def fetch_news():
    df_list = []
    # Primary API
    try:
        resp = requests.get("https://cryptocurrency.cv/api/news?limit=120", timeout=15)
        if resp.ok:
            articles = resp.json().get('articles', []) if isinstance(resp.json(), dict) else resp.json()
            df = pd.DataFrame(articles)
            if not df.empty:
                for col in ['published_at', 'pubDate', 'date', 'published']:
                    if col in df.columns:
                        df['posted_at'] = pd.to_datetime(df[col], errors='coerce')
                        break
                df_list.append(df)
    except:
        st.sidebar.warning("Primary API timeout")

    # RSS Fallback
    if not df_list or df_list[0].empty:
        rss_feeds = [
            "https://cointelegraph.com/rss",
            "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "https://decrypt.co/feed"
        ]
        for url in rss_feeds:
            try:
                feed = feedparser.parse(url)
                entries = []
                for entry in feed.entries[:40]:
                    entries.append({
                        'title': entry.get('title', ''),
                        'summary': entry.get('summary') or entry.get('description', ''),
                        'url': entry.get('link'),
                        'posted_at': pd.to_datetime(entry.get('published') or entry.get('pubDate'), errors='coerce')
                    })
                if entries:
                    df_list.append(pd.DataFrame(entries))
            except:
                continue

    if df_list:
        full_df = pd.concat(df_list, ignore_index=True)
        full_df = full_df.drop_duplicates(subset=['title'])
        full_df['posted_at'] = pd.to_datetime(full_df['posted_at'], errors='coerce')
        return full_df.dropna(subset=['posted_at'])
    return pd.DataFrame()

df = fetch_news()

# Filter time + Crypto only
if not df.empty:
    cutoff = datetime.now() - timedelta(days=days)
    df['posted_at'] = df['posted_at'].dt.tz_localize(None)
    df = df[df['posted_at'] >= cutoff].copy()

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
                    cluster_labels.append(" | ".join(top[:5]))
                else:
                    cluster_labels.append("Other")
            
            summary = pd.DataFrame({'count': pd.Series(labels).value_counts()})
            summary['narrative'] = [cluster_labels[i] for i in summary.index]
            summary['percentage'] = (summary['count'] / len(df) * 100).round(1)
            
            st.subheader("🔥 Top Crypto Narratives")
            fig = px.pie(summary, names='narrative', values='count')
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(summary.sort_values('count', ascending=False), use_container_width=True)
        else:
            st.warning("Không đủ data để cluster. Thử giảm Crypto Focus Level.")

# Top Articles
st.subheader("📌 Top Crypto Articles & Signals")
if not df.empty:
    for _, row in df.sort_values('posted_at', ascending=False).head(15).iterrows():
        title = row.get('title', row.get('combined_text', '')[:80])
        with st.expander(f"**{title}**"):
            st.write(row.get('summary', row.get('combined_text', ''))[:500])
            st.caption(f"{row.get('posted_at')} | Score: {sum(1 for kw in CRYPTO_KEYWORDS if kw in row['combined_text'].lower())}")
            if row.get('url'):
                st.markdown(f"[Đọc đầy đủ]({row['url']})")
else:
    st.error("**Không có content crypto nào.** Thử giảm **Crypto Focus Level** xuống 2 hoặc 3 và refresh.")

st.caption("Built for Minh Anh - Mantle Squad | Crypto-Focused 🔥")
