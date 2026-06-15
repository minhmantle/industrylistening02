import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import feedparser
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
import numpy as np

st.set_page_config(page_title="Crypto Narrative Dashboard", layout="wide")
st.title("🚀 Crypto Market Narrative & Alpha Dashboard (Semantic Trained)")
st.markdown("**Semantic + Keyword Detection • Chính xác hơn**")

# Sidebar
st.sidebar.header("🔍 Filters")
days = st.sidebar.slider("Time Range (ngày)", 1, 30, 7)
min_score = st.sidebar.slider("Crypto Focus Level", 1, 10, 2)

# Pre-defined Narratives (đã train semantic)
NARRATIVE_SEEDS = {
    "RWA & Tokenization": "RWA real world asset tokenized treasury ondofinance blackrock tokenization",
    "AI Agents & DeFAI": "AI agent autonomous agent defai crypto ai bai x402 intelligent agent",
    "Stablecoins & Payments": "stablecoin usdc usdt pyusd circle tether payment rail",
    "DePIN & Physical Infra": "depin depai render io.net decentralized physical infrastructure",
    "Infrastructure & L2": "mantle layer2 l2 modular blockchain scaling rollup",
    "Prediction Markets": "prediction market polymarket kalshi election bet",
    "Privacy & ZK": "zero knowledge zk proof privacy fhe",
    "Perp DEXs & Derivatives": "perp perpetual hyperliquid derivatives leverage trading",
    "Quantum Resistance": "quantum post-quantum cryptography resistant",
    "Meme & Launchpads": "meme coin pump.fun launchpad solana meme",
    "GameFi": "gamefi play to earn gaming blockchain game",
    "Others": "crypto general news"
}

@st.cache_resource
def get_embedder():
    return SentenceTransformer('all-MiniLM-L6-v2')

embedder = get_embedder()

# Pre-compute narrative embeddings
narrative_embeddings = {name: embedder.encode(seed) for name, seed in NARRATIVE_SEEDS.items()}

def classify_narrative_semantic(text):
    if not isinstance(text, str) or len(text) < 20:
        return "Others"
    text_emb = embedder.encode(text)
    scores = {name: np.dot(text_emb, emb) / (np.linalg.norm(text_emb) * np.linalg.norm(emb)) 
              for name, emb in narrative_embeddings.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0.35 else "Others"   # threshold

# Fetch data
@st.cache_data(ttl=180)
def fetch_data():
    df_list = []
    try:
        resp = requests.get("https://cryptocurrency.cv/api/news?limit=150", timeout=15)
        if resp.ok:
            articles = resp.json().get('articles', [])
            df_list.append(pd.DataFrame(articles))
    except:
        pass

    rss = ["https://cointelegraph.com/rss", "https://www.coindesk.com/arc/outboundfeeds/rss/", "https://decrypt.co/feed", "https://www.theblock.co/rss.xml"]
    for url in rss:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:50]:
                df_list.append(pd.DataFrame([{
                    'title': e.get('title',''),
                    'summary': e.get('summary') or e.get('description',''),
                    'url': e.get('link'),
                    'posted_at': pd.to_datetime(e.get('published'), errors='coerce')
                }]))
        except:
            continue

    full = pd.concat(df_list, ignore_index=True).drop_duplicates(subset=['title'])
    full['posted_at'] = pd.to_datetime(full['posted_at'], errors='coerce')
    return full.dropna(subset=['posted_at'])

df = fetch_data()

if not df.empty:
    cutoff = datetime.now() - timedelta(days=days)
    df['posted_at'] = df['posted_at'].dt.tz_localize(None)
    df = df[df['posted_at'] >= cutoff].copy()
    
    df['combined'] = (df.get('title','') + " " + df.get('summary','')).fillna('')
    # Crypto filter
    df = df[df['combined'].str.contains('crypto|bitcoin|eth|mantle|rwa|defi|ai|stable|zk|depin', case=False, na=False)]

    # Semantic classify
    df['narrative'] = df['combined'].apply(classify_narrative_semantic)

# Analysis
if not df.empty and st.button("🔄 Phân tích Narratives (Semantic)"):
    with st.spinner("Đang train & phân loại..."):
        summary = df['narrative'].value_counts().reset_index()
        summary.columns = ['narrative', 'count']
        summary['percentage'] = (summary['count'] / len(df) * 100).round(1)
        
        st.subheader("🔥 Top Crypto Narratives")
        fig = px.pie(summary, names='narrative', values='count')
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(summary.sort_values('count', ascending=False), use_container_width=True)

# Top content
st.subheader("📌 Top Content by Narrative")
if not df.empty:
    for narr in sorted(df['narrative'].unique()):
        subset = df[df['narrative'] == narr].head(5)
        with st.expander(f"**{narr}** ({len(subset)} items)"):
            for _, row in subset.iterrows():
                st.write(row.get('title') or row['combined'][:200])
                if row.get('url'):
                    st.markdown(f"[Link]({row['url']})")
else:
    st.warning("Giảm Focus Level xuống 1-2 và thử lại.")

st.caption("Built for Minh Anh - Mantle Squad | Semantic Narrative Engine 🔥")
