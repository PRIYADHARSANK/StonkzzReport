
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def debug_fetch():
    print("Fetching FII/DII Page...")
    url = "https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/index.php"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Status: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print("Scanning for Table 2...")
        tables = soup.find_all('table')
        target = tables[2] if len(tables) > 2 else None
        
        if target:
            rows = target.find_all('tr')
            print(f"Table 2 has {len(rows)} rows.")
            for i, row in enumerate(rows):
                cols = row.find_all('td')
                if cols:
                    date_txt = cols[0].get_text(strip=True)
                    print(f"Row {i} Date: '{date_txt}' | Cols: {len(cols)}")
                    # Try parsing
                    try:
                        dt = datetime.strptime(date_txt, '%d %b %Y')
                        print(f"  Parsed: {dt}")
                    except ValueError as e:
                         print(f"  Parse Error: {e}")
        else:
            print("Table 2 not found.")

            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_fetch()
