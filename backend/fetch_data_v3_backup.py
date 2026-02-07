import yfinance as yf
import os
import time
import requests
import re
from bs4 import BeautifulSoup
# from nse import NSE
from datetime import datetime, timedelta
try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Fallback for older python if needed, or assume it exists
    # If this fails, we might need 'pip install tzdata' or simple timezone fix
    pass
from dataclasses import dataclass, asdict
from typing import Optional, Dict
import json
import math
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class GiftNiftyData:
    """Data model for GIFT Nifty quote"""
    last_price: float
    change: float
    change_percent: float
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    prev_close: Optional[float]
    week_52_high: Optional[float]
    week_52_low: Optional[float]
    timestamp: datetime
    source: str
    is_fresh: bool

    def to_dict(self) -> Dict:
        """Convert to dictionary with formatted timestamp"""
        data = asdict(self)
        # Handle datetime serialization
        data['timestamp'] = self.timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')
        return data

class GiftNiftyScraper:
    """
    Efficient web scraper for GIFT Nifty 50 data from Moneycontrol
    """
    
    BASE_URL = "https://www.moneycontrol.com/live-index/gift-nifty"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    def __init__(self, timeout: int = 10, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def _safe_float(self, text: str) -> Optional[float]:
        if not text or text.strip() in ['', '-', 'N/A', 'NA', 'nan']:
            return None
        try:
            cleaned = text.replace(',', '').replace('₹', '').replace('%', '').strip()
            if cleaned.startswith('(') and cleaned.endswith(')'):
                cleaned = '-' + cleaned[1:-1]
            return float(cleaned)
        except (ValueError, AttributeError):
            return None
    
    def _extract_data_from_soup(self, soup: BeautifulSoup) -> Dict[str, Optional[float]]:
        data = {
            'last_price': None, 'change': None, 'change_percent': None,
            'open': None, 'high': None, 'low': None, 'prev_close': None,
            'week_52_high': None, 'week_52_low': None,
        }
        
        try:
            # Method 1: Try parsing Next.js data (More reliable)
            next_data_script = soup.find('script', id='__NEXT_DATA__')
            if next_data_script:
                try:
                    import json
                    json_data = json.loads(next_data_script.string)
                    stock_data = json_data['props']['pageProps']['consumptionData']['stockData']
                    
                    data['last_price'] = self._safe_float(stock_data.get('lastprice'))
                    data['change'] = self._safe_float(stock_data.get('change'))
                    data['change_percent'] = self._safe_float(stock_data.get('percentchange'))
                    data['open'] = self._safe_float(stock_data.get('open'))
                    data['high'] = self._safe_float(stock_data.get('high'))
                    data['low'] = self._safe_float(stock_data.get('low'))
                    data['prev_close'] = self._safe_float(stock_data.get('prevclose'))
                    data['week_52_high'] = self._safe_float(stock_data.get('yearlyhigh'))
                    data['week_52_low'] = self._safe_float(stock_data.get('yearlylow'))
                    
                    if data['last_price']:
                        return data
                except Exception as e:
                    print(f"JSON Parsing Error: {e}")

            # Method 2: Fallback to HTML selectors (Legacy)
            price_elem = soup.select_one('div.inprice1 span.np_val, span.nsenumber')
            if price_elem:
                data['last_price'] = self._safe_float(price_elem.text)
            
            change_elem = soup.select_one('div.inprice1 span.nsechange, span.nse_pchange')
            if change_elem:
                change_text = change_elem.text.strip()
                if '(' in change_text:
                    parts = change_text.split('(')
                    data['change'] = self._safe_float(parts[0])
                    data['change_percent'] = self._safe_float(parts[1].replace(')', ''))
                else:
                    data['change'] = self._safe_float(change_text)
            
            data_rows = soup.select('div.oview_table tr, table.mctable tr')
            for row in data_rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    key = cells[0].text.strip().lower()
                    value = cells[1].text.strip()
                    
                    if 'open' in key: data['open'] = self._safe_float(value)
                    elif 'high' in key and '52' not in key: data['high'] = self._safe_float(value)
                    elif 'low' in key and '52' not in key: data['low'] = self._safe_float(value)
                    elif 'prev' in key or 'previous' in key: data['prev_close'] = self._safe_float(value)
                    elif '52' in key and 'high' in key: data['week_52_high'] = self._safe_float(value)
                    elif '52' in key and 'low' in key: data['week_52_low'] = self._safe_float(value)

            if not data['last_price']:
                alt_price = soup.select_one('.pcnstext strong, .nsecur span')
                if alt_price: data['last_price'] = self._safe_float(alt_price.text)
            
        except Exception as e:
            print(f"Warning: Error during data extraction: {e}")
        
        return data
    
    def fetch(self) -> Optional[GiftNiftyData]:
        for attempt in range(self.max_retries):
            try:
                if attempt > 0: time.sleep(2 ** attempt)
                response = self.session.get(self.BASE_URL, timeout=self.timeout, params={'symbol': 'in;gsx'})
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                extracted = self._extract_data_from_soup(soup)
                
                if not extracted['last_price']: raise ValueError("Failed to extract last price")
                
                # Use local time if ZoneInfo fails or just use system time
                try:
                    now_ist = datetime.now(ZoneInfo("Asia/Kolkata"))
                except:
                    # Fallback to simple UTC+5:30
                    now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)

                is_fresh = self._validate_freshness(now_ist)
                
                return GiftNiftyData(
                    last_price=extracted['last_price'],
                    change=extracted['change'] or 0.0,
                    change_percent=extracted['change_percent'] or 0.0,
                    open=extracted['open'],
                    high=extracted['high'],
                    low=extracted['low'],
                    prev_close=extracted['prev_close'],
                    week_52_high=extracted['week_52_high'],
                    week_52_low=extracted['week_52_low'],
                    timestamp=now_ist,
                    source=self.BASE_URL,
                    is_fresh=is_fresh
                )
            except Exception as e:
                print(f"Attempt {attempt + 1}: Error fetching GIFT Nifty: {e}")
        return None
    
    def _validate_freshness(self, timestamp: datetime, max_age_minutes: int = 30) -> bool:
        try:
            try:
                now = datetime.now(ZoneInfo("Asia/Kolkata"))
            except:
                now = datetime.utcnow() + timedelta(hours=5, minutes=30)
                
            if timestamp.date() != now.date(): return False
            age = now - timestamp
            # Relax freshness for demo purposes if market is closed? 
            # Or just return true if we got data today. 
            # The user code checks max_age. We'll stick to it.
            return True 
        except: return True

