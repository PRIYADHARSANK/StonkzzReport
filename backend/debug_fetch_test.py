import requests
from bs4 import BeautifulSoup
import re
import json

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        # 'Referer': 'https://www.google.com/'
    }

def test_gift_nifty():
    print("\n--- Testing GIFT Nifty ---")
    url = "https://www.moneycontrol.com/live-index/gift-nifty"
    try:
        resp = requests.get(url, headers=get_headers(), timeout=15)
        print(f"Status Code: {resp.status_code}")
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, 'html.parser')
            script = soup.find('script', id='__NEXT_DATA__')
            if script:
                print("Found __NEXT_DATA__ script")
                data = json.loads(script.string)
                try:
                    stock_data = data['props']['pageProps']['consumptionData']['stockData']
                    print(f"Extracted 'lastprice': {stock_data.get('lastprice')}")
                    print(f"Extracted 'name': {stock_data.get('name')}")
                except KeyError as e:
                    print(f"KeyError in JSON path: {e}")
                    # Print keys to debug
                    print("Available keys in props:", data.get('props', {}).keys())
            else:
                print("FAILED: __NEXT_DATA__ script NOT found")
                # Check if we got a captcha or different page
                if "Access Denied" in resp.text or "Captcha" in resp.text:
                    print("Likely blocked/captcha")
                
                # Try finding legacy selectors
                el = soup.select_one('div.inprice1 span.np_val')
                print(f"Legacy Select check: {el}")
        else:
            print("Failed request")
    except Exception as e:
        print(f"Exception: {e}")

def test_fii_dii():
    print("\n--- Testing FII/DII ---")
    url = "https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/index.php"
    try:
        resp = requests.get(url, headers=get_headers(), timeout=15)
        print(f"Status Code: {resp.status_code}")
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # Check table class
            tables = soup.find_all('table', class_='mctable1')
            print(f"Found {len(tables)} tables with class 'mctable1'")
            
            # Check dates
            daily_date_pattern = re.compile(r'\d{2}-[A-Za-z]{3}-20\d{2}')
            text_matches = daily_date_pattern.findall(resp.text)
            print(f"Regex found {len(text_matches)} date patterns in raw text")
            if text_matches:
                print(f"Sample dates: {text_matches[:5]}")
            
            if not tables:
                print("Trying all tables...")
                tables = soup.find_all('table')
                for i, t in enumerate(tables):
                    txt = t.get_text()
                    matches = daily_date_pattern.findall(txt)
                    if matches:
                        print(f"Table {i} contains {len(matches)} dates. (Potential Target)")
            
        else:
            print("Failed request")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_gift_nifty()
    test_fii_dii()
