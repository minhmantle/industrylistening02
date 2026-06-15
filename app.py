import streamlit as st
import pandas as pd
import feedparser
from datetime import datetime, timedelta

st.set_page_config(page_title="Crypto Narrative Dashboard", layout="wide")
st.title("🚀 Crypto Narrative & Alpha Dashboard")
st.markdown("**Top Content từ X + Crypto Media • Public**")

days = st.sidebar.slider("Thời gian (ngày)", 1, 14, 7)

@st.cache_data(ttl=60)
def load_crypto_content():
    data = []
    # RSS sources crypto-focused
    feeds = [
        "https://cointelegraph.com/rss",
        "https://decrypt.co/feed",
        "https://www.theblock.co/rss.xml",
        "https://bitcoinmagazine.com/feed",
        "https://www.coindesk.com/arc/outboundfeeds/rss/"
    ]
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:30]:
                data.append({
                    'title': entry.get('title', ''),
                    'summary': entry.get('summary') or entry.get('description', ''),
                    'url': entry.get('link', ''),
                    'posted_at': entry.get('published') or entry.get('pubDate'),
                    'source': feed.feed.get('title', 'Crypto Media')
                })
        except:
            continue
    return pd.DataFrame(data)

df = load_crypto_content()

if not df.empty:
    df['posted_at'] = pd.to_datetime(df['posted_at'], errors='coerce')
    df = df.dropna(subset=['posted_at'])
    cutoff = datetime.now() - timedelta(days=days)
    df = df[df['posted_at'] >= cutoff].copy()

st.write(f"**Số bài crypto gần đây:** {len(df)}")

# Simple Narrative filter (keyword)
if not df.empty:
    st.subheader("🔥 Top Crypto Narratives & Content")
    search = st.text_input("Tìm narrative (ví dụ: rwa, ai agent, mantle, depin, perp)", "")
    
    display_df = df
    if search:
        display_df = df[df['title'].str.contains(search, case=False, na=False) | 
                       df['summary'].str.contains(search, case=False, na=False)]
    
    for _, row in display_df.sort_values('posted_at', ascending=False).head(20).iterrows():
        with st.expander(f"**{row['title'][:100]}...**"):
            st.write(row['summary'][:500])
            st.caption(f"{row['source']} • {row['posted_at'].date()}")
            st.markdown(f"[Xem chi tiết]({row['url']})")

else:
    st.error("Đang load data... Refresh nếu không thấy.")

st.caption("Built for Minh Anh - Mantle Squad | Public Dashboard 🔥")