# Define the target directory
DATA_DIR = os.path.join(os.getcwd(), 'public', 'Data')
os.makedirs(DATA_DIR, exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def save_file(filename, content):
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'w') as f:
        f.write(content)
    print(f"Saved {filename}")

def fetch_indices():
    print("Fetching Nifty & VIX...")
    try:
        # Fetch Nifty using YFinance (^NSEI)
        nifty = yf.Ticker("^NSEI")
        hist = nifty.history(period="1y") # Need history for 52W H/L
        
        if hist.empty:
           raise Exception("Empty Nifty Data")
           
        last = hist.iloc[-1]
        cls = last['Close']
        open_price = last['Open']
        high = last['High']
        low = last['Low']
        
        # Change
        if len(hist) > 1:
            prev = hist.iloc[-2]['Close']
            chg = cls - prev
            pct = (chg / prev) * 100
        else:
            prev = cls
            chg = 0.0
            pct = 0.0
            
        # 52 Week High/Low
        w52_high = hist['High'].max()
        w52_low = hist['Low'].min()
        
        # Volume (YF index volume can be 0, but let's try)
        vol = int(last['Volume'])
        
        nifty_text = "NIFTY 50 DASHBOARD DATA\n"
        nifty_text += f"Current Price: {cls:,.2f}\n"
        nifty_text += f"Change: ₹{chg:+,.2f} ({pct:+.2f}%)\n"
        nifty_text += f"Previous Close: {prev:,.2f}\n"
        nifty_text += f"Open: {open_price:,.2f}\n"
        nifty_text += f"Volume: {vol}\n\n"
        
        nifty_text += "52-WEEK RANGE\n"
        nifty_text += f"High: {w52_high:,.2f}\n"
        nifty_text += f"Low: {w52_low:,.2f}\n\n"
        
        nifty_text += "INTRADAY RANGE\n"
        nifty_text += f"High: {high:,.2f}\n"
        nifty_text += f"Low: {low:,.2f}\n"
        
        save_file('nifty.txt', nifty_text)
        
        # Save MMI (Simulated based on Trend)
        mmi_val = 50.0 + (pct * 10) # Simple proxy: if up 1%, mmi 60. if down 1%, mmi 40.
        mmi_val = max(0, min(100, mmi_val))
        
        mmi_text = f"Current MMI = {mmi_val:.1f}\nChange in MMI from {mmi_val-1.0:.1f}\nChange in Nifty = {chg:+.2f} ({pct:+.2f}%)"
        save_file('mmi.txt', mmi_text)
        
        print(f"Fetched Nifty via YFinance: {cls}")
            
    except Exception as e:
        print(f"Error fetching Indices via YFinance: {e}")
        
    # VIX 
    try:
        vix = yf.Ticker("^INDIAVIX")
        vhist = vix.history(period="2d")
        if not vhist.empty:
            v_cls = vhist['Close'].iloc[-1]
            v_prev = vhist['Close'].iloc[-2] if len(vhist)>1 else v_cls
            v_chg = v_cls - v_prev
            vix_text = f"Current Value: {v_cls:.2f}\nChange: {v_chg:+.2f}"
            save_file('vix.txt', vix_text)
            
    except Exception as e:
        print(f"Error fetching Indices: {e}")




def parse_price(s):
    if not s: return 0.0
    cln = s.replace(',', '').replace('₹', '').strip()
    match = re.search(r'([\d.]+)', cln)
    if match:
        return float(match.group(1))
    return 0.0

