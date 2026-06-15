import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import feedparser
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
import numpy as np

st.set_page_config(page_title="Crypto Narrative Dashboard", layout="wide")
st.title("🚀 Crypto Narrative & Alpha Dashboard (X-style)")
st.markdown("**Multi RSS + Strong Semantic Detection**")

st.sidebar.header("Filters")
days = st.sidebar.slider("Time Range (ngày)", 1, 30, 7)
focus = st.sidebar.slider("Focus Level", 1, 5, 2)

# Narrative seeds mạnh
NARRATIVE_SEEDS = {
    "RWA & Tokenization": "rwa tokenized real world asset ondo blackrock",
    "AI Agents": "ai agent defai autonomous bai crypto ai",
    "DePIN": "depin depai render io.net physical infrastructure",
    "L2 & Infrastructure": "mantle layer2 l2 modular scaling",
    "Stablecoins": "stablecoin usdc usdt circle tether",
    "Prediction Markets": "polymarket prediction market",
    "Privacy & ZK": "zk zero knowledge privacy",
    "Perps & Derivatives": "perp perpetual hyperliquid",
    "Meme Coins": "meme pump.fun launchpad",
    "Others": ""
}

@st.cache_resource
def get_embedder():
    return SentenceTransformer('all-MiniLM-L6-v2')

embedder = get_embedder()
narr_emb = {k: embedder.encode(v) for k, v in NARRATIVE_SEEDS.items()}

def get_narrative(text):
    if len(text) < 30:
        return "Others"
    emb = embedder.encode(text)
    best = max(narr_emb, key=lambda x: np.dot(emb, narr_emb[x]))
    return best

# Fetch data từ nhiều nguồn mạnh
@st.cache_data(ttl=60)
def fetch_data():
    articles = []
    feeds = [
        "https://cointelegraph.com/rss",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://decrypt.co/feed",
        "https://www.theblock.co/rss.xml",
        "https://bitcoinmagazine.com/feed"
    ]
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                articles.append({
                    'title': entry.get('title', ''),
                    'summary': entry.get('summary') or entry.get('description', ''),
                    'url': entry.get('link'),
                    'posted_at': pd.to_datetime(entry.get('published'), errors='coerce')
                })
        except:
            continue
    return pd.DataFrame(articles)

df = fetch_data()

if not df.empty:
    cutoff = datetime.now() - timedelta(days=days)
    df = df[df['posted_at'] >= cutoff].copy()
    df['combined'] = (df['title'] + " " + df['summary']).fillna('')
    
    # Filter crypto
    df = df[df['combined'].str.contains('crypto|bitcoin|eth|mantle|rwa|defi|ai|stable|zk|depin|perp|token', case=False, na=False)]

    df['narrative'] = df['combined'].apply(get_narrative)

if not df.empty and st.button("🔄 Phân tích Narratives"):
    summary = df['narrative'].value_counts().reset_index()
    summary.columns = ['narrative', 'count']
    summary['percentage'] = (summary['count'] / len(df) * 100).round(1)
    
    st.subheader("🔥 Top Narratives")
    fig = px.pie(summary, names='narrative', values='count')
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(summary.sort_values('count', ascending=False))

st.subheader("📌 Recent Content")
if not df.empty:
    for _, row in df.sort_values('posted_at', ascending=False).head(15).iterrows():
        with st.expander(row['title'][:100]):
            st.write(row['summary'][:400])
            st.markdown(f"[Link]({row['url']})")
else:
    st.error("Vẫn chưa có data. Thử giảm Focus Level xuống 1")

st.caption("Built for Minh Anh - Mantle Squad 🔥")
