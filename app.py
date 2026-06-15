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

# Thay auth_token của mày vào đây
@st.cache_resource
def get_scweet():
    return Scweet(auth_token="YOUR_AUTH_TOKEN_HERE")  # <--- Thay cái này

scweet = get_scweet()

# Fetch từ X
@st.cache_data(ttl=120)
def fetch_from_x(days_back=7, limit=200):
    try:
        since = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        query = "crypto OR bitcoin OR eth OR mantle OR rwa OR defi OR depin OR ai agent OR stablecoin OR zk OR perp"
        
        tweets = scweet.search(
            search_query=query,
            since=since,
            until=datetime.now().strftime("%Y-%m-%d"),
            limit=limit,
            display_type="Latest"
        )
        
        data = []
        for t in tweets:
            text = t.get('text', '')
            data.append({
                'text': text,
                'username': t.get('username', ''),
                'posted_at': pd.to_datetime(t.get('timestamp')),
                'likes': t.get('likes', 0),
                'retweets': t.get('retweets', 0),
                'url': t.get('url', '')
            })
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Lỗi fetch X: {e}")
        return pd.DataFrame()

df = fetch_from_x(days)

# Filter + Narrative
if not df.empty:
    cutoff = datetime.now() - timedelta(days=days)
    df = df[pd.to_datetime(df['posted_at']) >= cutoff].copy()
    
    df['combined'] = df['text'].fillna('')
    df = df[df['combined'].str.contains('crypto|bitcoin|eth|mantle|rwa|defi|ai|stable|zk|depin|perp', case=False)]

# Phân loại narrative (semantic)
if not df.empty and st.button("🔄 Phân tích Narratives từ X"):
    with st.spinner("Đang quét X và phân loại..."):
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        # Narrative seeds
        seeds = {
            "RWA": "rwa real world asset tokenized",
            "AI Agents": "ai agent defai autonomous",
            "DePIN": "depin decentralized physical",
            "Infrastructure": "mantle l2 layer2 scaling",
            "Stablecoins": "stablecoin usdc usdt",
            "Prediction Markets": "polymarket prediction",
            "Privacy ZK": "zk zero knowledge",
            "Perps": "perp perpetual derivatives",
            "Meme": "meme pump.fun"
        }
        
        narrative_emb = {k: embedder.encode(v) for k, v in seeds.items()}
        
        def classify(text):
            if len(text) < 30: return "Others"
            emb = embedder.encode(text)
            best = max(narrative_emb, key=lambda k: np.dot(emb, narrative_emb[k]))
            return best
        
        df['narrative'] = df['combined'].apply(classify)
        
        summary = df['narrative'].value_counts().reset_index()
        summary.columns = ['narrative', 'count']
        summary['percentage'] = (summary['count'] / len(df) * 100).round(1)
        
        st.subheader("🔥 Top Narratives từ X")
        fig = px.pie(summary, names='narrative', values='count')
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(summary)

# Hiển thị tweets
st.subheader("🐦 Recent Posts trên X")
if not df.empty:
    for _, row in df.sort_values('posted_at', ascending=False).head(15).iterrows():
        with st.expander(f"@{row['username']} • {row['posted_at'].date()}"):
            st.write(row['text'])
            st.markdown(f"[Xem trên X]({row['url']})")
else:
    st.warning("Chưa có data. Kiểm tra auth_token và Focus Level.")

st.caption("Built for Minh Anh | Fetch trực tiếp từ X 🔥")