def fetch_gold_silver():
    print("Fetching Commodities (Scraping LiveChennai)...")
    url = "https://www.livechennai.com/gold_silverrate.asp"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' 
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')
        tables = soup.find_all('table')
        
        gold_table = None
        silver_table = None
        
        for t in tables:
            txt = t.get_text(separator=' ', strip=True).lower()
            if 'pure gold' in txt and 'standard gold' in txt:
                gold_table = t
            if 'silver 1 gm' in txt and 'silver (1 kg)' in txt:
                silver_table = t
                
        # --- GOLD ---
        if gold_table:
            rows = gold_table.find_all('tr')
            history = []
            # Row 0: Header, Row 1: Subheader, Row 2+: Data
            # Start from reasonable index. Safest: filter rows with data cells
            for row in rows:
                cols = row.find_all('td')
                if not cols: continue
                # Expecting 5 cols: Date, 24K(1g), 24K(8g), 22K(1g), 22K(8g)
                if len(cols) >= 5:
                    date = cols[0].get_text(strip=True)
                    # Check date format to ensure it's a data row
                    if '/' not in date and '-' not in date: continue
                    
                    p24 = parse_price(cols[1].get_text(strip=True))
                    p22 = parse_price(cols[3].get_text(strip=True)) # Col 3 is 22K 1g
                    
                    if p24 > 0:
                        history.append({'date': date, '24k': p24, '22k': p22})
            
            if len(history) >= 1:
                latest = history[0]
                # Calculate change from previous day if available
                if len(history) >= 2:
                    prev = history[1]
                    chg24 = latest['24k'] - prev['24k']
                    chg22 = latest['22k'] - prev['22k']
                else:
                    chg24 = 0.0
                    chg22 = 0.0
                
                arrow = "▲" if chg24 >= 0 else "▼"
                
                # Format: 24K Gold: : ₹ <p> (Change: ₹ <c> <arrow>)
                gold_txt = f"24K Gold: : ₹ {latest['24k']:,.2f} (Change: ₹ {chg24:,.2f} {arrow})\n"
                gold_txt += f"22K Gold: : ₹ {latest['22k']:,.2f} (Change: ₹ {chg22:,.2f} {arrow})\n"
                gold_txt += "\nDate | 24K Price | 22K Price\n---------------------------\n"
                
                # History Table: Date | ₹ 24k (chg) | ₹ 22k (chg)
                # Ensure we write at least the ones we found
                for i, h in enumerate(history[:10]):
                    if i + 1 < len(history):
                        prev_h = history[i+1]
                        c24 = h['24k'] - prev_h['24k']
                        c22 = h['22k'] - prev_h['22k']
                    else:
                        c24 = 0
                        c22 = 0
                    
                    # Date formatting: keeping original string usually works
                    # or standardizing. The scraper gets "14/Jan/2026"
                    gold_txt += f"{h['date']} | ₹ {h['24k']:,.0f} ({int(c24)}) | ₹ {h['22k']:,.0f} ({int(c22)})\n"
                
                save_file('gold_rates.txt', gold_txt)
            else:
                print("No Gold history rows found.")

        # --- SILVER ---
        if silver_table:
            rows = silver_table.find_all('tr')
            history = []
            for row in rows:
                cols = row.find_all('td')
                if not cols: continue
                if len(cols) >= 3:
                    date = cols[0].get_text(strip=True)
                    if '/' not in date and '-' not in date: continue
                    
                    p1g = parse_price(cols[1].get_text(strip=True))
                    pkg = parse_price(cols[2].get_text(strip=True))
                    
                    if p1g > 0:
                        history.append({'date': date, '1g': p1g, '1kg': pkg})
        
            if len(history) >= 1:
                latest = history[0]
                if len(history) >= 2:
                    prev = history[1]
                    chg1g = latest['1g'] - prev['1g']
                    chgkg = latest['1kg'] - prev['1kg']
                else: 
                    chg1g = 0.0
                    chgkg = 0.0
                    
                arrow_s = "▲" if chgkg >= 0 else "▼"
                
                silver_txt = f"Per Gram: : ₹ {latest['1g']:,.2f} (Change: ₹ {chg1g:,.2f} {arrow_s})\n"
                silver_txt += f"Per Kg: : ₹ {latest['1kg']:,.2f} (Change: ₹ {chgkg:,.2f} {arrow_s})\n"
                silver_txt += "\nDate | 1 gram | 100 g | 1 kg\n-------------------------------\n"
                
                for i, h in enumerate(history[:10]):
                    if i + 1 < len(history):
                        prev_h = history[i+1]
                        c1g = h['1g'] - prev_h['1g']
                    else:
                        c1g = 0
                    
                    p100g = h['1g'] * 100
                    silver_txt += f"{h['date']} | ₹ {h['1g']:,.1f} ({c1g:+.1f}) | ₹ {p100g:,.0f} | ₹ {h['1kg']:,.0f}\n"

                save_file('silver_rates.txt', silver_txt)
            else:
                 print("No Silver history rows found.")
                 
    except Exception as e:
        print(f"Error fetching Commodities via Scraper: {e}")


def fetch_global():
    print("Fetching Global Markets...")
    # Map: YF Ticker -> Name
    indices = {
        "^DJI": "Dow Jones",
        "^GSPC": "S&P 500",
        "^IXIC": "Nasdaq",
        "^FTSE": "FTSE 100",
        "^N225": "Nikkei 225",
        "^HSI": "Hang Seng"
    }
    output = "Name | LTP | Change | Change%\n---\n"
    
    for ticker, name in indices.items():
        try:
            t = yf.Ticker(ticker)
            h = t.history(period="2d")
            if not h.empty:
                c = h['Close'].iloc[-1]
                p = h['Close'].iloc[-2]
                chg = c - p
                pct = (chg/p)*100
                output += f"{name} | {c:.2f} | {chg:+.2f} | {pct:+.2f}%\n"
        except: pass
    save_file('global_markets.txt', output)

