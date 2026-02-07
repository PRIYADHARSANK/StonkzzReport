
import requests
import json

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
    'accept-language': 'en,gu;q=0.9,hi;q=0.8',
    'accept-encoding': 'gzip, deflate, br'
}

def fetch_hl():
    s = requests.Session()
    s.headers.update(headers)
    print("Visiting homepage...")
    s.get("https://www.nseindia.com", timeout=10)
    
    print("Fetching 52 Week High/Low...")
    # Endpoint for 52 week high/low
    # Often: /api/live-analysis-variations?index=yearHigh
    # and /api/live-analysis-variations?index=yearLow
    
    try:
        r_high = s.get("https://www.nseindia.com/api/live-analysis-variations?index=yearHigh", timeout=10)
        print(f"High Status: {r_high.status_code}")
        if r_high.status_code == 200:
             data = r_high.json()
             # usually structure: { "NIFTY 50": { "data": [...] } } or just list
             print("High Data Keys:", data.keys() if isinstance(data, dict) else "List")
    except Exception as e:
        print(f"High Error: {e}")

    try:
        r_low = s.get("https://www.nseindia.com/api/live-analysis-variations?index=yearLow", timeout=10)
        print(f"Low Status: {r_low.status_code}")
    except Exception as e:
        print(f"Low Error: {e}")

if __name__ == "__main__":
    fetch_hl()
