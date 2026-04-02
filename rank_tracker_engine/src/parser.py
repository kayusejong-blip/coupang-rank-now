from bs4 import BeautifulSoup

import re

import re

def parse_coupang_html(html: str):
    soup = BeautifulSoup(html, 'html.parser')
    
    products = []
    
    def match_class(c, keywords):
        if not c: return False
        if isinstance(c, str): c = [c]
        for cls in c:
            for kw in keywords:
                if kw in cls: return True
        return False
        
    # v1 (기존) & v2 (새로운 리액트/Nextjs 방식) 호환
    items = soup.find_all('li', class_=lambda c: match_class(c, ['search-product', 'ProductUnit_productUnit__']))
    
    for item in items:
        # 1. Product ID & Vendor Item ID (기존)
        product_id = item.get('id', '')
        if not product_id:
            product_id = item.get('data-product-id', '')
        vendor_item_id = item.get('data-vendor-item-id', '')
        
        # v2 방식인 경우
        item_classes = " ".join(item.get('class', []))
        if 'ProductUnit_productUnit__' in item_classes:
            vendor_item_id = item.get('data-id', '')
            a_tag = item.find('a', href=True)
            if a_tag:
                pid_match = re.search(r'/products/(\d+)', a_tag['href'])
                if pid_match:
                    product_id = pid_match.group(1)
            
        # 2. Product Name
        name_div = item.find('div', class_=lambda c: match_class(c, ['name', 'ProductUnit_productName']))
        name = name_div.text.strip() if name_div else "Unknown"
        
        # 3. Ad Status (광고)
        ad_badge = item.find(class_=lambda c: match_class(c, ['search-product-ad-badge', 'AdMark_adMark']))
        is_ad = "YES" if ad_badge else "NO"
        
        # 4. Rocket Status (로켓배송 여부)
        rocket_badge1 = item.find('span', class_=lambda c: match_class(c, ['badge-rocket']))
        rocket_badge2 = item.find('img', attrs={'data-testid': 'wp-ui-biz-badge-item', 'data-badge-id': lambda x: x and 'ROCKET' in x})
        is_rocket = "YES" if (rocket_badge1 or rocket_badge2) else "NO"
        
        # 5. Thumbnail URL
        thumbnail = ""
        img_tag = item.find('img')
        if img_tag:
            thumbnail = img_tag.get('src') or img_tag.get('data-src') or ""
            # 상대 경로나 프로토콜 없는 경로 처리
            if thumbnail.startswith("//"):
                thumbnail = "https:" + thumbnail
            elif thumbnail.startswith("/"):
                thumbnail = "https://www.coupang.com" + thumbnail
        
        products.append({
            'Product_ID': str(product_id).strip(),
            'Vendor_Item_ID': str(vendor_item_id).strip(),
            'Product_Name': name,
            'Thumbnail': thumbnail,
            'Ad_Status': is_ad,
            'Rocket_Status': is_rocket
        })
        
    return products