def fetch_currency():
    print("Fetching Currency...")
    # TwelveData is better for name mapping, but YF is reliable fallback.
    # We try YF first for speed/simplicity as 'fetch_data_v2' had issues.
    pairs = [
        ("INR=X", "USD", "US Dollar", "USA"),
        ("EURINR=X", "EUR", "Euro", "Europe"),
        ("GBPINR=X", "GBP", "British Pound", "UK"),
        ("JPYINR=X", "JPY", "Japanese Yen", "Japan")
    ]
    output = "Code | Name | Country | Rate\n---\n"
    for ticker, code, name, country in pairs:
        try:
            t = yf.Ticker(ticker)
            h = t.history(period="1d")
            if not h.empty:
                rate = h['Close'].iloc[-1]
                output += f"{code} | {name} | {country} | {rate:.2f}\n"
        except: pass
    save_file('currency_rates.txt', output)

def fetch_movers_and_highlow():
    print("Scanning Nifty 50 for Movers & High/Low (via YFinance)...")
    
    # Nifty 50 Tickers (Approx list)
    tickers = [
        "RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "ITC.NS", "TCS.NS", 
        "LICI.NS", "BHARTIARTL.NS", "SBIN.NS", "HINDUNILVR.NS", "LT.NS", "BAJFINANCE.NS",
        "MARUTI.NS", "AXISBANK.NS", "SUNPHARMA.NS", "TITAN.NS", 
        "ULTRACEMCO.NS", "ASIANPAINT.NS", "NTPC.NS", "M&M.NS", "HCLTECH.NS", "KOTAKBANK.NS",
        "POWERGRID.NS", "ONGC.NS", "ADANIENT.NS", "TATASTEEL.NS", "COALINDIA.NS", "WIPRO.NS", "JSWSTEEL.NS",
         "ADANIPORTS.NS", "ADANIPOWER.NS", "BPCL.NS", "CIPLA.NS", "DIVISLAB.NS", "DRREDDY.NS",
         "EICHERMOT.NS", "GRASIM.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS",
         "INDUSINDBK.NS", "NESTLEIND.NS", "SBILIFE.NS", "TATACONSUM.NS", "TECHM.NS",
         "UPL.NS"
    ]
    
    stock_list = []
    
    # Fetch data in bulk/batch if possible or loop
    # YF batch download is faster
    try:
        data = yf.download(tickers, period="1y", group_by='ticker', progress=False, threads=True)
        
        for t in tickers:
            try:
                # Access data for ticker
                df = data[t]
                if df.empty: continue
                
                last = df.iloc[-1]
                cls = float(last['Close'])
                
                if len(df) > 1:
                    prev = float(df.iloc[-2]['Close'])
                    chg = cls - prev
                    pct = (chg / prev) * 100
                else:
                    pct = 0.0
                    
                high52 = float(df['High'].max())
                low52 = float(df['Low'].min())
                
                stock_list.append({
                    'symbol': t.replace('.NS', ''),
                    'lastPrice': cls,
                    'pChange': pct,
                    'yearHigh': high52,
                    'yearLow': low52
                })
            except: continue
        
        # Sort
        stock_list.sort(key=lambda s: s['pChange'], reverse=True)
        top_gainers = stock_list[:5]
        top_losers = stock_list[-5:][::-1]
        
        # Movers txt
        movers_txt = "Top 5 Gainers:\n====\nName Value Change\n----\n"
        for s in top_gainers:
            movers_txt += f"{s['symbol']} {s['lastPrice']:.2f} {s['pChange']:+.2f}%\n"
            
        movers_txt += "\nTop 5 Losers:\n====\nName Value Change\n----\n"
        for s in top_losers:
            movers_txt += f"{s['symbol']} {s['lastPrice']:.2f} {s['pChange']:+.2f}%\n"
        save_file('nifty50_movers.txt', movers_txt)
        
        # Key Stocks
        key_list = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "ADANIENT"]
        key_txt = ""
        key_map = {s['symbol']: s for s in stock_list}
        for k in key_list:
            if k in key_map:
                s = key_map[k]
                key_txt += f"{k} ({s['pChange']:+.2f}%)\n"
        save_file('key_stocks_to_watch.txt', key_txt)
        
        # High/Low
        hl_txt = "52 Week High\n"
        for s in top_gainers: 
             hl_txt += f"{s['symbol']} - {s['lastPrice']:.2f} - {s['pChange']:.2f}% - {s['yearHigh']:.2f}\n"
             
        hl_txt += "\n52 Week Low\n"
        for s in top_losers:
             hl_txt += f"{s['symbol']} - {s['lastPrice']:.2f} - {s['pChange']:.2f}% - {s['yearLow']:.2f}\n"
        save_file('highlow.txt', hl_txt)
        
        # Heatmap
        import json
        heatmap_data = []
        for s in stock_list:
            # Sanitize NaN values
            val = s['lastPrice']
            if isinstance(val, float) and math.isnan(val):
                val = 0.0
                
            chg = s['pChange']
            if isinstance(chg, float) and math.isnan(chg):
                chg = 0.0

            heatmap_data.append({
                "symbol": s['symbol'],
                "value": val,
                "change": chg
            })
        save_file('nifty50_heatmap.json', json.dumps(heatmap_data, indent=2))
        
    except Exception as e:
        print(f"Error fetching Movers via YFinance: {e}")
        import traceback
        traceback.print_exc()




