import time
import requests
from typing import Any, Dict, List, Optional, Tuple, Union

# Actor identifier per request (stable public IDs)
ACTOR_PRIMARY = "vdrmota~amazon-scraper"
ACTOR_FALLBACK = "junglee~amazon-crawler"

# Embedded API token (as requested)
APIFY_TOKEN = "apify_api_VCb1D6HbNGS4IfU1OC4e5asnqgHe3U1CLkg8"

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


def _run_actor_once(api_token: str, actor_id: str, input_data: Dict[str, Any], timeout_seconds: int = 120) -> Dict[str, Any]:
    """Run a single Apify actor and return a structured result dict.

    Returns a dict with either:
      - {"ok": True, "items": [...], "actor": actor_id}
    or
      - {"ok": False, "error": True, "message": ..., "actor": actor_id, "http_status": code, "raw_response": ...}
    """
    params = {"token": api_token}
    run_web_url = None
    url = f"https://api.apify.com/v2/acts/{actor_id}/runs"
    try:
        resp = requests.post(url, params=params, json={"input": input_data}, timeout=60)
    except Exception as e:
        return {"ok": False, "error": True, "message": str(e), "actor": actor_id, "http_status": None, "raw_response": None}

    # If non-200, return full response details so UI can show why
    if resp.status_code >= 400:
        raw = None
        try:
            raw = resp.json()
        except Exception:
            raw = resp.text
        return {"ok": False, "error": True, "message": f"HTTP {resp.status_code}", "actor": actor_id, "http_status": resp.status_code, "raw_response": raw}

    try:
        run = resp.json()
    except Exception as e:
        return {"ok": False, "error": True, "message": f"Invalid JSON response: {e}", "actor": actor_id, "http_status": resp.status_code, "raw_response": resp.text}

    run_id = run.get("data", {}).get("id") or run.get("id")
    run_web_url = run.get("data", {}).get("webUrl") or run.get("data", {}).get("web_url")
    if not run_web_url and run_id:
        run_web_url = f"https://console.apify.com/actors/{actor_id}/runs/{run_id}"

    # Poll for completion
    poll_url = f"https://api.apify.com/v2/acts/{actor_id}/runs/{run_id}"
    status = run.get("data", {}).get("status") or run.get("status")
    waited = 0
    while status not in ("SUCCEEDED", "FAILED", "ABORTED", "STOPPED", "TIMED-OUT") and waited < timeout_seconds:
        time.sleep(2)
        waited += 2
        rr = requests.get(poll_url, params=params, timeout=30)
        if rr.status_code >= 400:
            raw = None
            try:
                raw = rr.json()
            except Exception:
                raw = rr.text
            return {"ok": False, "error": True, "message": f"HTTP {rr.status_code} while polling", "actor": actor_id, "http_status": rr.status_code, "raw_response": raw}
        rr.raise_for_status()
        run = rr.json()
        status = run.get("data", {}).get("status") or run.get("status")

    if status != "SUCCEEDED":
        msg = run.get("data", {}).get("statusMessage") or run.get("data", {}).get("errorMessage") or f"Run finished with status: {status}"
        return {"ok": False, "error": True, "message": str(msg), "actor": actor_id, "run_url": run_web_url, "http_status": None, "raw_response": run}

    data = run.get("data", {})
    dataset_id = data.get("defaultDatasetId") or data.get("defaultDataset")
    if dataset_id:
        ds_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
        ds_params = {"token": api_token, "format": "json"}
        r = requests.get(ds_url, params=ds_params, timeout=30)
        if r.status_code >= 400:
            raw = None
            try:
                raw = r.json()
            except Exception:
                raw = r.text
            return {"ok": False, "error": True, "message": f"HTTP {r.status_code} when fetching dataset", "actor": actor_id, "http_status": r.status_code, "raw_response": raw, "run_url": run_web_url}
        r.raise_for_status()
        try:
            items = r.json()
        except Exception:
            items = []
        return {"ok": True, "items": items, "actor": actor_id, "run_url": run_web_url}

    kv_id = data.get("defaultKeyValueStoreId")
    if kv_id:
        kv_url = f"https://api.apify.com/v2/key-value-stores/{kv_id}/records/output"
        rr = requests.get(kv_url, params={"token": api_token}, timeout=30)
        if rr.status_code >= 400:
            raw = None
            try:
                raw = rr.json()
            except Exception:
                raw = rr.text
            return {"ok": False, "error": True, "message": f"HTTP {rr.status_code} when fetching key-value store", "actor": actor_id, "http_status": rr.status_code, "raw_response": raw, "run_url": run_web_url}
        rr.raise_for_status()
        try:
            items = rr.json()
        except Exception:
            items = rr.text
        return {"ok": True, "items": items, "actor": actor_id, "run_url": run_web_url}

    return {"ok": False, "error": True, "message": "No dataset or key-value store found in run output", "actor": actor_id, "run_url": run_web_url}


def scrape_movers_and_shakers(api_token: Optional[str] = None,
                              movers_urls: List[str] = None,
                              max_items: int = 50,
                              test_mode: bool = False) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Scrape provided Movers & Shakers URLs using the official actor, filter brands, clean prices.

    Returns either an error dict {error: True, message: ..., run_url: ...} or
    a dict: {"items": [...], "metrics": {...}}
    """
    # Use embedded token regardless of passed value (requested)
    api_token = APIFY_TOKEN

    # Ensure movers_urls is a list
    if not movers_urls:
        movers_urls = []

    # Try primary actor first, then fallback
    attempts = []
    actors = [ACTOR_PRIMARY, ACTOR_FALLBACK]
    final_run_result = None
    for actor in actors:
        # Build actor-specific input schema
        if actor == ACTOR_PRIMARY:
            input_data = {
                "startUrls": [{"url": u} for u in movers_urls],
                "maxItems": 1 if test_mode else max_items,
                "proxyConfiguration": {"useApifyProxy": True},
                "captchaSolver": True,
                "scrapeProductDetails": False,
            }
        else:
            input_data = {
                "categoryOrProductUrls": movers_urls,
                "maxItems": 1 if test_mode else max_items,
                "proxyConfiguration": {"useApifyProxy": True},
                "captchaSolver": True,
                "scrapeProductDetails": False,
            }

        run_result = _run_actor_once(api_token, actor, input_data)
        attempts.append(run_result)
        if run_result.get("ok"):
            final_run_result = run_result
            break
        # If 404 / actor-not-found, try next; otherwise stop with error
        http_status = run_result.get("http_status")
        if http_status == 404:
            # try next actor
            continue
        # If other error, exit early and return structured error with attempts
        return {"error": True, "message": run_result.get("message"), "run_url": run_result.get("run_url"), "attempts": attempts}

    if not final_run_result:
        # all attempts failed
        return {"error": True, "message": "All actor attempts failed", "attempts": attempts}

    raw_items: List[Dict[str, Any]] = final_run_result.get("items") or []

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
