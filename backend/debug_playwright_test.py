from playwright.sync_api import sync_playwright
import time
import json
from bs4 import BeautifulSoup
import re

def test_with_playwright():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        
        print("\n--- Testing GIFT Nifty (Playwright) ---")
        try:
            page.goto("https://www.moneycontrol.com/live-index/gift-nifty", timeout=60000)
            page.wait_for_load_state("networkidle")
            
            # Additional wait for dynamic content
            time.sleep(5)
            
            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Check __NEXT_DATA__
            script = soup.find('script', id='__NEXT_DATA__')
            if script:
                 print("Found __NEXT_DATA__ script via Playwright")
                 data = json.loads(script.string)
                 try:
                    stock_data = data['props']['pageProps']['consumptionData']['stockData']
                    print(f"Extracted 'lastprice': {stock_data.get('lastprice')}")
                 except:
                    print("Could not extract path from JSON")
            else:
                 print("__NEXT_DATA__ missing even with Playwright")
                 
            # Check visual selectors
            price = page.locator('.inprice1 .np_val, .nsenumber').first
            if price.is_visible():
                print(f"Visual Price Found: {price.inner_text()}")
            else:
                 print("Visual Price element not found/visible")

        except Exception as e:
            print(f"GIFT Nifty Error: {e}")

        print("\n--- Testing FII/DII (Playwright) ---")
        try:
            page.goto("https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/index.php", timeout=60000)
            page.wait_for_load_state("domcontentloaded") # Network idle might timeout on heavy ad pages
            time.sleep(5)
            
            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Check for Daily Dates
            daily_date_pattern = re.compile(r'\d{2}-[A-Za-z]{3}-20\d{2}')
            matches = daily_date_pattern.findall(content)
            print(f"Found {len(matches)} daily date patterns")
            if matches:
                 print(f"Sample: {matches[:5]}")
            
            # Check specific table
            tables = soup.find_all('table', class_='mctable1')
            print(f"Found {len(tables)} tables with class 'mctable1'")
            
        except Exception as e:
            print(f"FII/DII Error: {e}")
            
        browser.close()

if __name__ == "__main__":
    test_with_playwright()