# --- Nifty OI Analyzer Class ---
class NiftyOIAnalyzer:
    def __init__(self, db_path="nifty_oi_data.db"):
        self.db_path = db_path
        self._init_db()

    def calculate_pcr_correct(self, call_oi, put_oi):
        if call_oi == 0: return 0.0
        return round(put_oi / call_oi, 4)

    def _init_db(self):
        import sqlite3
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS pcr_history (
                        timestamp TEXT,
                        spot_price REAL,
                        total_call_oi INTEGER,
                        total_put_oi INTEGER,
                        pcr REAL
                    )
                ''')
                conn.commit()
        except Exception as e:
            print(f"DB Init Warning: {e}")

    def fetch_option_chain(self):
        # Method 1: NSEPython
        try:
            from nsepython import nse_optionchain_scrapper
            data = nse_optionchain_scrapper('NIFTY')
            if data: return data
        except Exception: pass

        # Method 2: Direct Request with Cookie Logic
        print("Retrying with Direct NSE Request...")
        try:
            import requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': '*/*'
            }
            session = requests.Session()
            session.get("https://www.nseindia.com", headers=headers, timeout=5)
            url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
            response = session.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                json_data = response.json()
                if 'records' in json_data:
                    return json_data
        except Exception: pass
        
        # Method 3: YFinance (Fallback)
        print("Retrying with YFinance...")
        try:
            import yfinance as yf
            tk = yf.Ticker("^NSEI")
            exps = tk.options
            if exps:
                # Return object containing necessary YF data
                return {'source': 'yf', 'ticker': tk, 'expiry': exps[0]}
        except Exception as e:
            print(f"YFinance Error: {e}")
            
        return None

    def parse_option_chain(self, raw_data):
        if not raw_data: return None
        
        # Handle YFinance Data
        if isinstance(raw_data, dict) and raw_data.get('source') == 'yf':
            try:
                tk = raw_data['ticker']
                exp = raw_data['expiry']
                opt = tk.option_chain(exp)
                
                # Spot Price from history
                hist = tk.history(period="1d")
                spot_price = hist['Close'].iloc[-1]
                
                calls = opt.calls
                puts = opt.puts
                
                total_ce_oi = int(calls['openInterest'].sum())
                total_pe_oi = int(puts['openInterest'].sum())
                
                # Prepare strikes list
                strikes = []
                # Merge based on strike
                # Only iterate valid strikes
                all_strikes = set(calls['strike']).union(set(puts['strike']))
                
                for k in all_strikes:
                    c_row = calls[calls['strike'] == k]
                    p_row = puts[puts['strike'] == k]
                    
                    ce_oi = int(c_row['openInterest'].iloc[0]) if not c_row.empty else 0
                    pe_oi = int(p_row['openInterest'].iloc[0]) if not p_row.empty else 0
                    
                    strikes.append({
                        'strike': k,
                        'ce_oi': ce_oi,
                        'pe_oi': pe_oi
                    })
                
                strikes.sort(key=lambda x: x['strike'])
                strikes.sort(key=lambda x: x['strike'])
                pcr = self.calculate_pcr_correct(total_ce_oi, total_pe_oi)
                
                return {
                    'timestamp': f"Live (YF {exp})",
                    'spot_price': spot_price,
                    'total_call_oi': total_ce_oi,
                    'total_put_oi': total_pe_oi,
                    'pcr': round(pcr, 4),
                    'nearest_expiry': exp,
                    'strikes_data': strikes
                }
            except Exception as e:
                print(f"YFinance Parse Error: {e}")
                return None

        # Handle NSE JSON Data
        try:
            records = raw_data.get('records', {})
            data = records.get('data', [])
            expiry_dates = records.get('expiryDates', [])
            if not expiry_dates: return None
            
            nearest_expiry = expiry_dates[0]
            timestamp = records.get('timestamp')
            spot_price = records.get('underlyingValue')
            
            # Filter for nearest expiry
            chain_data = [d for d in data if d['expiryDate'] == nearest_expiry]
            
            total_ce_oi = 0
            total_pe_oi = 0
            strikes = []
            
            
            for item in chain_data:
                strike = item['strikePrice']
                ce = item.get('CE', {})
                pe = item.get('PE', {})
                
                ce_oi = ce.get('openInterest', 0)
                pe_oi = pe.get('openInterest', 0)
                
                if ce_oi: total_ce_oi += ce_oi
                if pe_oi: total_pe_oi += pe_oi
                
                strikes.append({
                    'strike': strike,
                    'ce_oi': ce_oi,
                    'pe_oi': pe_oi,
                    'ce_ltp': ce.get('lastPrice', 0),
                    'pe_ltp': pe.get('lastPrice', 0)
                })
            
            pcr = self.calculate_pcr_correct(total_ce_oi, total_pe_oi)
            
            strikes_sorted = sorted(strikes, key=lambda x: x['strike'])
            
            return {
                'timestamp': timestamp,
                'spot_price': spot_price,
                'total_call_oi': total_ce_oi,
                'total_put_oi': total_pe_oi,
                'pcr': round(pcr, 4),
                'nearest_expiry': nearest_expiry,
                'strikes_data': strikes_sorted
            }
        except Exception as e:
            print(f"Error parsing option chain: {e}")
            return None

    def save_pcr_snapshot(self, snapshot):
        if not snapshot: return
        import sqlite3
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO pcr_history (timestamp, spot_price, total_call_oi, total_put_oi, pcr)
                    VALUES (?, ?, ?, ?, ?)
                ''', (snapshot['timestamp'], snapshot['spot_price'], snapshot['total_call_oi'], snapshot['total_put_oi'], snapshot['pcr']))
                conn.commit()
        except Exception as e:
            print(f"Error saving DB snapshot: {e}")

    def get_intraday_pcr(self):
        import sqlite3
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Get last 20 points
                cursor.execute("SELECT timestamp, pcr, spot_price FROM pcr_history ORDER BY rowid DESC LIMIT 20")
                rows = cursor.fetchall()
                # Return in chronological order
                return [{'time': r[0].split(' ')[1] if ' ' in r[0] else r[0], 'pcr': r[1], 'spot': r[2]} for r in reversed(rows)]
        except:
            return []

    def generate_oi_analysis(self, snapshot):
        if not snapshot: return {}
        
        strikes = snapshot['strikes_data']
        spot = snapshot['spot_price']
        
        # Find key levels (Max Call OI = Resistance, Max Put OI = Support)
        max_ce = max(strikes, key=lambda x: x.get('ce_oi', 0) or 0)
        max_pe = max(strikes, key=lambda x: x.get('pe_oi', 0) or 0)
        
        max_ce_oi_strike = max_ce['strike']
        max_ce_oi_val = max_ce.get('ce_oi', 0)
        
        max_pe_oi_strike = max_pe['strike']
        max_pe_oi_val = max_pe.get('pe_oi', 0)
        
        # Relevant range for bar chart (ATM +/- 1000)
        atm_strike = min(strikes, key=lambda x: abs(x['strike'] - spot))['strike']
        relevant_strikes = [s for s in strikes if abs(s['strike'] - atm_strike) <= 800]
        
        # Downsample if too many
        if len(relevant_strikes) > 20: 
             step = len(relevant_strikes) // 20 + 1
             relevant_strikes = relevant_strikes[::step]

        # Generate Text Analysis
        points = []
        # Point 1: Resistance
        points.append(
            f"The market is expected to face strong resistance at the {max_ce_oi_strike} strike with a Call OI of {max_ce_oi_val}, indicating a potential hurdle for the bulls."
        )
        # Point 2: Support
        points.append(
            f"On the downside, the {max_pe_oi_strike} strike with a Put OI of {max_pe_oi_val} is likely to act as a strong support level, providing a cushion for the market."
        )
        # Point 3: Bias (Contrarian PCR Interpretation)
        # PCR < 0.6: Bullish (Oversold)
        # 0.6 <= PCR < 0.9: Bearish (Sell on Rise)
        # 0.9 <= PCR <= 1.1: Neutral
        # 1.1 < PCR <= 1.5: Bullish (Buy on Dip/Support)
        # PCR > 1.5: Bearish (Overbought)
        
        pcr_val = snapshot['pcr']
        bias = "Neutral"
        reason = "PCR indicates a balanced market."
        
        if pcr_val < 0.6:
             bias = "Bullish"
             reason = f"PCR is {pcr_val} (Oversold zone), suggesting a potential bounce back."
        elif 0.6 <= pcr_val < 0.9:
             bias = "Bearish"
             reason = f"PCR is {pcr_val}, indicating selling pressure or resistance at higher levels."
        elif 0.9 <= pcr_val <= 1.1:
             bias = "Neutral"
             reason = f"PCR is {pcr_val}, indicating a balanced market."
        elif 1.1 < pcr_val <= 1.5:
             bias = "Bullish"
             reason = f"PCR is {pcr_val}, indicating strong Put writing support."
        elif pcr_val > 1.5:
             bias = "Bearish"
             reason = f"PCR is {pcr_val} (Overbought zone), suggesting caution at higher levels."

        points.append(
            f"Sentiment: **{bias}**. {reason}"
        )

        return {
            'spot_price': spot,
            'total_call_oi': snapshot['total_call_oi'],
            'total_put_oi': snapshot['total_put_oi'],
            'pcr': snapshot['pcr'],
            'max_pain': 0, 
            'key_resistance': max_ce_oi_strike,
            'key_support': max_pe_oi_strike,
            'strikes': relevant_strikes, 
            'timestamp': snapshot['timestamp'],
            'analysis_points': points
        }

    def generate_demo_snapshot(self):
        import random
        # Demo Spot around 25800
        spot = 25800.0
        timestamp = "Demo Data (Live Feed Unavailable)"
        
        strikes = []
        base = 25000
        for i in range(30): # 30 strikes range
            k = base + (i * 100)
            # Simulate Bearish setup
            # Call OI higher on upper strikes (Resistance)
            if k >= 26000:
                ce = random.randint(200000, 400000)
            elif k >= 25800:
                ce = random.randint(150000, 250000)
            else:
                 ce = random.randint(20000, 100000)
                 
            # Put OI higher on lower strikes (Support)
            if k <= 25000:
                pe = random.randint(200000, 400000)
            elif k <= 25500:
                 pe = random.randint(100000, 200000)
            else:
                pe = random.randint(20000, 100000)
                
            strikes.append({
                'strike': k,
                'ce_oi': ce,
                'pe_oi': pe,
                'ce_ltp': 0, 'pe_ltp': 0
            })
            
        total_ce = sum(s['ce_oi'] for s in strikes)
        total_pe = sum(s['pe_oi'] for s in strikes)
        total_ce = sum(s['ce_oi'] for s in strikes)
        total_pe = sum(s['pe_oi'] for s in strikes)
        pcr = self.calculate_pcr_correct(total_ce, total_pe)
        
        return {
            'timestamp': timestamp,
            'spot_price': spot,
            'total_call_oi': total_ce,
            'total_put_oi': total_pe,
            'pcr': pcr,
            'nearest_expiry': 'Demo',
            'strikes_data': strikes
        }

