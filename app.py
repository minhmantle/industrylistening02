import streamlit as st
import pandas as pd
import feedparser
from datetime import datetime, timedelta

st.set_page_config(page_title="Crypto Narrative Dashboard", layout="wide")
st.title("🚀 Crypto Narrative Dashboard")
st.markdown("**Stable RSS Version - Fixed Datetime**")

days = st.sidebar.slider("Thời gian (ngày)", 1, 30, 7)

@st.cache_data(ttl=60)
def load_data():
    feeds = [
        "https://cointelegraph.com/rss",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://decrypt.co/feed",
        "https://www.theblock.co/rss.xml"
    ]
    data = []
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:50]:
                data.append({
                    'title': entry.get('title', 'No title'),
                    'summary': entry.get('summary') or entry.get('description', ''),
                    'url': entry.get('link', ''),
                    'posted_at_raw': entry.get('published') or entry.get('pubDate') or entry.get('updated')
                })
        except:
            continue
    df = pd.DataFrame(data)
    return df

df = load_data()

if not df.empty:
    # FIX DATETIME CỨNG
    df['posted_at'] = pd.to_datetime(df['posted_at_raw'], errors='coerce', utc=True)
    df = df.dropna(subset=['posted_at'])
    df['posted_at'] = df['posted_at'].dt.tz_convert(None)  # remove timezone

    cutoff = datetime.now() - timedelta(days=days)
    df = df[df['posted_at'] >= cutoff].copy()

st.write(f"**Tổng số bài:** {len(df)}")

if not df.empty:
    st.subheader("📌 Recent Content")
    for _, row in df.sort_values('posted_at', ascending=False).head(20).iterrows():
        with st.expander(row['title'][:120]):
            st.write(row['summary'][:600])
            st.caption(str(row['posted_at']))
            if row['url']:
                st.markdown(f"[Đọc đầy đủ]({row['url']})")
else:
    st.warning("Chưa có data. Thử refresh trang.")

st.caption("Built for Minh Anh - Mantle Squad 🔥")
