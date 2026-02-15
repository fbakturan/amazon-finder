import streamlit as st
import pandas as pd
from scraper import scrape_all_categories, filter_brands
import time

# API KEYS
APIFY_API_TOKEN = "apify_api_VCb1D6HbNGS4IfU1OC4e5asnqgHe3U1CLkg8"

st.set_page_config(page_title="Amazon Fırsat Bulucu", page_icon="🎯", layout="wide")
st.title("🎯 Amazon Movers & Shakers Fırsat Bulucu")
st.markdown("**9 kategoriden** büyük markaları filtreleyerek **fırsat ürünleri** bulur.")

st.sidebar.header("⚙️ Ayarlar")
all_categories = ["Electronics", "Home & Kitchen", "Tools & Home Improvement", "Automotive", "Cell Phones & Accessories", "Computers & Accessories", "Kitchen & Dining", "Pet Supplies", "Sports & Outdoors"]

selected_categories = [cat for cat in all_categories if st.sidebar.checkbox(cat, value=True)]
max_items = st.sidebar.slider("Kategori başına max ürün:", 5, 50, 10)

col1, col2, col3 = st.columns(3)
m1, m2, m3 = col1.empty(), col2.empty(), col3.empty()
m1.metric("📦 Taranan", "-")
m2.metric("🚫 Elenen", "-")
m3.metric("🎯 Fırsat", "-")

if st.button("🚀 BAŞLAT", type="primary", use_container_width=True):
    if not selected_categories:
        st.error("En az bir kategori seçin!")
        st.stop()
    
    # Progress bar
    progress = st.progress(0)
    
    # Hata ve Durum mesajları için container (artık silinmeyecek)
    log_container = st.container()
    
    all_results, total_scraped, total_filtered = [], 0, 0
    
    for idx, cat in enumerate(selected_categories):
        with log_container:
            st.info(f"🔍 {cat} taranıyor (Apify)...")
            
        try:
            # Scraper çağrısı
            result = scrape_all_categories(APIFY_API_TOKEN, [cat], max_items)
            
            # HATA KONTROLÜ
            if isinstance(result, dict) and result.get("error"):
                with log_container:
                    st.error(f"❌ {cat} için ürün bulunamadı!")
                    if result.get("run_url"):
                        st.link_button(f"👉 {cat} HATASINI GÖRMEK İÇİN TIKLA (Apify Log)", result["run_url"])
                        st.warning(f"Yukarıdaki linke tıkla. Eğer 'Blocked' yazıyorsa veya captcha sayfası görüyorsan Amazon engellemiştir.")
                products = []
            else:
                products = result

            if products:
                filtered = filter_brands(products, cat)
                scraped_count = len(products)
                filtered_count = len(filtered)
                
                total_scraped += scraped_count
                total_filtered += (scraped_count - filtered_count)
                all_results.extend(filtered)
                with log_container:
                    st.success(f"✅ {cat}: {scraped_count} ürün çekildi.")
            
        except Exception as e:
            with log_container:
                st.error(f"❌ {cat} kod hatası: {e}")
            
        progress.progress((idx + 1) / len(selected_categories))
    
    st.success("✅ İşlem Tamamlandı!")
    m1.metric("📦 Taranan", total_scraped)
    m2.metric("🚫 Elenen", total_filtered)
    m3.metric("🎯 Fırsat", len(all_results))
    
    if all_results:
        st.balloons()
        df = pd.DataFrame(all_results)
        st.dataframe(df[['title', 'brand', 'price', 'category', 'amazon_url']], use_container_width=True)
        st.download_button("📥 CSV İndir", df.to_csv(index=False).encode('utf-8'), "sonuc.csv", "text/csv")
    elif total_scraped == 0:
        st.error("❌ Hiçbir ürün çekilemedi. Yukarıdaki hata linklerine tıkla!")
