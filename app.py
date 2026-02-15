import streamlit as st
import pandas as pd
from scraper import scrape_all_categories, filter_brands
import time

APIFY_API_TOKEN = "apify_api_VCb1D6HbNGS4IfU1OC4e5asnqgHe3U1CLkg8"

st.set_page_config(page_title="Amazon Fırsat Bulucu", page_icon="🎯", layout="wide")
st.title("🎯 Amazon Movers & Shakers Fırsat Bulucu")

st.sidebar.header("⚙️ Ayarlar")
all_categories = ["Electronics", "Home & Kitchen", "Tools & Home Improvement", "Automotive", "Cell Phones & Accessories", "Computers & Accessories", "Kitchen & Dining", "Pet Supplies", "Sports & Outdoors"]

selected_categories = [cat for cat in all_categories if st.sidebar.checkbox(cat, value=True)]
max_items = st.sidebar.slider("Kategori başına max ürün:", 10, 100, 50)

col1, col2, col3 = st.columns(3)
m1, m2, m3 = col1.empty(), col2.empty(), col3.empty()
m1.metric("📦 Taranan", "-")
m2.metric("🚫 Elenen", "-")
m3.metric("🎯 Fırsat", "-")

if st.button("🚀 BAŞLAT", type="primary", use_container_width=True):
    if not selected_categories:
        st.error("En az bir kategori seçin!")
        st.stop()
    
    progress = st.progress(0)
    status = st.empty()
    all_results, total_scraped, total_filtered = [], 0, 0
    
    for idx, cat in enumerate(selected_categories):
        status.info(f"🔍 {cat} taranıyor...")
        try:
            products = scrape_all_categories(APIFY_API_TOKEN, [cat], max_items)
            if products:
                filtered = filter_brands(products, cat)
                total_scraped += len(products)
                total_filtered += len(products) - len(filtered)
                all_results.extend(filtered)
        except Exception as e:
            status.error(f"❌ {cat}: {e}")
        progress.progress((idx + 1) / len(selected_categories))
    
    status.success("✅ Tamamlandı!")
    m1.metric("📦 Taranan", total_scraped)
    m2.metric("🚫 Elenen", total_filtered)
    m3.metric("🎯 Fırsat", len(all_results))
    
    if all_results:
        st.balloons()
        df = pd.DataFrame(all_results)
        st.dataframe(df[['title', 'brand', 'price', 'category', 'amazon_url']], use_container_width=True)
        st.download_button("📥 CSV İndir", df.to_csv(index=False).encode('utf-8'), "sonuc.csv", "text/csv")