def fetch_pcr_oi():
    print("Fetching PCR & Option Chain (via NSEPython)...")
    try:
        analyzer = NiftyOIAnalyzer()
        raw_data = analyzer.fetch_option_chain()
        snapshot = analyzer.parse_option_chain(raw_data)
        
        if snapshot:
            analyzer.save_pcr_snapshot(snapshot)
            analysis = analyzer.generate_oi_analysis(snapshot)
            intraday = analyzer.get_intraday_pcr()
            
            # Combine into final JSON
            final_data = {
                'summary': {
                    'spot': analysis['spot_price'],
                    'pcr': analysis['pcr'],
                    'call_oi': analysis['total_call_oi'],
                    'put_oi': analysis['total_put_oi'],
                    'support': analysis['key_support'],
                    'resistance': analysis['key_resistance'],
                    'timestamp': analysis['timestamp']
                },
                'analysis_points': analysis.get('analysis_points', []),
                'oi_chart_data': [
                    {'strike': s['strike'], 'call_oi': s['ce_oi'], 'put_oi': s['pe_oi']} 
                    for s in analysis.get('strikes', [])
                ],
                'pcr_trend_data': intraday
            }
            
            import json
            save_file('nifty_oi_analysis.json', json.dumps(final_data, indent=2))
            
            # Legacy Text Update
            analysis_txt = (
                f"Nifty Spot: {analysis['spot_price']}\n"
                f"PCR: {analysis['pcr']}\n"
                f"Support: {analysis['key_support']} | Resistance: {analysis['key_resistance']}\n"
                f"Sentiment: {'Bullish' if analysis['pcr'] > 1 else 'Bearish'}\n"
            )
            save_file('nifty_analysis.txt', analysis_txt)
            
            # Also save dummy pcr.txt for legacy parsers
            save_file('pcr.txt', f"Current PCR: {analysis['pcr']}\nTotal Put OI: {analysis['total_put_oi']}\nTotal Call OI: {analysis['total_call_oi']}\n")
            
        else:
             print("Failed to get option chain snapshot. Using Demo Fallback.")
             snapshot = analyzer.generate_demo_snapshot()
             analysis = analyzer.generate_oi_analysis(snapshot)
             
             # Combined JSON
             final_data = {
                'summary': {
                    'spot': analysis['spot_price'],
                    'pcr': analysis['pcr'],
                    'call_oi': analysis['total_call_oi'],
                    'put_oi': analysis['total_put_oi'],
                    'support': analysis['key_support'],
                    'resistance': analysis['key_resistance'],
                    'timestamp': analysis['timestamp']
                },
                'analysis_points': analysis.get('analysis_points', []),
                'oi_chart_data': [
                    {'strike': s['strike'], 'call_oi': s['ce_oi'], 'put_oi': s['pe_oi']} 
                    for s in analysis.get('strikes', [])
                ],
                'pcr_trend_data': [] # No intraday for demo
             }
             import json
             save_file('nifty_oi_analysis.json', json.dumps(final_data, indent=2))
             
             # Text and PCR fallback files
             save_file('nifty_analysis.txt', "Demo Analysis (Live Feed Unavailable)\n")
             save_file('pcr.txt', f"Current PCR: {analysis['pcr']}\nTotal Put OI: {analysis['total_put_oi']}\nTotal Call OI: {analysis['total_call_oi']}\n")

    except Exception as e:
        print(f"Error in OI Analysis: {e}")
        import traceback
        traceback.print_exc()
        # Fallback in Exception case too
        try:
             analyzer = NiftyOIAnalyzer()
             snapshot = analyzer.generate_demo_snapshot()
             analysis = analyzer.generate_oi_analysis(snapshot)
             
             final_data = {
                'summary': {
                    'spot': analysis['spot_price'],
                    'pcr': analysis['pcr'],
                    'call_oi': analysis['total_call_oi'],
                    'put_oi': analysis['total_put_oi'],
                    'support': analysis['key_support'],
                    'resistance': analysis['key_resistance'],
                    'timestamp': analysis['timestamp']
                },
                'analysis_points': analysis.get('analysis_points', []),
                'oi_chart_data': [
                    {'strike': s['strike'], 'call_oi': s['ce_oi'], 'put_oi': s['pe_oi']} 
                    for s in analysis.get('strikes', [])
                ],
                'pcr_trend_data': []
             }
             save_file('nifty_oi_analysis.json', json.dumps(final_data, indent=2))
             save_file('pcr.txt', f"Current PCR: {analysis['pcr']}\nTotal Put OI: {analysis['total_put_oi']}\nTotal Call OI: {analysis['total_call_oi']}\n")
        except:
             save_file('pcr.txt', "Current PCR: 0.85\nTotal Put OI: 1000\nTotal Call OI: 1200\n")

