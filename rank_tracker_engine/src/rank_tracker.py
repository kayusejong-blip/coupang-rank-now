from src.parser import parse_coupang_html

def calculate_rank(html_pages, target_product_id: str):
    all_products = []
    for html in html_pages:
        all_products.extend(parse_coupang_html(html))
        
    rank_incl_ad = 0
    rank_excl_ad = 0
    
    result = {
        'Rank': '-',             # 구버전 호환용 (순수 순위)
        'Rank_Incl_Ad': '-',     # 구버전 호환용 (화면상 위치)
        'Organic_Rank': '-',     # 일반(순수) 순위
        'Ad_Rank': '-',          # 광고 노출 순위 (화면상 위치)
        'Product_ID': target_product_id,
        'Product_Name': '',
        'Thumbnail': '',
        'Ad_Status': 'NO', 
        'Rocket_Status': 'NO',
        'Status': 'NOT_FOUND',
        'Total_Scanned': len(all_products)
    }
    
    found_organic = False
    found_ad = False
    
    for product in all_products:
        rank_incl_ad += 1
        
        is_target = (product['Product_ID'] == str(target_product_id) or product['Vendor_Item_ID'] == str(target_product_id))
        
        if product['Ad_Status'] == 'NO':
            rank_excl_ad += 1
            if is_target and not found_organic:
                result['Organic_Rank'] = rank_excl_ad
                result['Rank'] = rank_excl_ad
                result['Rank_Incl_Ad'] = rank_incl_ad
                if not result['Product_Name']:
                    result['Product_Name'] = product['Product_Name']
                    result['Thumbnail'] = product.get('Thumbnail', '')
                    result['Rocket_Status'] = product['Rocket_Status']
                found_organic = True
        else: # 광고 상품일 경우
            if is_target and not found_ad:
                result['Ad_Rank'] = rank_incl_ad
                result['Ad_Status'] = 'YES'
                if not result['Product_Name']:
                    result['Product_Name'] = product['Product_Name']
                    result['Thumbnail'] = product.get('Thumbnail', '')
                    result['Rocket_Status'] = product['Rocket_Status']
                found_ad = True
                
        # 일반과 광고 두 개를 다 찾으면 조기 종료
        if found_organic and found_ad:
            break
            
    if found_organic or found_ad:
        result['Status'] = 'FOUND'
        # 만약 일반은 없고 광고로만 떴다면 Rank_Incl_Ad를 광고 순위로 대체 (호환성 목적)
        if not found_organic:
            result['Rank_Incl_Ad'] = result['Ad_Rank']
            
    return result
