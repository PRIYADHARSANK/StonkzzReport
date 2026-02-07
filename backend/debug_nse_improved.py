import requests
import time
import json

def fetch_nse():
    session = requests.Session()
    
    # mimic modern browser (Firefox)
    headers_browser = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Upgrade-Insecure-Requests': '1',
    }
    
    session.headers.update(headers_browser)
    
    print("1. Visiting URL to initialize cookies...")
    try:
        # Visit the main page first
        r1 = session.get("https://www.nseindia.com", timeout=20)
        print(f"Main Page: {r1.status_code}")
        
        # Visit the option chain page specifically (crucial for some cookies)
        r2 = session.get("https://www.nseindia.com/option-chain", timeout=20)
        print(f"Option Chain Page: {r2.status_code}")
        
    except Exception as e:
        print(f"Init failed: {e}")
        return

    print("2. Fetching API...")
    # API specific headers
    headers_api = {
        'Accept': '*/*',
        'Referer': 'https://www.nseindia.com/option-chain',
        'X-Requested-With': 'XMLHttpRequest',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }
    # Important: Do not overwrite User-Agent or Cookies
    
    try:
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
        r3 = session.get(url, headers=headers_api, timeout=20)
        print(f"API Status: {r3.status_code}")
        
        if r3.status_code == 200:
            try:
                data = r3.json()
                if 'records' in data:
                    print("Success! 'records' found in response.")
                    print(f"Expiry dates: {data['records']['expiryDates'][:3]}")
                else:
                    print("Failed: JSON received but 'records' missing.")
                    print(f"Keys: {data.keys()}")
            except json.JSONDecodeError:
                print("Failed: Response is not JSON.")
                print(r3.text[:200])
        else:
            print("Failed: Non-200 Status")
            
    except Exception as e:
        print(f"Fetch failed: {e}")

if __name__ == "__main__":
    fetch_nse()
