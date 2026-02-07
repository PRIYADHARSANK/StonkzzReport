import requests
import time

class NSEFetcherDebug:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.nseindia.com/option-chain',
        }
        self.session.headers.update(self.headers)

    def test_connection(self):
        print("1. Initializing Cookies (Visiting Homepage)...")
        # Headers for browsing (HTML)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.nseindia.com/',
        })

        try:
            response = self.session.get('https://www.nseindia.com', timeout=15)
            print(f"Homepage Status: {response.status_code}")
        except Exception as e:
            print(f"Homepage Error: {e}")
            return
            
        # Headers for API (JSON/XHR)
        self.session.headers.update({
            'Accept': '*/*',
            'Referer': 'https://www.nseindia.com/option-chain',
            'X-Requested-With': 'XMLHttpRequest',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        })
        # Remove Upgrade-Insecure-Requests for XHR
        if 'Upgrade-Insecure-Requests' in self.session.headers:
            del self.session.headers['Upgrade-Insecure-Requests']

        print("\n2. Fetching Option Chain API...")
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
        try:
            response = self.session.get(url, timeout=15)
            print(f"API Status: {response.status_code}")
            if response.status_code != 200:
                print(f"Response Content (First 200 chars): {response.text[:200]}")
            else:
                print("Success! Data received.")
                data = response.json()
                print(f"Records found: {'records' in data}")
                if 'records' not in data:
                    print(f"JSON Keys: {list(data.keys())}")
                    print(f"Full JSON: {data}")
        except Exception as e:
            print(f"API Error: {e}")

if __name__ == "__main__":
    debug = NSEFetcherDebug()
    debug.test_connection()
