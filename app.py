import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import feedparser
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

st.set_page_config(page_title="Crypto Narrative Dashboard", layout="wide")
st.title("🚀 Crypto Market Narrative & Alpha Dashboard (Advanced)")
st.markdown("**Real-time Narrative Tracking • Pre-defined + Auto Detect**")

# Sidebar
st.sidebar.header("🔍 Filters")
days = st.sidebar.slider("Time Range (ngày)", 1, 30, 7)
min_score = st.sidebar.slider("Crypto Focus Level", 1, 10, 3)

# === PRE-DEFINED NARRATIVES ===
NARRATIVES = {
    "RWA": ["rwa", "real world asset", "tokenized", "tokenization", "treasury", "real estate"],
    "Stablecoins": ["stablecoin", "usdc", "usdt", "pyusd", "stable"],
    "Infrastructure": ["l2", "layer2", "modular", "scaling", "zk", "rollup"],
    "AI Agents": ["ai agent", "agentic", "defai", "ai crypto", "autonomous agent"],
    "Prediction Markets": ["prediction market", "polymarket", "kalshi"],
    "GameFi": ["gamefi", "play to earn", "gaming"],
    "Quantum Resistance": ["quantum", "post quantum", "quantum resistance"],
    "Perp DEXs": ["perp", "perpetual", "hyperliquid", "derivatives"],
    "Privacy & ZK": ["privacy", "zk", "zero knowledge", "fhe"],
    "Meme": ["meme", "launchpad", "pump.fun"],
    "DePIN": ["depin", "decentralized physical", "render", "io.net"],
    "Others": []
}

def classify_narrative(text):
    if not isinstance(text, str):
        return "Others"
    text_lower = text.lower()
    scores = {name: sum(1 for kw in keywords if kw in text_lower) for name, keywords in NARRATIVES.items()}
    max_narr = max(scores, key=scores.get)
    return max_narr if scores[max_narr] > 0 else "Others"

# Fetch data
@st.cache_data(ttl=180)
def fetch_data():
    # ... (giữ nguyên fetch_news + RSS như lần trước)
    df_list = []
    try:
        resp = requests.get("https://cryptocurrency.cv/api/news?limit=120", timeout=15)
        if resp.ok:
            articles = resp.json().get('articles', [])
            df_list.append(pd.DataFrame(articles))
    except:
        pass
    
    # RSS fallback
    rss_feeds = ["https://cointelegraph.com/rss", "https://www.coindesk.com/arc/outboundfeeds/rss/", "https://decrypt.co/feed"]
    for url in rss_feeds:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:40]:
                df_list.append(pd.DataFrame([{
                    'title': e.get('title', ''),
                    'summary': e.get('summary') or e.get('description', ''),
                    'url': e.get('link'),
                    'posted_at': pd.to_datetime(e.get('published'), errors='coerce')
                }]))
        except:
            continue
    
    full = pd.concat(df_list, ignore_index=True)
    full = full.drop_duplicates(subset=['title'])
    full['posted_at'] = pd.to_datetime(full['posted_at'], errors='coerce')
    return full.dropna(subset=['posted_at'])

df = fetch_data()

# Filter
if not df.empty:
    cutoff = datetime.now() - timedelta(days=days)
    df['posted_at'] = df['posted_at'].dt.tz_localize(None)
    df = df[df['posted_at'] >= cutoff].copy()
    
    df['combined'] = (df.get('title','') + " " + df.get('summary','')).fillna('')
    df = df[df['combined'].apply(lambda x: sum(1 for kw in ["crypto","bitcoin","eth","mantle","rwa","defi"] if kw in x.lower()) >= min_score)]

    # Classify
    df['narrative'] = df['combined'].apply(classify_narrative)

# Analysis
if not df.empty and st.button("🔄 Phân tích Narratives"):
    with st.spinner("Đang quét & phân loại narratives..."):
        summary = df['narrative'].value_counts().reset_index()
        summary.columns = ['narrative', 'count']
        summary['percentage'] = (summary['count'] / len(df) * 100).round(1)
        
        st.subheader("🔥 Top Crypto Narratives")
        fig = px.pie(summary, names='narrative', values='count', title="Narrative Distribution")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(summary.sort_values('count', ascending=False), use_container_width=True)

        # Hot narratives
        hot = summary[summary['percentage'] > 15]
        if not hot.empty:
            st.success("🚨 Narratives nóng nhất: " + ", ".join(hot['narrative']))

# Top content
st.subheader("📌 Top Content by Narrative")
if not df.empty:
    for narr in df['narrative'].unique():
        with st.expander(f"**{narr}** ({len(df[df['narrative']==narr])} bài)"):
            for _, row in df[df['narrative']==narr].head(5).iterrows():
                st.write(f"- {row.get('title') or row.get('combined')[:150]}...")
                if row.get('url'):
                    st.markdown(f"[Link]({row['url']})")
else:
    st.warning("Giảm Crypto Focus Level xuống 2-3 để có data.")

st.caption("Built for Minh Anh - Mantle Squad | Advanced Narrative Tracker 🔥")
