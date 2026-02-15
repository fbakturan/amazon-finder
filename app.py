import streamlit as st
import pandas as pd
from scraper import scrape_all_categories, filter_brands

# API KEY
APIFY_KEY = "apify_api_VCb1D6HbNGS4IfU1OC4e5asnqgHe3U1CLkg8"

st.title("Amazon Fırsat Avcısı (DEBUG MODU)")

cat = st.selectbox("Kategori Seç", ["Electronics", "Home & Kitchen", "Automotive"])

if st.button("TARAMAYI BAŞLAT"):
    st.info("Apify'a bağlanılıyor... Lütfen bekleyin (15-20 saniye sürebilir)")
    
    # Scraper'ı çağır
    sonuc = scrape_all_categories(APIFY_KEY, [cat], 5)
    
    # HATA VAR MI BAK
    if isinstance(sonuc, dict) and sonuc.get("error"):
        st.error("🚨 HATA OLUŞTU!")
        st.code(sonuc["message"])
        if sonuc.get("run_url") and sonuc["run_url"] != "Link Yok":
            st.link_button("👉 Apify Loglarını İncele", sonuc["run_url"])
    
    # ÜRÜN VARSA GÖSTER
    elif sonuc:
        st.success(f"✅ {len(sonuc)} ürün bulundu!")
        st.dataframe(sonuc)
    else:
        st.warning("Bot çalıştı ama boş liste döndü.")