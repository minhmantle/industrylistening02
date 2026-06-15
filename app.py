import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import nest_asyncio
from Scweet import Scweet
from sentence_transformers import SentenceTransformer
import numpy as np

nest_asyncio.apply()

st.set_page_config(page_title="Crypto X Narrative Dashboard", layout="wide")
st.title("🚀 Crypto Narrative Dashboard (X/Twitter Only)")
st.markdown("**Fetch trực tiếp từ X • Real-time**")

# Sidebar
st.sidebar.header("Filters")
days = st.sidebar.slider("Time Range (ngày)", 1, 14, 7)
focus_level = st.sidebar.slider("Focus Level", 1, 10, 3)

# Scweet client
@st.cache_resource
def get_scweet():
    return Scweet(auth_token="92942b0919675b65189a4182d3173ddb7a288b6e")   # <--- THAY Ở ĐÂY

scweet = get_scweet()

# Fetch data từ X
@st.cache_data(ttl=120)
def fetch_from_x(days_back=7, limit=150):
    try:
        since = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        query = "(crypto OR bitcoin OR eth OR mantle OR rwa OR defi OR depin OR ai OR stablecoin OR zk OR perp) lang:en"
        
        tweets = scweet.search(
            search_query=query,
            since=since,
            until=datetime.now().strftime("%Y-%m-%d"),
            limit=limit,
            display_type="Latest"
        )
        
        data = []
        for t in tweets:
            data.append({
                'text': t.get('text', ''),
                'username': t.get('username', ''),
                'posted_at': pd.to_datetime(t.get('timestamp')),
                'likes': t.get('likes', 0),
                'retweets': t.get('retweets', 0),
                'url': t.get('url', '')
            })
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Lỗi Scweet: {str(e)[:150]}\n\nKiểm tra auth_token")
        return pd.DataFrame()

df = fetch_from_x(days)

# Filter & Narrative
if not df.empty:
    cutoff = datetime.now() - timedelta(days=days)
    df = df[pd.to_datetime(df['posted_at']) >= cutoff].copy()
    
    df['combined'] = df['text'].fillna('')
    df = df[df['combined'].str.contains('crypto|bitcoin|eth|mantle|rwa|defi|ai|stable|zk|depin|perp', case=False)]

if not df.empty and st.button("🔄 Phân tích Narratives từ X"):
    with st.spinner("Đang phân tích narratives..."):
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        seeds = {
            "RWA": "rwa tokenized real world asset",
            "AI Agents": "ai agent defai autonomous",
            "DePIN": "depin decentralized physical",
            "L2 & Infra": "mantle layer2 scaling",
            "Stablecoins": "stablecoin usdc usdt",
            "Prediction Markets": "polymarket prediction",
            "Privacy ZK": "zk zero knowledge",
            "Perps": "perp perpetual",
            "Meme": "meme pump.fun"
        }
        
        narrative_emb = {k: embedder.encode(v) for k, v in seeds.items()}
        
        def classify(text):
            emb = embedder.encode(text)
            best = max(narrative_emb.keys(), key=lambda k: np.dot(emb, narrative_emb[k]))
            return best
        
        df['narrative'] = df['combined'].apply(classify)
        
        summary = df['narrative'].value_counts().reset_index()
        summary.columns = ['narrative', 'count']
        summary['percentage'] = (summary['count'] / len(df) * 100).round(1)
        
        st.subheader("🔥 Top Narratives từ X")
        fig = px.pie(summary, names='narrative', values='count')
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(summary)

st.subheader("🐦 Recent Tweets")
if not df.empty:
    for _, row in df.sort_values('posted_at', ascending=False).head(12).iterrows():
        with st.expander(f"@{row['username']}"):
            st.write(row['text'])
            st.markdown(f"[Xem tweet]({row['url']})")
else:
    st.info("Chưa có data hoặc Focus Level cao quá. Thử giảm xuống 2.")

st.caption("Built for Minh Anh - Mantle Squad 🔥")
