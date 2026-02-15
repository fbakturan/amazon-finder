import time
import requests
from typing import Any, Dict, List, Optional, Union

# apify/amazon-scraper actor (owner~actor)
ACTOR = "apify/amazon-scraper"


def run_scraper(api_token: str,
                search_query: Optional[str] = None,
                asin: Optional[str] = None,
                max_items: int = 10,
                test_mode: bool = False) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Runs the official apify/amazon-scraper actor and returns items or an error dict.

    On success: returns a list of result objects.
    On failure: returns {"error": True, "message": str(e), "run_url": ...}
    """
    params = {"token": api_token}
    run_web_url = None
    try:
        input_data: Dict[str, Any] = {}
        # Aggressive settings: use Apify proxy with residential if available and solve captchas
        input_data["proxyConfiguration"] = {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]}
        input_data["solveCaptchas"] = True
        # Limit number of items for quick test
        input_data["maxItems"] = 1 if test_mode else max_items

        if search_query:
            # many versions of the actor accept `queries` or `searchKeywords` — include common keys
            input_data.setdefault("queries", [search_query])
            input_data.setdefault("searchKeywords", [search_query])
        if asin:
            input_data.setdefault("asins", [asin])

        # Start actor run
        url = f"https://api.apify.com/v2/acts/{ACTOR}/runs"
        resp = requests.post(url, params=params, json={"input": input_data}, timeout=60)
        resp.raise_for_status()
        run = resp.json()

        run_id = run.get("data", {}).get("id") or run.get("id")
        run_web_url = run.get("data", {}).get("webUrl") or run.get("data", {}).get("web_url")
        if not run_web_url and run_id:
            run_web_url = f"https://console.apify.com/actors/apify/amazon-scraper/runs/{run_id}"

        # Poll for completion
        poll_url = f"https://api.apify.com/v2/acts/{ACTOR}/runs/{run_id}"
        status = run.get("data", {}).get("status") or run.get("status")
        timeout_seconds = 120
        waited = 0
        while status not in ("SUCCEEDED", "FAILED", "ABORTED", "STOPPED", "TIMED-OUT") and waited < timeout_seconds:
            time.sleep(2)
            waited += 2
            rr = requests.get(poll_url, params=params, timeout=30)
            rr.raise_for_status()
            run = rr.json()
            status = run.get("data", {}).get("status") or run.get("status")

        if status != "SUCCEEDED":
            # Try to get helpful failure message
            msg = run.get("data", {}).get("statusMessage") or run.get("data", {}).get("errorMessage") or f"Run finished with status: {status}"
            return {"error": True, "message": str(msg), "run_url": run_web_url}

        data = run.get("data", {})
        # Try dataset first
        dataset_id = data.get("defaultDatasetId") or data.get("defaultDataset")
        if dataset_id:
            ds_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
            ds_params = {"token": api_token, "format": "json"}
            if test_mode:
                ds_params["limit"] = 1
            r = requests.get(ds_url, params=ds_params, timeout=30)
            r.raise_for_status()
            return r.json()

        # Fallback to key-value store output record
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


def scrape_all_categories(api_token: str, categories: List[str], max_items: int = 10, test_mode: bool = False) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """Scrape multiple categories and aggregate results. Returns error dict if any run fails."""
    aggregated: List[Dict[str, Any]] = []
    for cat in categories:
        res = run_scraper(api_token=api_token, search_query=cat, max_items=max_items, test_mode=test_mode)
        if isinstance(res, dict) and res.get("error"):
            return res
        if isinstance(res, list):
            aggregated.extend(res)
    return aggregated


if __name__ == "__main__":
    print("This module provides `run_scraper` and `scrape_all_categories` functions.")
