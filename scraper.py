from apify_client import ApifyClient
import time

# Kategoriler ve Marka Kara Listesi
CATEGORIES = {
    "Electronics": {
        "url": "https://www.amazon.com/gp/movers-and-shakers/electronics",
        "blacklist": ["samsung", "apple", "sony", "lg", "panasonic", "philips", "bose", "jbl", "logitech", "canon", "nikon", "gopro", "dell", "hp", "lenovo", "asus", "acer", "microsoft", "beats", "anker", "belkin", "sandisk", "western digital"]
    },
    "Home & Kitchen": {
        "url": "https://www.amazon.com/gp/movers-and-shakers/home-garden",
        "blacklist": ["dyson", "irobot", "shark", "bissell", "hoover", "black+decker", "cuisinart", "kitchenaid", "ninja", "instant pot", "oster", "hamilton beach", "keurig", "nespresso", "breville"]
    },
    "Tools & Home Improvement": {
        "url": "https://www.amazon.com/gp/movers-and-shakers/hi",
        "blacklist": ["dewalt", "bosch", "makita", "milwaukee", "ryobi", "black+decker", "craftsman", "stanley", "irwin", "klein tools", "3m"]
    },
    "Automotive": {
        "url": "https://www.amazon.com/gp/movers-and-shakers/automotive",
        "blacklist": ["bosch", "michelin", "goodyear", "bridgestone", "castrol", "mobil 1", "shell", "pennzoil", "valvoline", "armor all"]
    },
    "Cell Phones & Accessories": {
        "url": "https://www.amazon.com/gp/movers-and-shakers/wireless",
        "blacklist": ["apple", "samsung", "otterbox", "spigen", "anker", "belkin", "mophie", "zagg", "uag"]
    },
    "Computers & Accessories": {
        "url": "https://www.amazon.com/gp/movers-and-shakers/pc",
        "blacklist": ["logitech", "razer", "corsair", "steelseries", "hyperx", "dell", "hp", "microsoft", "apple", "samsung", "seagate", "western digital", "kingston", "crucial", "asus"]
    },
    "Kitchen & Dining": {
        "url": "https://www.amazon.com/gp/movers-and-shakers/kitchen",
        "blacklist": ["kitchenaid", "cuisinart", "lodge", "le creuset", "all-clad", "oxo", "pyrex", "corningware", "ninja", "instant pot"]
    },
    "Pet Supplies": {
        "url": "https://www.amazon.com/gp/movers-and-shakers/pet-supplies",
        "blacklist": ["purina", "pedigree", "royal canin", "hill's", "blue buffalo", "iams", "nutro", "wellness", "kong", "furminator"]
    },
    "Sports & Outdoors": {
        "url": "https://www.amazon.com/gp/movers-and-shakers/sporting-goods",
        "blacklist": ["nike", "adidas", "under armour", "puma", "reebok", "new balance", "north face", "patagonia", "columbia", "yeti", "hydro flask", "coleman", "garmin", "fitbit", "gopro"]
    }
}

def scrape_all_categories(apify_token, selected_categories, max_items_per_category=100):
    """Apify üzerinden GERÇEK veri çeker - Resmi Actor"""
    client = ApifyClient(apify_token)
    all_products = []

    last_run_info = {"url": "", "status": ""}

    for category_name in selected_categories:
        if category_name not in CATEGORIES:
            continue

        category_url = CATEGORIES[category_name]["url"]

        # ACTOR DEĞİŞTİ: apify/amazon-scraper kullanıyoruz
        run_input = {
            "categoryOrProductUrls": [{"url": category_url}],
            "maxItems": max_items_per_category,
            "proxyConfiguration": {"useApifyProxy": True},
            "captchaSolver": True
        }

        try:
            run = client.actor("apify/amazon-scraper").call(run_input=run_input)
            last_run_info["url"] = f"https://console.apify.com/view/runs/{run['id']}"

            dataset = client.dataset(run["defaultDatasetId"])
            items = list(dataset.iterate_items())

            if not items:
                return {"error": True, "run_url": last_run_info["url"], "products": []}

            for item in items:
                asin = item.get("asin", "")
                if not asin: continue 

                price = 0.0
                raw_price = item.get("price")
                if raw_price:
                    if isinstance(raw_price, (int, float)):
                        price = float(raw_price)
                    elif isinstance(raw_price, str):
                        try:
                            import re
                            clean_price = re.sub(r'[^\d.]', '', raw_price)
                            price = float(clean_price)
                        except:
                            price = 0.0

                product = {
                    "asin": asin,
                    "title": item.get("title", "Unknown Product"),
                    "brand": (item.get("brand") or item.get("manufacturer") or "").lower().strip(),
                    "price": price,
                    "image_url": item.get("thumbnailUrl", ""),
                    "category": category_name,
                    "amazon_url": f"https://www.amazon.com/dp/{asin}",
                    "rating": float(item.get("stars", 0)),
                    "reviews_count": int(item.get("reviewsCount", 0))
                }
                all_products.append(product)

        except Exception as e:
            return {"error": True, "message": str(e), "products": []}

    return all_products

def filter_brands(products, category_name):
    if isinstance(products, dict) and products.get("error"):
        return []

    if category_name not in CATEGORIES:
        return products

    blacklist = CATEGORIES[category_name]["blacklist"]
    filtered = []

    for product in products:
        brand = product["brand"]
        title = product["title"].lower()

        is_blacklisted = False
        for blocked_brand in blacklist:
            if blocked_brand in brand or blocked_brand in title:
                is_blacklisted = True
                break

        if not is_blacklisted:
            filtered.append(product)

    return filtered
