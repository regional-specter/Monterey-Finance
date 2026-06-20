import os
import re
import json

def extract_json_ld_blocks(file_path):
    """Reads HTML file and extracts all JSON-LD script blocks."""
    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    # Matches everything inside <script type="application/ld+json">...</script>
    pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
    matches = re.findall(pattern, html, re.DOTALL)
    
    blocks = []
    for match in matches:
        try:
            blocks.append(json.loads(match.strip()))
        except json.JSONDecodeError:
            pass
    return blocks

def find_product_listings(blocks):
    """Finds the main ItemList containing product listings from the blocks."""
    products = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        
        # Check for CollectionPage schema
        main_entity = block.get("mainEntity")
        if not main_entity:
            continue
        if isinstance(main_entity, list):
            main_entity = main_entity[0]
            
        if main_entity.get("@type") == "ItemList":
            items = main_entity.get("itemListElement", [])
            for item in items:
                prod = item.get("item")
                if prod and prod.get("@type") == "Product":
                    products.append(prod)
    return products

def parse_additional_properties(product):
    """Extracts raw key-value stats from additionalProperty section."""
    props = {}
    for prop in product.get("additionalProperty", []):
        name = prop.get("name")
        val = prop.get("value")
        if name and val:
            props[name] = val
    return props

def clean_financial_value(val_str):
    """Cleans currency strings into numeric figures or min/max bounds."""
    if not val_str or not isinstance(val_str, str):
        return None
        
    cleaned = re.sub(r'[^\d\.\-KkMm]', '', val_str)
    
    def parse_suffix(s):
        s = s.strip().upper()
        if not s:
            return None
        multiplier = 1.0
        if s.endswith('K'):
            multiplier = 1000.0
            s = s[:-1]
        elif s.endswith('M'):
            multiplier = 1000000.0
            s = s[:-1]
        try:
            return float(s) * multiplier
        except ValueError:
            return None

    # Handle Ranges (e.g. $100K - $250K)
    if '-' in cleaned:
        parts = cleaned.split('-')
        if len(parts) == 2:
            return {
                "min": parse_suffix(parts[0]),
                "max": parse_suffix(parts[1])
            }
            
    val_lower = val_str.lower()
    single_val = parse_suffix(cleaned)
    if not single_val:
        return None
        
    if "under" in val_lower or "less" in val_lower:
        return {"min": 0, "max": single_val}
    elif "over" in val_lower or "more" in val_lower:
        return {"min": single_val, "max": None}
        
    return single_val

def compute_implied_multiple(price, cash_flow):
    """Calculates multiple based on price and cash flow representations."""
    if not price or not cash_flow:
        return None
        
    # Get standard price value
    price_val = price.get("max") or price.get("min") if isinstance(price, dict) else price
    if not price_val:
        return None
        
    # Get standard cash flow value
    if isinstance(cash_flow, dict):
        min_cf = cash_flow.get("min") or 0
        max_cf = cash_flow.get("max")
        cf_val = (min_cf + max_cf) / 2.0 if (max_cf and min_cf > 0) else (max_cf or min_cf)
    else:
        cf_val = cash_flow
        
    if not cf_val or cf_val <= 0:
        return None
        
    return round(float(price_val) / float(cf_val), 2)

def process_product(product):
    """Pre-processes raw product listing into a structured schema."""
    props = parse_additional_properties(product)
    offers = product.get("offers", {})
    addr = offers.get("availableAtOrFrom", {}).get("address", {})
    
    raw_price = props.get("Asking Price")
    raw_revenue = props.get("Revenue")
    raw_cash_flow = props.get("Cash Flow")
    
    clean_price = clean_financial_value(raw_price) or offers.get("price")
    clean_revenue = clean_financial_value(raw_revenue)
    clean_cash_flow = clean_financial_value(raw_cash_flow)
    
    multiple = compute_implied_multiple(clean_price, clean_cash_flow)
    
    return {
        "id": product.get("productId"),
        "name": product.get("name"),
        "url": product.get("url"),
        "description": product.get("description"),
        "location": {
            "city": addr.get("addressLocality"),
            "region": addr.get("addressRegion"),
            "country": addr.get("addressCountry")
        },
        "currency": offers.get("priceCurrency"),
        "financials": {
            "asking_price": clean_price,
            "asking_price_raw": raw_price,
            "revenue": clean_revenue,
            "revenue_raw": raw_revenue,
            "cash_flow": clean_cash_flow,
            "cash_flow_raw": raw_cash_flow,
            "multiple": multiple
        }
    }

def scrape_folder_to_json(input_dir, output_file):
    """Processes all HTML files in a folder and saves output to a JSON file."""
    all_listings = []
    
    for filename in os.listdir(input_dir):
        if not filename.endswith(".html"):
            continue
            
        file_path = os.path.join(input_dir, filename)
        blocks = extract_json_ld_blocks(file_path)
        products = find_product_listings(blocks)
        
        for prod in products:
            processed = process_product(prod)
            all_listings.append(processed)
            
    # Save the output to JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_listings, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully processed {len(all_listings)} listings. Output saved to {output_file}")
    return all_listings

if __name__ == "__main__":
    raw_dir = "/Users/raoabdul/Documents/Development/Monterey-Finance/raw_html"
    out_file = "/Users/raoabdul/Documents/Development/Monterey-Finance/listings_output.json"
    
    if os.path.exists(raw_dir):
        scrape_folder_to_json(raw_dir, out_file)
    else:
        print(f"Error: Directory {raw_dir} does not exist.")
