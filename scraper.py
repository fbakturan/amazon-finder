import time

CATEGORIES = {"Electronics": {"url": "https://www.amazon.com/gp/movers-and-shakers/electronics", "blacklist": ["samsung", "apple", "sony", "lg"]}, "Home & Kitchen": {"url": "https://www.amazon.com/gp/movers-and-shakers/home-garden", "blacklist": ["dyson", "irobot"]}}

def scrape_all_categories(apify_token, selected_categories, max_items_per_category=100):
    """MOCK DATA - Test amaçlı sahte ürünler döndürür"""
    
    mock_products = [
        {"asin": "B08N5WRWNW", "title": "Wireless Earbuds Pro", "brand": "techpro", "price": 29.99, "image_url": "", "category": "Electronics", "amazon_url": "https://www.amazon.com/dp/B08N5WRWNW", "rating": 4.5, "reviews_count": 234},
        {"asin": "B08N5WRWXX", "title": "USB-C Cable Fast Charge", "brand": "cablez", "price": 12.99, "image_url": "", "category": "Electronics", "amazon_url": "https://www.amazon.com/dp/B08N5WRWXX", "rating": 4.2, "reviews_count": 156},
        {"asin": "B08N5WRYYZ", "title": "Phone Stand Adjustable", "brand": "standmaster", "price": 15.99, "image_url": "", "category": "Electronics", "amazon_url": "https://www.amazon.com/dp/B08N5WRYYZ", "rating": 4.7, "reviews_count": 89},
        {"asin": "B08N5WR112", "title": "Screen Protector Glass", "brand": "guardpro", "price": 8.99, "image_url": "", "category": "Electronics", "amazon_url": "https://www.amazon.com/dp/B08N5WR112", "rating": 4.3, "reviews_count": 445},
        {"asin": "B08N5WR223", "title": "Samsung Galaxy S23", "brand": "samsung", "price": 799.99, "image_url": "", "category": "Electronics", "amazon_url": "https://www.amazon.com/dp/B08N5WR223", "rating": 4.8, "reviews_count": 1205},
        {"asin": "B08N5WR334", "title": "Apple iPhone 15", "brand": "apple", "price": 999.99, "image_url": "", "category": "Electronics", "amazon_url": "https://www.amazon.com/dp/B08N5WR334", "rating": 4.9, "reviews_count": 3421},
        {"asin": "B08N5WR445", "title": "LED Desk Lamp", "brand": "brightlight", "price": 24.99, "image_url": "", "category": "Electronics", "amazon_url": "https://www.amazon.com/dp/B08N5WR445", "rating": 4.4, "reviews_count": 312},
        {"asin": "B08N5WR556", "title": "Bluetooth Speaker Mini", "brand": "soundwave", "price": 19.99, "image_url": "", "category": "Electronics", "amazon_url": "https://www.amazon.com/dp/B08N5WR556", "rating": 4.1, "reviews_count": 178},
    ]
    
    # Sadece seçilen kategorilerdekileri döndür
    filtered = [p for p in mock_products if p["category"] in selected_categories]
    
    # max_items kadar döndür
    return filtered[:max_items_per_category]

def filter_brands(products, category_name):
    """Büyük markaları filtrele"""
    if category_name not in CATEGORIES:
        return products
    blacklist = CATEGORIES[category_name]["blacklist"]
    return [p for p in products if not any(b in p["brand"].lower() or b in p["title"].lower() for b in blacklist)]
