import requests
import json

def fetch_yf_direct():
    print("Fetching Yahoo Finance Options Direct...")
    url = "https://query2.finance.yahoo.com/v7/finance/options/^NSEI"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            # Check structure
            res = data.get('optionChain', {}).get('result', [])
            if res:
                print("Success! Data received.")
                print(f"Quote: {res[0].get('quote', {}).get('regularMarketPrice')}")
                opts = res[0].get('options', [])
                if opts:
                    print(f"Calls count in nearest expiry: {len(opts[0].get('calls', []))}")
                    print(f"Puts count in nearest expiry: {len(opts[0].get('puts', []))}")
            else:
                print("No result in JSON.")
        else:
            print(f"Failed with status {resp.status_code}")
            print(resp.text[:200])
            
    except Exception as e:
        print(f"Direct Fetch Error: {e}")

if __name__ == "__main__":
    fetch_yf_direct()
