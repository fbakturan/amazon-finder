import time
import requests
from typing import Any, Dict, List, Optional, Tuple, Union

# Actor identifier per request
ACTOR = "apify/amazon-scraper"

# Brand blacklist (case-insensitive)
BRAND_BLACKLIST = [
    "samsung",
    "apple",
    "nike",
    "sony",
    "lg",
    "microsoft",
    "bose",
    "adidas",
    "google",
    "hp",
    "dell",
    "lenovo",
    "panasonic",
    "canon",
]


def _clean_price(raw: Optional[str]) -> Optional[float]:
    if not raw:
        return None
    try:
        s = str(raw).replace("$", "").replace(",", "").strip()
        if s == "":
            return None
        return float(s)
    except Exception:
        return None


def _is_brand_blacklisted(title: str, brand: Optional[str]) -> bool:
    hay = (title or "").lower()
    if brand:
        hay += " " + brand.lower()
    for b in BRAND_BLACKLIST:
        if b in hay:
            return True
    return False


def run_apify_actor(api_token: str, input_data: Dict[str, Any], timeout_seconds: int = 120) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Runs the configured Apify actor with given `input_data` and returns dataset items or error dict.
    """
    params = {"token": api_token}
    run_web_url = None
    try:
        url = f"https://api.apify.com/v2/acts/{ACTOR}/runs"
        resp = requests.post(url, params=params, json={"input": input_data}, timeout=60)
        resp.raise_for_status()
        run = resp.json()

        run_id = run.get("data", {}).get("id") or run.get("id")
        run_web_url = run.get("data", {}).get("webUrl") or run.get("data", {}).get("web_url")
        if not run_web_url and run_id:
            run_web_url = f"https://console.apify.com/actors/{ACTOR}/runs/{run_id}"

        # Poll for completion
        poll_url = f"https://api.apify.com/v2/acts/{ACTOR}/runs/{run_id}"
        status = run.get("data", {}).get("status") or run.get("status")
        waited = 0
        while status not in ("SUCCEEDED", "FAILED", "ABORTED", "STOPPED", "TIMED-OUT") and waited < timeout_seconds:
            time.sleep(2)
            waited += 2
            rr = requests.get(poll_url, params=params, timeout=30)
            rr.raise_for_status()
            run = rr.json()
            status = run.get("data", {}).get("status") or run.get("status")

        if status != "SUCCEEDED":
            msg = run.get("data", {}).get("statusMessage") or run.get("data", {}).get("errorMessage") or f"Run finished with status: {status}"
            return {"error": True, "message": str(msg), "run_url": run_web_url}

        data = run.get("data", {})
        dataset_id = data.get("defaultDatasetId") or data.get("defaultDataset")
        if dataset_id:
            ds_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
            ds_params = {"token": api_token, "format": "json"}
            r = requests.get(ds_url, params=ds_params, timeout=30)
            r.raise_for_status()
            return r.json()

        kv_id = data.get("defaultKeyValueStoreId")
        if kv_id:
            kv_url = f"https://api.apify.com/v2/key-value-stores/{kv_id}/records/output"
            rr = requests.get(kv_url, params={"token": api_token}, timeout=30)
            rr.raise_for_status()
            try:
                return rr.json()
            except ValueError:
                return rr.text

        return {"error": True, "message": "No dataset or key-value store found in run output", "run_url": run_web_url}

    except Exception as e:
        return {"error": True, "message": str(e), "run_url": run_web_url}


def scrape_movers_and_shakers(api_token: str,
                              movers_urls: List[str],
                              max_items: int = 50,
                              test_mode: bool = False) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Scrape provided Movers & Shakers URLs using the official actor, filter brands, clean prices.

    Returns either an error dict {error: True, message: ..., run_url: ...} or
    a dict: {"items": [...], "metrics": {...}}
    """
    # Build actor input according to requested aggressive settings
    input_data: Dict[str, Any] = {}
    input_data["categoryOrProductUrls"] = movers_urls
    input_data["maxItems"] = 1 if test_mode else max_items
    input_data["proxyConfiguration"] = {"useApifyProxy": True}
    input_data["captchaSolver"] = True
    input_data["scrapeProductDetails"] = False

    # Run Apify actor
    res = run_apify_actor(api_token, input_data)
    if isinstance(res, dict) and res.get("error"):
        return res

    # Expecting list of items
    raw_items: List[Dict[str, Any]] = res if isinstance(res, list) else []

    cleaned: List[Dict[str, Any]] = []
    filtered_out = 0
    for it in raw_items:
        title = it.get("title") or it.get("name") or ""
        brand = it.get("brand") or it.get("manufacturer") or ""
        asin = it.get("asin") or it.get("asin13") or it.get("asinCode")
        price_raw = it.get("price") or it.get("buyboxPrice") or it.get("currentPrice")

        if _is_brand_blacklisted(title, brand):
            filtered_out += 1
            continue

        price = _clean_price(price_raw)

        amazon_url = None
        if asin:
            amazon_url = f"https://www.amazon.com/dp/{asin}"
        else:
            amazon_url = it.get("url") or it.get("productUrl")

        cleaned_item = {
            "title": title,
            "brand": brand,
            "asin": asin,
            "price": price,
            "amazon_url": amazon_url,
            "raw": it,
        }
        cleaned.append(cleaned_item)

    metrics = {
        "total_scraped": len(raw_items),
        "filtered_by_brand": filtered_out,
        "potential_opportunities": len(cleaned),
    }

    return {"items": cleaned, "metrics": metrics}


# Placeholder for future Trendyol price check (to be implemented later)
def check_trendyol_price(product_title: str) -> Optional[float]:
    """Stub: return None for now. Implementation will query Trendyol later."""
    return None


# Placeholder for future visual similarity using Gemini
def check_visual_similarity(amazon_img: str, trendyol_img: str, gemini_api_key: Optional[str] = None) -> Optional[float]:
    """Stub: return None. Implementation will use Gemini later."""
    return None


if __name__ == "__main__":
    print("Module ready: provides scrape_movers_and_shakers(), check_trendyol_price(), check_visual_similarity().")
