import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import feedparser
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

st.set_page_config(page_title="Crypto Narrative Dashboard", layout="wide")
st.title("🚀 Crypto Market Narrative & Alpha Dashboard")
st.markdown("**Advanced Narrative Detection • Pre-defined + Semantic**")

# Sidebar
st.sidebar.header("🔍 Filters")
days = st.sidebar.slider("Time Range (ngày)", 1, 30, 7)
min_score = st.sidebar.slider("Crypto Focus Level", 1, 10, 2)

# NARRATIVES MẠNH HƠN (cập nhật theo real-time 2026)
NARRATIVES = {
    "RWA & Tokenization": ["rwa", "real world asset", "tokenized", "tokenization", "ondo", "treasury", "real estate token"],
    "AI Agents & DeFAI": ["ai agent", "agentic", "defai", "ai crypto", "autonomous agent", "bai", "x402"],
    "Stablecoins & Payments": ["stablecoin", "usdc", "usdt", "pyusd", "stable", "payment"],
    "DePIN & DePAI": ["depin", "depai", "render", "io.net", "decentralized physical"],
    "Infrastructure & L2": ["l2", "layer2", "mantle", "modular", "scaling", "rollup"],
    "Prediction Markets": ["prediction market", "polymarket", "kalshi"],
    "Privacy & ZK": ["privacy", "zk", "zero knowledge", "fhe"],
    "Perp DEXs & Derivatives": ["perp", "perpetual", "hyperliquid", "derivatives"],
    "Quantum Resistance": ["quantum", "post quantum"],
    "Meme & Launchpads": ["meme", "launchpad", "pump.fun"],
    "GameFi": ["gamefi", "play to earn"],
    "Others": []
}

def classify_narrative(text):
    if not isinstance(text, str) or len(text) < 15:
        return "Others"
    text_lower = text.lower()
    best_narr = "Others"
    max_score = 0
    for narr, keywords in NARRATIVES.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > max_score:
            max_score = score
            best_narr = narr
    return best_narr

# Fetch data
@st.cache_data(ttl=180)
def fetch_data():
    df_list = []
    try:
        resp = requests.get("https://cryptocurrency.cv/api/news?limit=150", timeout=15)
        if resp.ok:
            articles = resp.json().get('articles', []) if isinstance(resp.json(), dict) else resp.json()
            df_list.append(pd.DataFrame(articles))
    except:
        pass

    rss_feeds = ["https://cointelegraph.com/rss", "https://www.coindesk.com/arc/outboundfeeds/rss/", "https://decrypt.co/feed", "https://www.theblock.co/rss.xml"]
    for url in rss_feeds:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:50]:
                df_list.append(pd.DataFrame([{
                    'title': e.get('title', ''),
                    'summary': e.get('summary') or e.get('description', ''),
                    'url': e.get('link'),
                    'posted_at': pd.to_datetime(e.get('published') or e.get('pubDate'), errors='coerce')
                }]))
        except:
            continue

    if df_list:
        full = pd.concat(df_list, ignore_index=True)
        full = full.drop_duplicates(subset=['title'])
        full['posted_at'] = pd.to_datetime(full['posted_at'], errors='coerce')
        return full.dropna(subset=['posted_at'])
    return pd.DataFrame()

df = fetch_data()

if not df.empty:
    cutoff = datetime.now() - timedelta(days=days)
    df['posted_at'] = df['posted_at'].dt.tz_localize(None)
    df = df[df['posted_at'] >= cutoff].copy()
    
    df['combined'] = (df.get('title','') + " " + df.get('summary','')).fillna('')
    # Filter crypto
    df = df[df['combined'].str.contains('crypto|bitcoin|eth|mantle|rwa|defi|ai|stablecoin', case=False, na=False)]

    df['narrative'] = df['combined'].apply(classify_narrative)

# Analysis
if not df.empty and st.button("🔄 Phân tích Narratives"):
    with st.spinner("Đang quét narratives..."):
        summary = df['narrative'].value_counts().reset_index()
        summary.columns = ['narrative', 'count']
        summary['percentage'] = (summary['count'] / len(df) * 100).round(1)
        
        st.subheader("🔥 Top Crypto Narratives")
        fig = px.pie(summary, names='narrative', values='count')
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(summary.sort_values('count', ascending=False), use_container_width=True)

        hot = summary[summary['percentage'] > 12]
        if not hot.empty:
            st.success(f"🚨 Narratives nóng: {', '.join(hot['narrative'])}")

# Top content
st.subheader("📌 Top Content")
if not df.empty:
    for narr in df['narrative'].unique():
        subset = df[df['narrative'] == narr].head(6)
        with st.expander(f"**{narr}** ({len(subset)} content)"):
            for _, row in subset.iterrows():
                st.write(f"• {row.get('title') or row['combined'][:150]}...")
                if row.get('url'):
                    st.markdown(f"[Link]({row['url']})")
else:
    st.error("Vẫn chưa có data. Thử giảm **Crypto Focus Level** xuống **1 hoặc 2** và bấm Analyze lại.")

st.caption("Built for Minh Anh - Mantle Squad | Advanced Narrative Tracker 🔥")
