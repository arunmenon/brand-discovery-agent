import requests
from bs4 import BeautifulSoup

def scrape_counterfeit_listings(brand_name):
    """Scrape counterfeit brand listings from AliExpress & eBay"""
    fake_brands = set()
    try:

        # AliExpress search
        aliexpress_url = f"https://www.aliexpress.com/wholesale?SearchText={brand_name}"
        response = requests.get(aliexpress_url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        for product in soup.find_all("h1"):
            fake_brands.add(product.text.strip())

        # eBay search
        ebay_url = f"https://www.ebay.com/sch/i.html?_nkw={brand_name}+replica"
        response = requests.get(ebay_url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        for product in soup.find_all("h3", class_="s-item__title"):
            fake_brands.add(product.text.strip())
            
    except requests.exceptions.RequestException as e:
        print(f"[Scraper] Error scraping counterfeit listings for {brand_name}: {e}")
        

    return list(fake_brands)
