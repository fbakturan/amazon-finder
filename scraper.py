from apify_client import ApifyClient
import time

CATEGORIES = {"Electronics": {"url": "https://www.amazon.com/gp/movers-and-shakers/electronics", "blacklist": ["samsung", "apple", "sony", "lg", "panasonic", "philips", "bose", "jbl", "logitech", "canon", "nikon", "gopro", "dell", "hp", "lenovo", "asus", "acer", "microsoft", "beats", "anker", "belkin", "sandisk", "western digital"]}, "Home & Kitchen": {"url": "https://www.amazon.com/gp/movers-and-shakers/home-garden", "blacklist": ["dyson", "irobot", "shark", "bissell", "hoover", "black+decker", "cuisinart", "kitchenaid", "ninja", "instant pot", "oster", "hamilton beach", "keurig", "nespresso", "breville"]}, "Tools & Home Improvement": {"url": "https://www.amazon.com/gp/movers-and-shakers/hi", "blacklist": ["dewalt", "bosch", "makita", "milwaukee", "ryobi", "black+decker", "craftsman", "stanley", "irwin", "klein tools", "3m"]}, "Automotive": {"url": "https://www.amazon.com/gp/movers-and-shakers/automotive", "blacklist": ["bosch", "michelin", "goodyear", "bridgestone", "castrol", "mobil 1", "shell", "pennzoil", "valvoline", "armor all"]}, "Cell Phones & Accessories": {"url": "https://www.amazon.com/gp/movers-and-shakers/wireless", "blacklist": ["apple", "samsung", "otterbox", "spigen", "anker", "belkin", "mophie", "zagg", "uag"]}, "Computers & Accessories": {"url": "https://www.amazon.com/gp/movers-and-shakers/pc", "blacklist": ["logitech", "razer", "corsair", "steelseries", "hyperx", "dell", "hp", "microsoft", "apple", "samsung", "seagate", "western digital", "kingston", "crucial", "asus"]}, "Kitchen & Dining": {"url": "https://www.amazon.com/gp/movers-and-shakers/kitchen", "blacklist": ["kitchenaid", "cuisinart", "lodge", "le creuset", "all-clad", "oxo", "pyrex", "corningware", "ninja", "instant pot"]}, "Pet Supplies": {"url": "https://www.amazon.com/gp/movers-and-shakers/pet-supplies", "blacklist": ["purina", "pedigree", "royal canin", "hill's", "blue buffalo", "iams", "nutro", "wellness", "kong", "furminator"]}, "Sports & Outdoors": {"url": "https://www.amazon.com/gp/movers-and-shakers/sporting-goods", "blacklist": ["nike", "adidas", "under armour", "puma", "reebok", "new balance", "north face", "patagonia", "columbia", "yeti", "hydro flask", "coleman", "garmin", "fitbit", "gopro"]}}

def scrape_all_categories(apify_token, selected_categories, max_items_per_category=100):
    client = ApifyClient(apify_token)
    all_products = []
    for category_name in selected_categories:
        if category_name not in CATEGORIES:
            continue
        category_url = CATEGORIES[category_name]["url"]
        run_input = {"startUrls": [{"url": category_url}], "maxItems": max_items_per_category, "proxyConfiguration": {"useApifyProxy": True}, "maxRequestRetries": 3}
        try:
            run = client.actor("junglee/amazon-crawler").call(run_input=run_input)
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                asin = item.get("asin", "")
                product = {"asin": asin, "title": item.get("title") or "Unknown", "brand": (item.get("brand") or "").lower().strip(), "price": float(item.get("price") or 0), "image_url": item.get("thumbnailImage", ""), "category": category_name, "amazon_url": f"https://www.amazon.com/dp/{asin}", "rating": float(item.get("stars") or 0), "reviews_count": int(item.get("reviewsCount") or 0)}
                all_products.append(product)
            time.sleep(2)
        except Exception as e:
            print(f"Error: {e}")
    return all_products

def filter_brands(products, category_name):
    if category_name not in CATEGORIES:
        return products
    blacklist = CATEGORIES[category_name]["blacklist"]
    return [p for p in products if not any(b in p["brand"] or b in p["title"].lower() for b in blacklist)]
