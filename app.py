import streamlit as st
import pandas as pd
import json
from typing import List
from scraper import scrape_movers_and_shakers

# Config
APIFY_KEY = "apify_api_VCb1D6HbNGS4IfU1OC4e5asnqgHe3U1CLkg8"
GEMINI_KEY = "AIzaSyBKZB4HEGIRbhSqXK6aRwRZwu3uddCOLL4"

st.set_page_config(page_title="Amazon Movers & Shakers -> Trendyol Finder", layout="wide")
st.title("Amazon Movers & Shakers → Trendyol Opportunity Finder")

with st.sidebar:
    st.header("Ayarlar")
    movers_input = st.text_area("Movers & Shakers URL'leri (her satıra 1 URL)", value="https://www.amazon.com/gp/movers-and-shakers")
    max_items = st.number_input("Max Ürün (toplam)", min_value=1, max_value=500, value=50)
    test_mode = st.checkbox("Test Connection (sadece 1 ürün)")

# Logs container persists messages
logs = st.container()

st.markdown("---")

cols = st.columns([3,1])
cols[0].write("Hazır olduğunda 'Scrape' ile başlatın. Test Connection bağlantıyı hızlıca kontrol eder.")

if cols[1].button("Test Connection"):
    with logs:
        st.info("Test modunda Apify çağrısı yapılıyor (1 ürün)...")
        movers = [u.strip() for u in movers_input.splitlines() if u.strip()]
        res = scrape_movers_and_shakers(APIFY_KEY, movers, max_items=max_items, test_mode=True)
        if isinstance(res, dict) and res.get("error"):
            st.error("🚨 Apify Hatası")
            st.code(res.get("message", "Bilinmeyen hata"))
            if res.get("run_url"):
                run_url = res.get("run_url")
                st.markdown(f"**Apify Run URL:** [{run_url}]({run_url})")
            if res.get("attempts"):
                st.markdown("**Actor Attempts (raw):**")
                st.code(json.dumps(res.get("attempts"), indent=2, ensure_ascii=False))
        else:
            items = res.get("items") if isinstance(res, dict) else res
            st.success(f"Bağlantı başarılı — {len(items)} ürün örneği alındı.")

if st.button("Scrape"):
    with logs:
        st.info("Apify'a bağlanılıyor... Bu işlem zaman alabilir.")
        movers = [u.strip() for u in movers_input.splitlines() if u.strip()]
        res = scrape_movers_and_shakers(APIFY_KEY, movers, max_items=max_items, test_mode=test_mode)

        # Error handling
        if isinstance(res, dict) and res.get("error"):
            st.error("🚨 Apify çağrısı başarısız oldu.")
                st.code(res.get("message", "Bilinmeyen hata"))
                if res.get("run_url"):
                    run_url = res.get("run_url")
                    st.markdown(f"**Apify Run URL:** [{run_url}]({run_url})")
                if res.get("attempts"):
                    st.markdown("**Actor Attempts (raw):**")
                    st.code(json.dumps(res.get("attempts"), indent=2, ensure_ascii=False))
        else:
            data = res if isinstance(res, dict) else {"items": res, "metrics": {}}
            items: List[dict] = data.get("items", [])
            metrics = data.get("metrics", {})

            st.metric("Toplam Taranan", metrics.get("total_scraped", len(items)))
            st.metric("Filtrelenen (Marka)", metrics.get("filtered_by_brand", 0))
            st.metric("Potansiyel Fırsatlar", metrics.get("potential_opportunities", len(items)))

            if items:
                try:
                    df = pd.DataFrame(items)
                    st.dataframe(df)
                    csv = df.to_csv(index=False)
                    st.download_button("CSV indir", data=csv, file_name="movers_shakers.csv")
                except Exception:
                    st.write(items)
            else:
                st.warning("Hiç uygun ürün bulunamadı.")