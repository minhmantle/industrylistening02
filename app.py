import streamlit as st
import pandas as pd
import plotly.express as px
import feedparser
from datetime import datetime, timedelta

st.set_page_config(page_title="Crypto Narrative", layout="wide")
st.title("🚀 Crypto Narrative Dashboard")
st.markdown("**Simple & Stable - RSS only**")

days = st.sidebar.slider("Thời gian (ngày)", 1, 30, 7)

@st.cache_data(ttl=60)
def load_data():
    feeds = [
        "https://cointelegraph.com/rss",
        "https://decrypt.co/feed",
        "https://www.theblock.co/rss.xml",
        "https://bitcoinmagazine.com/feed"
    ]
    data = []
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:40]:
                data.append({
                    'title': entry.title,
                    'summary': entry.get('summary') or entry.get('description', ''),
                    'url': entry.link,
                    'posted_at': entry.get('published')
                })
        except:
            continue
    df = pd.DataFrame(data)
    df['posted_at'] = pd.to_datetime(df['posted_at'], errors='coerce')
    return df.dropna(subset=['posted_at'])

df = load_data()

if not df.empty:
    cutoff = datetime.now() - timedelta(days=days)
    df = df[df['posted_at'] >= cutoff].copy()

st.write(f"**Số bài tải được:** {len(df)}")

if not df.empty:
    st.subheader("📌 Recent Crypto News")
    for _, row in df.sort_values('posted_at', ascending=False).head(20).iterrows():
        with st.expander(row['title'][:120]):
            st.write(row['summary'][:600])
            st.markdown(f"[Đọc đầy đủ]({row['url']})")
else:
    st.error("Không load được data. Refresh trang thử.")

st.caption("Built for Minh Anh 🔥")