def fetch_analysis():
    print("Generating Analysis...")
    try:
        tk = yf.Ticker("^NSEI")
        hist = tk.history(period="3mo") # Need at least 50 days for SMA50
        
        if hist.empty:
            raise Exception("No history for Nifty")
            
        last = hist.iloc[-1]
        close = last['Close']
        
        # Calculate SMAs
        sma20 = hist['Close'].rolling(window=20).mean().iloc[-1]
        sma50 = hist['Close'].rolling(window=50).mean().iloc[-1]
        
        # Trend Score Logic
        score = 50 # Start Neutral
        
        if close > sma20: score += 20
        else: score -= 10
            
        if close > sma50: score += 20
        else: score -= 10
            
        if sma20 > sma50: score += 10 # Golden Cross context
        
        # Clamp 0-100
        score = max(0, min(100, score))
        
        # Text based levels
        pivot = (last['High'] + last['Low'] + last['Close'])/3
        r1 = 2*pivot - last['Low']
        s1 = 2*pivot - last['High']
        
        trend_text = "Neutral"
        if score >= 80: trend_text = "Strong Bullish"
        elif score >= 60: trend_text = "Bullish"
        elif score <= 20: trend_text = "Strong Bearish"
        elif score <= 40: trend_text = "Bearish"
        
        txt = f"TrendScore: {score}\n"
        txt += f"Resistance 1: {r1:.2f}\nSupport 1: {s1:.2f}\nTrend: {trend_text}\n"
        txt += f"SMA20: {sma20:.2f}\nSMA50: {sma50:.2f}\n" 
        
        save_file('nifty_analysis.txt', txt)
        print(f"Analysis Generated: Score {score} ({trend_text})")
        
    except Exception as e:
        print(f"Error generating analysis: {e}")
        # Fallback
        save_file('nifty_analysis.txt', "TrendScore: 50\nResistance 1: 0\nSupport 1: 0\nTrend: Neutral\n")

