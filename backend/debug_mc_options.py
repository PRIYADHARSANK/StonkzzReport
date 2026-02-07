import requests
from bs4 import BeautifulSoup
import json
import re

def fetch_mc_options():
    print("Starting MoneyControl Options Fetch...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.moneycontrol.com/stocks/fno/view_option_chain.php?ind_id=9',
        'Origin': 'https://www.moneycontrol.com',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    # -1. Fetch Homepage
    home_url = "https://www.moneycontrol.com/"
    print(f"-1. GET {home_url} to init cookies...")
    try:
        resp_home = session.get(home_url, timeout=10)
        print(f"Homepage Status: {resp_home.status_code}")
        print(f"Cookies after Homepage: {session.cookies.get_dict()}")
    except Exception as e:
        print(f"Homepage Fetch Error: {e}")

    # 0. Fetch Main Page to init cookies
    main_url = "https://www.moneycontrol.com/stocks/fno/view_option_chain.php?ind_id=9"
    print(f"0. GET {main_url} to init cookies...")
    try:
        resp_main = session.get(main_url, timeout=10)
        print(f"Main Page Status: {resp_main.status_code}")
        print(f"Cookies after Main Page: {session.cookies.get_dict()}")
    except Exception as e:
        print(f"Main Page Fetch Error: {e}")
    
    # 1. Fetch Expiry Dates
    expiry_api = "https://www.moneycontrol.com/stocks/fno/query_tool/get_expdate.php?symbol=BANKNIFTY&inst_type=OPTIDX"
    print(f"1. Fetching Expiry Dates from {expiry_api}...")
    
    try:
        resp_exp = session.get(expiry_api, timeout=10)
        print(f"Expiry API Status: {resp_exp.status_code}")
        
        # Parse Expiry Dates
        soup_exp = BeautifulSoup(resp_exp.content, 'html.parser')
        options = soup_exp.find_all('option')
        
        valid_expiries = [opt['value'] for opt in options if opt.get('value')]
        print(f"Found Expiries: {valid_expiries}")
        
        if not valid_expiries:
            print("No valid expiries found. Aborting.")
            return
            
        selected_expiry = valid_expiries[0]
        print(f"Selected Expiry: {selected_expiry}")
        
        # 2. POST for Option Chain
        url_post = f"https://www.moneycontrol.com/stocks/fno/view_option_chain.php?ind_id=23&sel_exp_date={selected_expiry}"
        
        payload = {
            "instrument_type": "OPTIDX",
            "post_flag": "true",
            "ind_id": "23",
            "sc_id": "BANKNIFTY",
            "short_name": "BANKNIFTY",
            "index_code": "23|BANKNIFTY",
            "sel_exp_date": selected_expiry
        }
        
        print(f"2. POST {url_post} with payload...")
        # Note: Removing X-Requested-With for the main page POST might be safer as it is a form submit
        session.headers.pop('X-Requested-With', None)
        
        response = session.post(url_post, data=payload, timeout=15)
        
        print(f"POST Status Code: {response.status_code}")
        
        with open("mc_options.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("Saved HTML to mc_options.html")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            tables = soup.find_all('table')
            print(f"Tables found: {len(tables)}")
            
            # Check for tblopt
            tbl_opt = soup.find('table', {'class': 'tblopt'})
            if tbl_opt:
                print("SUCCESS: 'tblopt' table found!")
                rows = tbl_opt.find_all('tr')
                print(f"Table Rows: {len(rows)}")
                if len(rows) > 5:
                     print("Table seems populated.")
            else:
                print("WARNING: 'tblopt' table NOT found.")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_mc_options()
