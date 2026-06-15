import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import feedparser
from datetime import datetime, timedelta

st.set_page_config(page_title="Crypto Narrative Dashboard", layout="wide")
st.title("🚀 Crypto Narrative & Alpha Dashboard")
st.markdown("**Simple & Stable Version**")

st.sidebar.header("Filters")
days = st.sidebar.slider("Time Range (ngày)", 1, 30, 7)

@st.cache_data(ttl=180)
def fetch_data():
    articles = []
    # RSS sources
    feeds = [
        "https://cointelegraph.com/rss",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://decrypt.co/feed",
        "https://www.theblock.co/rss.xml"
    ]
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:50]:
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
    df['combined'] = (df['title'].fillna('') + " " + df['summary'].fillna(''))

st.subheader("📊 Data Summary")
st.write(f"**Total articles:** {len(df)}")

if not df.empty:
    st.subheader("📌 Recent Crypto Content")
    for _, row in df.head(15).iterrows():
        with st.expander(row['title'][:100]):
            st.write(row['summary'][:400])
            if row['url']:
                st.markdown(f"[Read]({row['url']})")
else:
    st.error("Không load được data. Thử refresh.")

st.caption("Built for Minh Anh - Mantle Squad 🔥")