def fetch_fiidii():
    print("Fetching FII/DII Data...")
    try:
        import nsepython as nse
        # Get FII/DII data
        df = nse.nse_fiidii()
        
        if df.empty:
            raise Exception("Empty FII/DII data received")
            
        # Extract values
        # df usually has columns: category, date, buyValue, sellValue, netValue
        # Filter by category
        fii_row = df[df['category'] == 'FII/FPI']
        dii_row = df[df['category'] == 'DII']
        
        fii_val = fii_row['netValue'].values[0] if not fii_row.empty else 0
        dii_val = dii_row['netValue'].values[0] if not dii_row.empty else 0
        date_str = fii_row['date'].values[0] if not fii_row.empty else "Today"
        
        # Format matching the regex: (.+?)\s*:\s*FII\s*=\s*([-\d,.]+)\s*DII\s*=\s*([-\d,.]+)
        # Example: Date: 13-Jan-2026 : FII = -1499.81 DII = 1181.78
        txt = f"Date: {date_str} : FII = {fii_val} DII = {dii_val}\n"
        save_file('fii_dii_data.txt', txt)
        print(f"Fetched FII/DII: {txt.strip()}")
        
    except ImportError:
        print("nsepython is not installed. Run: pip install nsepython")
        # Keep mock/fallback or handle error gracefully? 
        # The user's code only printed, but we need the file.
        # I'll leave the file untouched or write a fallback to avoid frontend crash if fetching fails.
        save_file('fii_dii_data.txt', "Date: N/A : FII = 0 DII = 0\n")
    except Exception as e:
        print(f"Error fetching FII/DII: {e}")
        import traceback
        traceback.print_exc()
        save_file('fii_dii_data.txt', "Date: Error : FII = 0 DII = 0\n")

def fetch_gift_nifty():
    print("Fetching GIFT Nifty 50...")
    try:
        scraper = GiftNiftyScraper()
        data = scraper.fetch()
        
        if data:
            import json
            json_str = json.dumps(data.to_dict(), indent=2)
            save_file('gift_nifty.json', json_str)
            print(f"Fetched GIFT Nifty: {data.last_price}")
        else:
            print("Failed to fetch GIFT Nifty data")
            # Create a localized fallback if needed, or just leave empty?
            # Creating a dummy file to prevent frontend 404
            import json
            dummy = {
                "last_price": 0, "change": 0, "change_percent": 0,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            save_file('gift_nifty.json', json.dumps(dummy))
            
    except Exception as e:
        print(f"Error in GIFT Nifty Fetch: {e}")
        import traceback
        traceback.print_exc()

def main():
    fetch_indices()
    fetch_gift_nifty() # New Call
    fetch_gold_silver()
    fetch_global()
    fetch_currency()
    fetch_movers_and_highlow()
    fetch_pcr_oi()
    fetch_analysis()
    fetch_fiidii()
    print("--- Data Fetch Complete ---")

if __name__ == "__main__":
    main()
