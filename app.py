import streamlit as st
import pandas as pd
from scraper import scrape_all_categories

# IMPERATIVE API KEY as requested
APIFY_KEY = "apify_api_VCb1D6HbNGS4IfU1OC4e5asnqgHe3U1CLkg8"

st.set_page_config(page_title="Amazon Fırsat Avcısı", layout="wide")
st.title("Amazon Fırsat Avcısı")

with st.sidebar:
    st.header("Ayarlar")
    category = st.selectbox("Kategori Seç", ["Electronics", "Home & Kitchen", "Automotive", "All"])
    max_items = st.number_input("Max Ürün (her kategori)", min_value=1, max_value=200, value=20)
    test_mode = st.checkbox("Test Mode (sadece 1 ürün) - hızlı doğrulama")

# Persistent logs container
logs = st.container()

st.markdown("---")
st.write("Hazır olduğunda taramayı başlatmak için butona basın.")

if st.button("TARAMAYI BAŞLAT"):
    with logs:
        st.info("Apify'a bağlanılıyor... Lütfen bekleyin (bazı koşullarda daha uzun sürebilir)")
        # Prepare categories list
        cats = [category] if category != "All" else ["Electronics", "Home & Kitchen", "Automotive"]
        # Call scraper
        result = scrape_all_categories(APIFY_KEY, cats, max_items=max_items, test_mode=test_mode)

        # If scraper returned structured error
        if isinstance(result, dict) and result.get("error"):
            # Big red error box with exact message and run URL
            st.error("HATA: Apify çağrısı başarısız oldu.")
            st.markdown("**Detay:**")
            st.code(result.get("message") or "Bilinmeyen hata")
            run_url = result.get("run_url")
            if run_url:
                st.markdown(f"**Apify Run URL:** [{run_url}]({run_url})")
        # If results returned
        elif isinstance(result, list):
            st.success(f"✅ Toplam {len(result)} ürün bulundu (birleştirilmiş).")
            try:
                df = pd.DataFrame(result)
                st.dataframe(df)
                csv = df.to_csv(index=False)
                st.download_button("CSV indir", data=csv, file_name="results.csv")
            except Exception:
                st.write(result)
        else:
            st.warning("Bot çalıştı ama sonuç listesi beklenmedik formatta döndü.")