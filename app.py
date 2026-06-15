import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import feedparser
from datetime import datetime, timedelta

st.set_page_config(page_title="Crypto Narrative Dashboard", layout="wide")
st.title("🚀 Crypto Narrative & Alpha Dashboard")
st.markdown("**Stable Version - Fixed Datetime**")

st.sidebar.header("Filters")
days = st.sidebar.slider("Time Range (ngày)", 1, 30, 7)

@st.cache_data(ttl=180)
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
            for entry in feed.entries[:60]:
                articles.append({
                    'title': entry.get('title', ''),
                    'summary': entry.get('summary') or entry.get('description', ''),
                    'url': entry.get('link'),
                    'posted_at': entry.get('published') or entry.get('pubDate')
                })
        except:
            continue
    return pd.DataFrame(articles)

df = fetch_data()

if not df.empty:
    # FIX DATETIME
    df['posted_at'] = pd.to_datetime(df['posted_at'], errors='coerce')
    df = df.dropna(subset=['posted_at'])
    
    cutoff = datetime.now() - timedelta(days=days)
    df = df[df['posted_at'] >= cutoff].copy()

st.subheader("📊 Data Summary")
st.write(f"**Total articles loaded:** {len(df)}")

if not df.empty:
    st.subheader("📌 Recent Content")
    for _, row in df.sort_values('posted_at', ascending=False).head(15).iterrows():
        with st.expander(row['title'][:100]):
            st.write(row['summary'][:500])
            st.caption(row['posted_at'])
            if row['url']:
                st.markdown(f"[Read full article]({row['url']})")
else:
    st.error("Không có data. Thử refresh trang.")

st.caption("Built for Minh Anh - Mantle Squad 🔥")
