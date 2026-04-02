from bs4 import BeautifulSoup
import sys
import re

html_path = 'd:\\안티그래비티\\Coupang_Rank_Tracker_v1\\page_wss.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

def match_class(c, keywords):
    if not c: return False
    if isinstance(c, str): c = [c]
    for cls in c:
        for kw in keywords:
            if kw in cls: return True
    return False

items = soup.find_all('li', class_=lambda c: match_class(c, ['search-product', 'ProductUnit_productUnit__']))
print(f"Products found: {len(items)}")

for i, item in enumerate(items[:2]):
    vendor_item_id = item.get('data-id', '')
    product_id = ''
    a_tag = item.find('a', href=True)
    if a_tag:
        pid_match = re.search(r'/products/(\d+)', a_tag['href'])
        if pid_match:
            product_id = pid_match.group(1)
            
    name_div = item.find('div', class_=lambda c: match_class(c, ['name', 'ProductUnit_productName']))
    name = name_div.text.strip() if name_div else "Unknown"
    
    ad_badge = item.find(class_=lambda c: match_class(c, ['search-product-ad-badge', 'AdMark_adMark']))
    is_ad = "YES" if ad_badge else "NO"
    
    # rocket status might be img with data-badge-id="ROCKET" or "ROCKET_MERCHANT", or "ROCKET_FRESH"
    rocket_badge1 = item.find('span', class_=lambda c: match_class(c, ['badge-rocket']))
    rocket_badge2 = item.find('img', attrs={'data-badge-id': lambda x: x and 'ROCKET' in x})
    is_rocket = "YES" if (rocket_badge1 or rocket_badge2) else "NO"
    
    print(f"[{i}] VenderID: {vendor_item_id}, ProductID: {product_id}, Name: {name}, isAD: {is_ad}, isRocket: {is_rocket}")
