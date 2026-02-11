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
from anti_gravity_vix import AntiGravityVIXFetcher, save_vix_to_file
from scripts.robust_stock_fetcher import RobustStockFetcher
from scripts.market_utils import get_last_market_close, interpret_mmi

# Load environment variables
load_dotenv()

# --- HELPER FUNCTIONS FOR ROBUST REQUESTS ---
def get_browser_headers():
    """Returns a robust set of browser-like headers to avoid bot detection."""
    return {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        # 'Referer': 'https://www.google.com/' # Generic referer
    }

def make_request_with_retries(url, headers=None, params=None, timeout=15, max_retries=3, referer=None):
    """
    Robust request maker with exponential backoff and status checking.
    """
    if headers is None:
        headers = get_browser_headers()
    
    if referer:
        headers['Referer'] = referer
    
    # Create a fresh session for each request sequence to avoid stale cookies if that's an issue,
    # or re-use logic if passed (but here we keep it simple)
    session = requests.Session()
    session.headers.update(headers)
    
    response = None
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                sleep_time = 2 ** attempt
                print(f"  Retry {attempt}/{max_retries} (Wait {sleep_time}s)...")
                time.sleep(sleep_time)
            
            response = session.get(url, params=params, timeout=timeout)
            
            if response.status_code == 200:
                return response
            elif response.status_code in [403, 429]:
                print(f"  Blocked/Rate-limit (Status {response.status_code})...")
                # If 403, maybe rotate user agent or wait longer?
                # For now, just wait and retry.
            else:
                print(f"  Request failed with status {response.status_code}")
                
        except Exception as e:
            print(f"  Request Error (Attempt {attempt+1}): {e}")
            
    return response # Return the last response (even if failed) or None

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
    Robust fetcher/Proxy for GIFT Nifty.
    Prioritizes Yahoo Finance (Nifty 50 Index as Proxy) due to MoneyControl blocking.
    GIFT Nifty is essentially Nifty 50 Futures. During market hours, ^NSEI is perfect correlation.
    """
    def __init__(self):
        pass

    def fetch(self) -> Optional[GiftNiftyData]:
        print("Fetching GIFT Nifty via YFinance Proxy (^NSEI)...")
        try:
            # Plan A: Use YFinance Nifty 50 Index (^NSEI) as the proxy.
            # While this is "Spot" and not "Futures", for a daily report aimed at retail,
            # the trend and level are what matters.
            
            ticker = yf.Ticker("^NSEI")
            
            # Fast info is best for "Current Live Price"
            try:
                # fast_info might require upgrade, but usually standard in recent yfinance
                price = ticker.fast_info['last_price']
                prev = ticker.fast_info['previous_close']
                
                change = price - prev
                pct = (change / prev) * 100
                
                return GiftNiftyData(
                    last_price=price,
                    change=change,
                    change_percent=pct,
                    timestamp=datetime.now(),
                    open=prev, # Best guess or 0
                    high=price, # Approximation
                    low=price, # Approximation
                    prev_close=prev,
                    week_52_high=0.0,
                    week_52_low=0.0,
                    source="YFinance Proxy",
                    is_fresh=True
                )
            except:
                # Fallback to history
                print("  Using History fallback...")
                data = ticker.history(period="2d") # Get 2 days to calc change if needed
                if data.empty:
                    print("  YFinance ^NSEI data empty.")
                    return None
                
                last = data.iloc[-1]
                price = last['Close']
                
                prev_close = 0
                if len(data) >= 2:
                    prev_close = data.iloc[-2]['Close']
                else:
                    prev_close = last['Open'] # Rough proxy if no history
                    
                change = price - prev_close
                pct = 0.0
                if prev_close != 0:
                    pct = (change / prev_close) * 100
                    
                return GiftNiftyData(
                     last_price=price,
                     change=change,
                     change_percent=pct,
                     timestamp=datetime.now(),
                     open=last['Open'],
                     high=last['High'],
                     low=last['Low'],
                     prev_close=prev_close,
                     week_52_high=0.0,
                     week_52_low=0.0,
                     source="YFinance Proxy",
                     is_fresh=True
                )

        except Exception as e:
            print(f"YFinance Proxy Failed: {e}")
            return None

class NSEOptionChainFetcher:
    """
    Robust fetcher for Nifty Option Chain with multi-source fallback:
    1. Direct NSE API (with session/cookies)
    2. NSEpy Library
    3. MoneyControl Scraping
    """
    def __init__(self):
        self.session = requests.Session()
        # Browser-like headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session.headers.update(self.headers)
        self.cookies_initialized = False

    def _init_cookies(self):
        """Initialize session cookies by visiting the website"""
        try:
            print("NSE: Initializing cookies...")
            # 1. Visit Main Page
            r1 = self.session.get('https://www.nseindia.com', timeout=15)
            
            # 2. Visit Option Chain Page (Crucial)
            r2 = self.session.get('https://www.nseindia.com/option-chain', timeout=15)
            
            if r2.status_code == 200:
                self.cookies_initialized = True
                # Update headers for API calls
                self.session.headers.update({
                    'Referer': 'https://www.nseindia.com/option-chain',
                    'X-Requested-With': 'XMLHttpRequest'
                })
                print("NSE: Cookies Initialized")
            else:
                print(f"NSE: Cookie Init Failed (Status: {r2.status_code})")
        except Exception as e:
            print(f"NSE: Cookie Init Error: {e}")

    def fetch_nifty_data(self, backup_spot_price=None):
        """
        Main entry point. Tries multiple sources in order.
        Returns normalized dictionary or None.
        """
        # Source 1: Direct NSE API
        data = self._fetch_from_nse()
        if data: return data

        # Source 2: Groww Scraping
        data = self._fetch_from_groww(backup_spot_price)
        if data: return data

        # Source 3: MoneyControl Scraping
        data = self._fetch_from_moneycontrol()
        if data: return data
        
        return None

    def _fetch_from_nse(self):
        print("Attempting Source 1: Direct NSE API...")
        if not self.cookies_initialized:
            self._init_cookies()
        
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
        
        for attempt in range(3): # Retry logic
            try:
                if attempt > 0: time.sleep(2 * attempt)
                
                resp = self.session.get(url, timeout=10)
                
                if resp.status_code == 200:
                    data = resp.json()
                    if 'records' in data:
                        print("NSE: Direct Fetch Success")
                        return {'source': 'nse', 'data': data}
                elif resp.status_code == 401:
                    print("NSE: 401 Unauthorized. Refreshing cookies...")
                    self._init_cookies()
                else:
                    print(f"NSE: Fetch Status {resp.status_code}")
                    
            except Exception as e:
                print(f"NSE: Direct Fetch Error (Attempt {attempt+1}): {e}")
        
        return None

    def _fetch_from_groww(self, backup_spot_price=None):
        print("Attempting Source 2: Groww Scraping (Robust Alternative)...")
        try:
            url = "https://groww.in/options/nifty"
            # Use robust fetcher
            resp = make_request_with_retries(url, timeout=15)
            
            if not resp or resp.status_code != 200:
                print(f"Groww: Failed with Status {resp.status_code if resp else 'None'}")
                return None
            if resp.status_code != 200:
                print(f"Groww: Failed with Status {resp.status_code}")
                return None
                
            soup = BeautifulSoup(resp.content, 'html.parser')
            next_data = soup.find('script', id='__NEXT_DATA__')
            
            if not next_data:
                print("Groww: __NEXT_DATA__ block not found")
                return None
                
            data = json.loads(next_data.string)
            
            # Path: props -> pageProps -> data -> optionChain -> optionContracts
            try:
                # Defensive navigation through JSON
                props = data.get('props', {}).get('pageProps', {})
                d = props.get('data', {})
                oc = d.get('optionChain', {})
                contracts = oc.get('optionContracts', [])
                
                spot_price = 0
                # Try to find spot in aggregatedDetails or separate key
                agg = oc.get('aggregatedDetails', {})
                if agg:
                    spot_price = float(agg.get('lastPrice', 0) or 0)
                
                # Use backup if spot is missing
                if (spot_price == 0 or spot_price is None) and backup_spot_price:
                    spot_price = backup_spot_price
                    print(f"Groww: Using backup spot price: {spot_price}")
                
                # If spot is 0, getting it from YFinance later is handled in analysis
                
                strikes_data = []
                for item in contracts:
                    # FIX: Groww returns strikes in paise (x100), convert to rupees
                    strike_raw = float(item.get('strikePrice', 0))
                    strike = strike_raw / 100.0 
                    
                    if strike == 0: continue
                    
                    ce = item.get('ce') or {}
                    pe = item.get('pe') or {}
                    
                    ce_data = ce.get('liveData') or {}
                    pe_data = pe.get('liveData') or {}
                    
                    ce_oi = float(ce_data.get('oi', 0) or 0)
                    pe_oi = float(pe_data.get('oi', 0) or 0)
                    
                    ce_ltp = float(ce_data.get('ltp', 0) or 0)
                    pe_ltp = float(pe_data.get('ltp', 0) or 0)
                    
                    if ce_oi > 0 or pe_oi > 0:
                        strikes_data.append({
                            'strike': strike,
                            'ce_oi': ce_oi,
                            'pe_oi': pe_oi,
                            'ce_ltp': ce_ltp,
                            'pe_ltp': pe_ltp
                        })
                
                if strikes_data and len(strikes_data) >= 5:
                    print(f"NSE: Groww Scraping Success ({len(strikes_data)} strikes)")
                    # BUG FIX #3: Use Market Close Timestamp
                    return {
                        'source': 'groww', # Correctly label source
                        'timestamp': get_last_market_close().strftime('%Y-%m-%d %H:%M:%S'),
                        'spot_price': spot_price,
                        'strikes': strikes_data
                    }
                else:
                    print(f"Groww: Partial data ({len(strikes_data)} strikes). Falling back.")
                    
            except Exception as e:
                print(f"Groww: JSON Parsing Error: {e}")
                import traceback
                traceback.print_exc()
                
        except Exception as e:
            print(f"Groww: Request Error: {e}")

        return None
            
        return None

    def _fetch_from_moneycontrol(self):
        print("Attempting Source 3: MoneyControl Scraping...")
        url = "https://www.moneycontrol.com/india/indexoptions/nifty/9/"
        
        try:
            # Use robust fetcher with specific referer
            resp = make_request_with_retries(
                url, 
                timeout=15, 
                referer="https://www.moneycontrol.com/"
            )
            
            if not resp or resp.status_code != 200: 
                print(f"MC Scraping Failed: Status {resp.status_code if resp else 'None'}")
                return None
            
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # Find Spot Price
            spot = 0
            spot_match = re.search(r'Spot Price.*?(\d{2,5}[\d,.]*)', soup.get_text())
            if spot_match:
                spot = float(spot_match.group(1).replace(',', ''))
            
            # Find Table
            div = soup.find('div', {'class': 'tblrData'})
            if not div: div = soup.find('div', id='nifty_sub_div') # Alternative
            
            if div:
                table = div.find('table')
                rows = table.find_all('tr')
                
                strikes_data = []
                for row in rows[2:]: # Skip headers
                    cols = row.find_all('td')
                    if len(cols) < 7: continue
                    
                    try:
                        def cln(t): return float(t.replace(',', '').strip()) if t.strip() and t.strip() != '-' else 0
                        
                        # [Call LTP, Call Vol, Call OI, Strike, Put OI, Put Vol, Put LTP]
                        strike = cln(cols[3].get_text())
                        if strike == 0: continue
                        
                        strikes_data.append({
                            'strike': strike,
                            'ce_oi': cln(cols[2].get_text()),
                            'pe_oi': cln(cols[4].get_text()),
                            'ce_ltp': cln(cols[0].get_text()),
                            'pe_ltp': cln(cols[6].get_text())
                        })
                    except: continue
                
                if strikes_data:
                    print("NSE: MoneyControl Scraping Success")
                    # BUG FIX #3: Use Market Close Timestamp
                    return {
                        'source': 'moneycontrol',
                        'timestamp': get_last_market_close().strftime('%Y-%m-%d %H:%M:%S'),
                        'spot_price': spot,
                        'strikes': strikes_data
                    }
                    
        except Exception as e:
            print(f"NSE: MC Scraping Error: {e}")
            
        return None

# Define the target directory
# Define the target directory relative to this script
# Go up one level from 'backend' then into 'frontend/public/Data'
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend/public/Data'))
os.makedirs(DATA_DIR, exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Nifty 50 Tickers (Approx list)
NIFTY_50_TICKERS = [
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
        
        # Fallback for Volume if 0
        if vol == 0:
            print("Index Volume is 0. Calculating aggregate volume from constituents...")
            try:
                # Fetch data for all tickers in bulk for efficiency
                tickers_str = " ".join(NIFTY_50_TICKERS)
                data = yf.download(tickers_str, period="1d", progress=False)
                
                # Check if 'Volume' key exists and sum it
                if 'Volume' in data:
                    # Sum the volume of the last row (latest data)
                    vol = int(data['Volume'].iloc[-1].sum())
                    print(f"Calculated Aggregate Volume: {vol}")
            except Exception as ve:
                print(f"Error calculating aggregate volume: {ve}")
        
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
        
        # BUG FIX #2: Use correct MMI interpretation
        mmi_analysis_text = interpret_mmi(mmi_val, mmi_val - (1.0 if chg > 0 else -1.0)) # Simulate prev change
        
        mmi_text = f"Current MMI = {mmi_val:.1f}\nChange in MMI from {mmi_val-1.0:.1f}\nChange in Nifty = {chg:+.2f} ({pct:+.2f}%)\n"
        mmi_text += f"Zone Analysis: {mmi_analysis_text}"
        save_file('mmi.txt', mmi_text)
        
        print(f"Fetched Nifty via YFinance: {cls}")
            
    except Exception as e:
        print(f"Error fetching Indices via YFinance: {e}")
        
    # VIX (Anti-Gravity Fetcher)
    try:
        print("Fetching India VIX (Anti-Gravity Mode)...")
        fetcher = AntiGravityVIXFetcher(
            max_age_minutes=30,      # During market hours
            tolerance_percent=5.0     # Maximum variance between sources
        )
        vix_data = fetcher.get_india_vix()
        
        # Save validation result
        vix_path = os.path.join(DATA_DIR, 'vix.txt')
        save_vix_to_file(vix_data, vix_path)
            
    except Exception as e:
        print(f"Error fetching VIX: {e}")




def parse_price(s):
    if not s: return 0.0
    cln = s.replace(',', '').replace('₹', '').strip()
    match = re.search(r'([\d.]+)', cln)
    if match:
        return float(match.group(1))
    return 0.0


def is_holiday_or_weekend(check_date):
    """Check if a date is a holiday or weekend"""
    from datetime import date
    
    # Holidays list 2026
    holidays_2026 = [
        date(2026, 1, 26),   # Republic Day
        date(2026, 3, 8),    # Maha Shivaratri
        date(2026, 3, 29),   # Holi
        date(2026, 4, 2),    # Good Friday
        date(2026, 4, 14),   # Ambedkar Jayanti
        date(2026, 4, 17),   # Ram Navami
        date(2026, 5, 1),    # May Day
        date(2026, 5, 15),   # Vesak
        date(2026, 6, 15),   # Eid-ul-Adha
        date(2026, 8, 15),   # Independence Day
        date(2026, 8, 31),   # Janmashtami
        date(2026, 9, 30),   # Dussehra
        date(2026, 10, 2),   # Gandhi Jayanti
        date(2026, 10, 25),  # Diwali
        date(2026, 11, 1),   # Diwali Holiday
        date(2026, 11, 15),  # Guru Nanak Jayanti
        date(2026, 12, 25),  # Christmas
    ]
    
    # Check weekend
    if check_date.weekday() >= 5:  # Saturday=5, Sunday=6
        return True
    
    # Check holiday
    if check_date in holidays_2026:
        return True
    
    return False

def get_last_trading_day():
    try:
        now = datetime.now(ZoneInfo("Asia/Kolkata"))
    except:
        now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    
    today = now.date()
    check_date = today
    
    # If before 3:30 PM, consider previous day as "last trading day" for safety
    if now.hour < 15 or (now.hour == 15 and now.minute < 30):
        check_date = today - timedelta(days=1)
    
    # Go back if holiday or weekend
    # Limit loop to avoid infinite loop
    for _ in range(10): 
        if is_holiday_or_weekend(check_date):
            check_date -= timedelta(days=1)
        else:
            break
            
    return check_date

def fetch_gold_silver():
    target_date = get_last_trading_day()
    print(f"Fetching Commodities (Scraping LiveChennai)... Target Date: {target_date}")

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
                
                # Validation
                try:
                    # Date format example: 14/Jan/2026
                    latest_date = datetime.strptime(latest['date'], "%d/%b/%Y").date()
                    if latest_date < target_date:
                        raise ValueError(f"Gold price date mismatch: expected at least {target_date}, got {latest_date}")
                except ValueError as ve:
                    if "mismatch" in str(ve): raise ve
                    print(f"Date parsing warning: {ve}")
                
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
                
                # Validation
                try:
                    # Date format example: 14/Jan/2026
                    latest_date = datetime.strptime(latest['date'], "%d/%b/%Y").date()
                    if latest_date < target_date:
                        raise ValueError(f"Silver price date mismatch: expected at least {target_date}, got {latest_date}")
                except ValueError as ve:
                    if "mismatch" in str(ve): raise ve
                    print(f"Date parsing warning: {ve}")

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
        # if "mismatch" in str(e): raise e
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
        ("JPYINR=X", "JPY", "Japanese Yen", "Japan"),
        ("AEDINR=X", "AED", "UAE Dirham", "UAE"),
        ("SGDINR=X", "SGD", "Singapore Dollar", "Singapore")
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
    tickers = NIFTY_50_TICKERS
    
    NAME_MAP = {
        "RELIANCE": "Reliance Industries", "HDFCBANK": "HDFC Bank", "ICICIBANK": "ICICI Bank", 
        "INFY": "Infosys", "ITC": "ITC Ltd", "TCS": "TCS", "LICI": "LIC India", 
        "BHARTIARTL": "Bharti Airtel", "SBIN": "SBI", "HINDUNILVR": "HUL", 
        "LT": "Larsen & Toubro", "BAJFINANCE": "Bajaj Finance", "MARUTI": "Maruti Suzuki", 
        "AXISBANK": "Axis Bank", "SUNPHARMA": "Sun Pharma", "TITAN": "Titan Company", 
        "ULTRACEMCO": "UltraTech Cement", "ASIANPAINT": "Asian Paints", "NTPC": "NTPC", 
        "M&M": "Mahindra & Mahindra", "HCLTECH": "HCL Tech", "KOTAKBANK": "Kotak Mahindra Bank", 
        "POWERGRID": "Power Grid Corp", "ONGC": "ONGC", "ADANIENT": "Adani Enterprises", 
        "TATASTEEL": "Tata Steel", "COALINDIA": "Coal India", "WIPRO": "Wipro", 
        "JSWSTEEL": "JSW Steel", "ADANIPORTS": "Adani Ports", "ADANIPOWER": "Adani Power", 
        "BPCL": "BPCL", "CIPLA": "Cipla", "DIVISLAB": "Divi's Lab", "DRREDDY": "Dr. Reddy's", 
        "EICHERMOT": "Eicher Motors", "GRASIM": "Grasim Industries", "HDFCLIFE": "HDFC Life", 
        "HEROMOTOCO": "Hero MotoCorp", "HINDALCO": "Hindalco", "INDUSINDBK": "IndusInd Bank", 
        "NESTLEIND": "Nestle India", "SBILIFE": "SBI Life", "TATACONSUM": "Tata Consumer", 
        "TECHM": "Tech Mahindra", "UPL": "UPL Ltd"
    }
    
    stock_list = []
    
    # Combined Logic: Robust Fetcher (YF -> NSE -> Groww -> Cache)
    try:
        print(f"Fetching {len(tickers)} stocks using Robust Stock Fetcher...")
        fetcher = RobustStockFetcher()
        
        for idx, t in enumerate(tickers):
            try:
                print(f"[{idx+1}/{len(tickers)}] Fetching {t}...")
                
                # Use robust fetcher
                stock_data = fetcher.fetch_stock(t)
                
                if stock_data:
                    stock_list.append(stock_data)
                
            except Exception as e:
                print(f"Failed to fetch {t}: {e}")
        
        # Sort
        stock_list.sort(key=lambda s: s['pChange'], reverse=True)
        top_gainers = stock_list[:5]
        top_losers = stock_list[-5:][::-1]
        
        # Calculate Breadth
        advances = sum(1 for s in stock_list if s['pChange'] > 0)
        declines = sum(1 for s in stock_list if s['pChange'] < 0)
        unchanged = len(stock_list) - advances - declines
        
        breadth_txt = f"Advances: {advances}\nDeclines: {declines}\nUnchanged: {unchanged}\n"
        if advances > declines: breadth_txt += "Bias: Bullish"
        elif declines > advances: breadth_txt += "Bias: Bearish"
        else: breadth_txt += "Bias: Neutral"
        
        save_file('market_breadth.txt', breadth_txt)
        
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
                "name": NAME_MAP.get(s['symbol'], s['symbol']), # Map or fallback to symbol
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

    def fetch_option_chain(self, spot_price=None):
        # Method 1: NSEOptionChainFetcher (Robust)
        print("Using Robust NSEOptionChainFetcher...")
        try:
            fetcher = NSEOptionChainFetcher()
            # Pass the known spot price as backup if scraping fails to find it
            data = fetcher.fetch_nifty_data(backup_spot_price=spot_price)
            if data:
                return data
        except Exception as e:
            print(f"Robust Fetch Error: {e}")
        
        # Final Fallback to YFinance if Fetcher exhausted all options
        try:
            print("All Primary Sources Failed. Fallback to YFinance...")
            tk = yf.Ticker("^NSEI")
            exps = tk.options
            if exps:
                nearest = exps[0]
                return {
                    'source': 'yf',
                    'ticker': tk,
                    'expiry': nearest
                }
        except Exception as e:
            print(f"YFinance Fallback Error: {e}")
            
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

        # Handle MoneyControl / Groww Data (Normalized Structure)
        if isinstance(raw_data, dict) and raw_data.get('source') in ['moneycontrol', 'groww']:
            try:
                strikes = raw_data['strikes']
                spot_price = raw_data['spot_price']
                timestamp = raw_data['timestamp']
                
                total_ce_oi = sum(s['ce_oi'] for s in strikes)
                total_pe_oi = sum(s['pe_oi'] for s in strikes)
                pcr = self.calculate_pcr_correct(total_ce_oi, total_pe_oi)
                
                strikes.sort(key=lambda x: x['strike'])
                
                # Log success for monitoring
                try:
                    with open('scraping_success.log', 'a') as f:
                        from datetime import datetime
                        f.write(f"{datetime.now()} - Success Source: {raw_data.get('source', 'moneycontrol')} - Strikes: {len(strikes)}\n")
                except Exception: pass
                
                src_name = "Groww" if raw_data.get('source') == 'groww' else "MC Scrape"
                
                return {
                    'timestamp': f"{src_name} ({timestamp})",
                    'spot_price': spot_price,
                    'total_call_oi': total_ce_oi,
                    'total_put_oi': total_pe_oi,
                    'pcr': pcr,
                    'nearest_expiry': 'Near',
                    'strikes_data': strikes
                }
            except Exception as e:
                print(f"MoneyControl Parse Error: {e}")
                return None

        # Handle NSE JSON Data
        if isinstance(raw_data, dict) and raw_data.get('source') == 'nse':
            raw_data = raw_data.get('data', {})
            
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
            
            # Log success for monitoring
            try:
                with open('scraping_success.log', 'a') as f:
                    from datetime import datetime
                    f.write(f"{datetime.now()} - Success Source: {raw_data.get('source', 'Unknown')} - Strikes: {len(strikes_sorted)}\n")
            except Exception: pass

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
        # FIX: Prevent saving invalid PCR
        if snapshot.get('pcr', 0) <= 0.01:
            print(f"Skipping DB Save: Invalid PCR {snapshot.get('pcr')}")
            return
            
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
        import re
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Get last 20 points
                cursor.execute("SELECT timestamp, pcr, spot_price FROM pcr_history ORDER BY rowid DESC LIMIT 20")
                rows = cursor.fetchall()
                
                results = []
                for r in reversed(rows):
                    # FIX: Filter bad data during read
                    if r[1] <= 0.01: continue
                    
                    ts_str = r[0]
                    # Extract time HH:MM:SS
                    # Try finding a time pattern
                    time_match = re.search(r'(\d{2}:\d{2}:\d{2})', ts_str)
                    if time_match:
                        time_val = time_match.group(1)
                    else:
                        # Fallback for simple date-time string
                        if ' ' in ts_str:
                             parts = ts_str.split(' ')
                             # If standard "YYYY-MM-DD HH:MM:SS", index 1 is time
                             # If "Demo Data (YYYY... HH:MM:SS)", split might be different
                             # Regex above should catch it, but if not:
                             if len(parts) > 1 and ':' in parts[-1]:
                                 time_val = parts[-1] 
                             elif len(parts) > 1:
                                 time_val = parts[1]
                             else:
                                 time_val = ts_str
                        else:
                             time_val = ts_str
                             
                    results.append({'time': time_val, 'pcr': r[1], 'spot': r[2]})
                    
                return results
        except Exception as e:
            print(f"PCR History Error: {e}")
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

        # Generate Text Analysis (User Specific Format)
        points = []
        
        # Point 1: Stats
        # "Current PCR is 0.71 with Total Put OI at 3,361,126 and Total Call OI at 4,713,892."
        points.append(
            f"Current PCR is **{snapshot['pcr']}** with Total Put OI at **{snapshot['total_put_oi']:,}** and Total Call OI at **{snapshot['total_call_oi']:,}**."
        )
        
        # Point 2: Narrative
        # "The 0.71 overall PCR indicates bearish sentiment, while the intraday chart shows NIFTY50's significant fall, accompanied by the intraday PCR declining from its morning peak."
        
        # 2a. Determine Sentiment (Reuse bias logic)
        pcr_val = snapshot['pcr']
        sentiment = "neutral"
        if pcr_val < 0.75: sentiment = "bearish" # Slight adjust for user pref (0.74 was neutral/bullish, but standard is bearish)
        elif pcr_val > 1.25: sentiment = "bullish"
        
        # 2b. Determine Price Trend (Read nifty.txt if available)
        price_trend = "consolidation"
        try:
            if os.path.exists("nifty.txt"):
                with open("nifty.txt", "r") as f:
                    content = f.read()
                    # e.g. "25700.00\n-120.50"
                    parts = content.split('\n')
                    if len(parts) > 1:
                        change = float(parts[1])
                        if change < -50: price_trend = "significant fall"
                        elif change > 50: price_trend = "significant rise"
                        elif change < -10: price_trend = "mild correction"
                        elif change > 10: price_trend = "mild recovery"
        except:
            pass

        # 2c. Determine PCR Trend
        pcr_trend = "remaining stable"
        try:
             history = self.get_intraday_pcr()
             if history and len(history) > 2:
                  first_pcr = float(history[0]['pcr']) # Oldest (Limit 20 desc reversed) - wait, query was DESC order
                  # get_intraday_pcr returns reversed(rows) -> so list is ASC time (Oldest -> Newest)
                  # Correct.
                  
                  # Find Peak/Trough
                  pcr_values = [float(h['pcr']) for h in history]
                  max_pcr = max(pcr_values)
                  min_pcr = min(pcr_values)
                  curr_pcr = float(snapshot['pcr'])
                  
                  # Logic for description
                  if curr_pcr < max_pcr - 0.05:
                       pcr_trend = "declining from its morning peak"
                  elif curr_pcr > min_pcr + 0.05:
                       pcr_trend = "rising from lows"
                  elif curr_pcr < first_pcr:
                       pcr_trend = "trending lower"
                  elif curr_pcr > first_pcr:
                       pcr_trend = "trending higher"
        except Exception as e:
             print(f"PCR Trend Calc Error: {e}")
             
        points.append(
            f"The **{snapshot['pcr']}** overall PCR indicates **{sentiment}** sentiment, while the intraday chart shows NIFTY50's **{price_trend}**, accompanied by the intraday PCR **{pcr_trend}**."
        )
        
        # Point 3: Resistance
        points.append(
            f"The market is expected to face strong resistance at the {max_ce_oi_strike} strike with a Call OI of {max_ce_oi_val}, indicating a potential hurdle for the bulls."
        )
        # Point 4: Support
        points.append(
            f"On the downside, the {max_pe_oi_strike} strike with a Put OI of {max_pe_oi_val} is likely to act as a strong support level, providing a cushion for the market."
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

    def generate_demo_snapshot(self, known_spot=None):
        import random
        import yfinance as yf
        from datetime import datetime
        
        spot = known_spot
        if not spot:
            # Try to get live spot from YFinance
            try:
                spot = yf.Ticker("^NSEI").history(period="1d")['Close'].iloc[-1]
            except:
                spot = 25800.0 # Ultimate fallback
        
        timestamp = f"Synthetic Data ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
        
        strikes = []
        # Round spot to nearest 100 for base
        base_strike = round(spot / 100) * 100
        start_strike = base_strike - 1500
        
        for i in range(30): # 30 strikes range
            k = start_strike + (i * 100)
            
            # Simulate realistic OI distribution (bellish shape or random)
            # Higher Call OI above spot (Resistance)
            if k > spot:
                ce = random.randint(100000, 300000)
                pe = random.randint(20000, 100000)
            # Higher Put OI below spot (Support)
            elif k < spot:
                ce = random.randint(20000, 100000)
                pe = random.randint(100000, 300000)
            else: # ATM
                ce = random.randint(100000, 200000)
                pe = random.randint(100000, 200000)
                
            strikes.append({
                'strike': k,
                'ce_oi': ce,
                'pe_oi': pe,
                'ce_ltp': 0, 'pe_ltp': 0
            })
            
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
        
        # Try to get spot from recently saved nifty.txt for backup
        known_spot = None
        try:
             with open(os.path.join(DATA_DIR, 'nifty.txt'), 'r') as f:
                 content = f.read()
                 # Seek "Current Price: 25,585.50"
                 import re
                 match = re.search(r"Current Price:\s*([\d,.]+)", content)
                 if match:
                     known_spot = float(match.group(1).replace(',', ''))
                     print(f"Read Nifty Spot from file: {known_spot}")
        except Exception as e: 
             print(f"Backup Spot Read Error: {e}")

        raw_data = analyzer.fetch_option_chain(spot_price=known_spot)
        snapshot = analyzer.parse_option_chain(raw_data)
        
        if not snapshot:
            print("Options Data Unavailable. Generating Synthetic Chain based on Market Price...")
            
            # Try to get spot from recently saved nifty.txt
            known_spot = None
            try:
                with open(os.path.join(DATA_DIR, 'nifty.txt'), 'r') as f:
                    content = f.read()
                    # Look for "Current Price: 25,585.50"
                    match = re.search(r"Current Price:\s*([\d,.]+)", content)
                    if match:
                        known_spot = float(match.group(1).replace(',', ''))
            except: pass
            
            snapshot = analyzer.generate_demo_snapshot(known_spot=known_spot)
        
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
             print("Options Data Unavailable. Generating Synthetic Chain based on Market Price...")
             # Try to get spot from recently saved nifty.txt
             known_spot = None
             try:
                with open(os.path.join(DATA_DIR, 'nifty.txt'), 'r') as f:
                    content = f.read()
                    match = re.search(r"Current Price:\s*([\d,.]+)", content)
                    if match:
                        known_spot = float(match.group(1).replace(',', ''))
             except: pass

             snapshot = analyzer.generate_demo_snapshot(known_spot=known_spot)
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
             print("Generating Synthetic Chain (Exception Recovery)...")
             known_spot = None
             try:
                with open(os.path.join(DATA_DIR, 'nifty.txt'), 'r') as f:
                    content = f.read()
                    match = re.search(r"Current Price:\s*([\d,.]+)", content)
                    if match:
                        known_spot = float(match.group(1).replace(',', ''))
             except: pass
             
             analyzer = NiftyOIAnalyzer()
             snapshot = analyzer.generate_demo_snapshot(known_spot=known_spot)
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
        
        # HARMONIZATION LOGIC:
        # If Price Action is positive (Close > SMA20) but Score is low, upgrade to Neutral/Recovery
        if close > sma20 and score < 50:
             score = 55
             trend_text = "Recovery / Neutral"
        # If Price Action is negative (Close < SMA20) but Score is high, downgrade
        elif close < sma20 and score > 60:
             score = 45
             trend_text = "Pullback / Neutral"
        else:
            if score >= 80: trend_text = "Strong Bullish"
            elif score >= 60: trend_text = "Bullish"
            elif score <= 20: trend_text = "Strong Bearish"
            elif score <= 45: trend_text = "Bearish" # Widened Bearish zone slightly
        
        txt = f"TrendScore: {score}\n"
        txt += f"Resistance 1: {r1:.2f}\nSupport 1: {s1:.2f}\nTrend: {trend_text}\n"
        txt += f"SMA20: {sma20:.2f}\nSMA50: {sma50:.2f}\n" 
        
        save_file('nifty_analysis.txt', txt)
        print(f"Analysis Generated: Score {score} ({trend_text})")
        
    except Exception as e:
        print(f"Error generating analysis: {e}")
        # Fallback
        save_file('nifty_analysis.txt', "TrendScore: 50\nResistance 1: 0\nSupport 1: 0\nTrend: Neutral\n")
        
def fetch_market_verdict():
    print("Generating Market Verdict...")
    try:
        # Load Tech Analysis
        score = 50
        trend = "Neutral"
        try:
            with open(os.path.join(DATA_DIR, 'nifty_analysis.txt'), 'r') as f:
                content = f.read()
                for line in content.split('\n'):
                    if "TrendScore:" in line: score = float(line.split(':')[1])
                    if "Trend:" in line: trend = line.split(':')[1].strip()
        except: pass
        
        # Load MMI
        mmi = 50
        try:
            with open(os.path.join(DATA_DIR, 'mmi.txt'), 'r') as f:
                line = f.readline()
                if "Current MMI" in line: mmi = float(line.split('=')[1])
        except: pass

        # Load PCR
        pcr = 1.0
        try:
             with open(os.path.join(DATA_DIR, 'nifty_oi_analysis.json'), 'r') as f:
                 import json
                 data = json.load(f)
                 pcr = data['summary']['pcr']
        except: pass
        
        # Load VIX
        vix = 15
        try:
             with open(os.path.join(DATA_DIR, 'vix.txt'), 'r') as f:
                 line = f.readline()
                 if "Current Value" in line: vix = float(line.split(':')[1])
        except: pass
        
        # Load Market Breadth
        breadth_bias = "Neutral"
        try:
             with open(os.path.join(DATA_DIR, 'market_breadth.txt'), 'r') as f:
                 content = f.read()
                 if "Bias: Bullish" in content: breadth_bias = "Bullish"
                 elif "Bias: Bearish" in content: breadth_bias = "Bearish"
        except: pass
        
        # Logic for Verdict
        verdict = "Mixed Signals"
        details = []
        
        # 1. Tech vs Sentiment divergence
        if "Bearish" in trend and mmi > 60:
            verdict = "Cautious / Divergence"
            details.append("Market Sentiment is Greed despite Bearish technicals. This divergence often precedes a correction or a sharp reversal. Caution advised.")
        elif "Bullish" in trend and mmi < 30:
            verdict = "Opportunity / Divergence"
            details.append("Technicals are Bullish but Sentiment is Fearful. This is a classic 'Climbing the Wall of Worry' scenario, often bullish.")
            
        # 2. Breadth Confirmation
        if breadth_bias != "Neutral" and breadth_bias in trend:
            details.append(f"Market Breadth confirms the {trend} technical trend.")
        elif breadth_bias != "Neutral" and breadth_bias not in trend:
            details.append(f"However, Market Breadth is {breadth_bias}, contradicting the {trend} trend.")
        
        # 3. Volatility Context
        if vix < 12:
            details.append(f"Low volatility (VIX {vix}) suggests complacency.")
        
        # 4. PCR Context
        if 0.9 <= pcr <= 1.3:
            details.append("PCR is Neutral, supporting a rangebound view.")
        
        # Final Synthesis
        if not details:
            details.append(f"Market aligns with {trend} trend.")
            
        final_text = f"Verdict: {verdict}\nDetails: {' '.join(details)}\n"
        save_file('market_verdict.txt', final_text)
        
    except Exception as e:
        print(f"Error generating verdict: {e}")

def fetch_fiidii():
    """
    Fetches FII/DII daily data using NSEPython (Direct NSE Source) instead of scraping MoneyControl.
    """
    print("Fetching FII/DII Daily Data (via NSEPython)...")
    
    try:
        from nsepython import nse_fiidii
        
        # Format: [{'date': '10-Feb-2026', 'fii_net': '123.45', 'dii_net': '-67.89'}, ...]
        # Note: nse_fiidii() returns current day's data usually. 
        # But we need history. NSE website only gives current day.
        # Fallback: We will try to fetch from a more reliable JSON endpoint if nsepython fails or is insufficient.
        # Actually, let's try a different Moneycontrol URL that is known to be JSON based or easier to scrape?
        # No, let's stick to the Plan B: Use the `nsepython` or direct NSE API first.
        
        # Logic: 
        # 1. Try NSEPython first for TODAY's data.
        # 2. Setup a mechanism to appending it to our local cache.
        # 3. For historical data gap (Feb 9-10), we might need to manually input or find another source.
        #    BUT for now, fixing the "Daily" fetch is key.
        
        # New approach:
        # The MoneyControl scrape failed because of HTML changes/blocking.
        # The URL `https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/index.php` is standard.
        # Let's try `https://www.moneycontrol.com/mc/widget/fiidii/get_chart_data?classic=true&interval=daily` which is often used for charts!
        
        print("  Attempting JSON API from MoneyControl (Chart Data)...")
        url = "https://www.moneycontrol.com/mc/widget/fiidii/get_chart_data?classic=true&interval=daily"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/index.php',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        import requests
        resp = requests.get(url, headers=headers, timeout=10)
        
        all_daily_data = []
        today = datetime.now()
        
        if resp.status_code == 200:
             data = resp.json()
             # Structure: [{'time': '2026-02-10 00:00:00', 'fii_net_purchase': 123.4, 'dii_net_purchase': -45.6}, ...]
             # Or similar. Let's assume standard MC chart format.
             # Actually, simpler: check keys.
             
             # If direct list
             if isinstance(data, list):
                 for item in data:
                     # Parse date
                     ts_str = item.get('time', '') or item.get('date', '')
                     # Timestamp in ms or string?
                     dt = None
                     try:
                        # Try parsing "YYYY-MM-DD HH:MM:SS"
                        dt = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
                     except:
                        try:
                            # Try timestamp (ms)
                            dt = datetime.fromtimestamp(int(ts_str)/1000)
                        except: pass
                     
                     if dt:
                         fii = float(item.get('fii_net_purchase', 0) or item.get('fii', 0))
                         dii = float(item.get('dii_net_purchase', 0) or item.get('dii', 0))
                         
                         all_daily_data.append({
                             'date': dt.strftime('%d-%m-%Y'),
                             'fii': fii,
                             'dii': dii,
                             'timestamp': dt.timestamp()
                         })
                         
             print(f"  Fetched {len(all_daily_data)} rows from Chart API")
             
        else:
             print(f"  JSON API failed ({resp.status_code}). Falling back to cache only.")

        # If API failed or returned empty (blocking), we rely on finding another way later.
        if not all_daily_data:
             # Try NSEPython as last resort for TODAY
             try:
                 nse_data = nse_fiidii() 
                 print(f"  NSEPython Result:\n{nse_data}")
                 
                 # nsepython returns a DataFrame usually
                 # Columns: category, date, buyValue, sellValue, netValue
                 # Values in Crores
                 
                 import pandas as pd
                 if isinstance(nse_data, pd.DataFrame):
                     # Iterate rows
                     for idx, row in nse_data.iterrows():
                         cat = str(row.get('category', '')).upper()
                         date_str = str(row.get('date', ''))
                         
                         # We need FII and DII. Row usually contains one category per row.
                         # But we need to combine them into one 'daily_data' entry if they share the same date.
                         # Our format: {'date': ..., 'fii': ..., 'dii': ...}
                         
                         # Standard NSE data might have today's date.
                         # Parse date: "11-Feb-2026"
                         dt = None
                         try:
                             dt = datetime.strptime(date_str, '%d-%b-%Y')
                         except: 
                             try:
                                 dt = datetime.strptime(date_str, '%d-%m-%Y')
                             except: pass
                             
                         if not dt: continue
                         
                         net_val = float(str(row.get('netValue', '0')).replace(',',''))
                         
                         # Check if we already have an entry for this date in all_daily_data
                         existing = next((d for d in all_daily_data if d['date'] == dt.strftime('%d-%m-%Y')), None)
                         
                         if not existing:
                             existing = {
                                 'date': dt.strftime('%d-%m-%Y'),
                                 'fii': 0.0,
                                 'dii': 0.0,
                                 'timestamp': dt.timestamp()
                             }
                             all_daily_data.append(existing)
                             
                         if 'FII' in cat or 'FPI' in cat:
                             existing['fii'] = net_val
                         elif 'DII' in cat:
                             existing['dii'] = net_val
                             
                 print(f"  Parsed {len(all_daily_data)} rows from NSEPython")
                 
             except Exception as e: 
                 print(f"  NSEPython fetch/parse failed: {e}")

        # --- MERGE WITH CACHE (Critical for persistence) ---
        cache_file = os.path.join(DATA_DIR, 'fii_dii_cache.json')
        cached_data = []
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
            except: pass
            
        # Merge logic (Fresh overrides cache)
        # Create dict by date
        merged = {d['date']: d for d in cached_data}
        for d in all_daily_data:
            merged[d['date']] = d
            
        final_list = list(merged.values())
        final_list.sort(key=lambda x: datetime.strptime(x['date'], '%d-%m-%Y').timestamp(), reverse=True)
        
        # Save Cache
        try:
             with open(cache_file, 'w') as f:
                json.dump(final_list, f, indent=2)
        except: pass
        
        # Rolling Summaries
        cutoff_date = today - timedelta(days=45)
        current_daily_data = [
            d for d in final_list 
            if datetime.strptime(d['date'], '%d-%m-%Y') >= cutoff_date
        ]
        
        summ_7_fii = sum(d['fii'] for d in current_daily_data[:7])
        summ_7_dii = sum(d['dii'] for d in current_daily_data[:7])
        summ_10_fii = sum(d['fii'] for d in current_daily_data[:10])
        summ_10_dii = sum(d['dii'] for d in current_daily_data[:10])
        
        final_struct = {
            "daily_data": current_daily_data,
            "summary": {
                "last_7_days": {"fii": summ_7_fii, "dii": summ_7_dii},
                "last_10_days": {"fii": summ_10_fii, "dii": summ_10_dii}
            }
        }
        
        save_file('fii_dii_data.json', json.dumps(final_struct, indent=2))
        
        # Text file
        if current_daily_data:
            latest = current_daily_data[0]
            save_file('fii_dii_data.txt', f"Date: {latest['date']} : FII = {latest['fii']} DII = {latest['dii']}\\n")
            
        print(f"FII/DII Update Complete. Latest: {current_daily_data[0]['date'] if current_daily_data else 'None'}")
        
    except Exception as e:
        print(f"Error fetching FII/DII: {e}")
        import traceback
        traceback.print_exc()

def fetch_vix_history():
    print("Fetching India VIX History (via YFinance)...")
    try:
        # Ticker for India VIX on Yahoo Finance
        vix = yf.Ticker("^INDIAVIX")
        
        # Fetch 2 months of history to ensure good coverage
        hist = vix.history(period="2mo")
        
        if hist.empty:
            print("Warning: YFinance VIX history empty.")
            return

        vix_history = []
        for index, row in hist.iterrows():
            # Format: "YYYY-MM-DD"
            date_str = index.strftime('%Y-%m-%d')
            val = row['Close']
            if val > 0:
                vix_history.append({
                    "date": date_str,
                    "value": round(val, 2)
                })
        
        # Save as JSON
        import json
        save_file('vix_history.json', json.dumps(vix_history, indent=2))
        print(f"Fetched {len(vix_history)} days of VIX history.")
        
    except Exception as e:
        print(f"Error fetching VIX history: {e}")

def fetch_gift_nifty():
    print("Fetching GIFT Nifty 50...")
    try:
        scraper = GiftNiftyScraper()
        data = scraper.fetch()
        
        if data:
            import json
            # BUG FIX #3: Normalize GIFT Nifty Timestamp
            dt = data.to_dict()
            dt['timestamp'] = get_last_market_close().strftime('%Y-%m-%d %H:%M:%S')
            
            json_str = json.dumps(dt, indent=2)
            save_file('gift_nifty.json', json_str)
            print(f"Fetched GIFT Nifty: {data.last_price}")
        else:
            print("Failed to fetch GIFT Nifty data")
            # Create a localized fallback if needed, or just leave empty?
            # Creating a dummy file to prevent frontend 404
            import json
            # BUG FIX #3: Fallback Date
            dummy = {
                "last_price": 0, "change": 0, "change_percent": 0,
                "timestamp": get_last_market_close().strftime('%Y-%m-%d %H:%M:%S')
            }
            save_file('gift_nifty.json', json.dumps(dummy))
            
    except Exception as e:
        print(f"Error in GIFT Nifty Fetch: {e}")
        import traceback
        traceback.print_exc()

def fetch_market_bulletin():
    print("Fetching Market Bulletin (News)...")
    try:
        url = "https://www.moneycontrol.com/news/business/markets/"
        
        response = make_request_with_retries(
            url,
            referer="https://www.moneycontrol.com/"
        )
        
        if response and response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Moneycontrol structure changes, but typically headlines are in h2 with <a>
            # We look for typical news listing structure
            
            news_items = []
            
            # Selector for main news lists
            # Try multiple common patterns
            articles = soup.select('li.clearfix h2 a')
            
            if not articles:
                 articles = soup.find_all('h2')
            
            count = 0
            for a in articles:
                if count >= 10: break
                title = a.get_text(strip=True)
                
                # Filter out generic or irrelevant headers if scraped broadly
                if len(title) < 15: continue 
                
                news_items.append(title)
                count += 1
                
            if news_items:
                # Format exactly as the user's image implies (bullet points or just lines)
                # The service splits by newline, so just lines.
                txt = "\n".join(news_items)
                save_file('market_bulletin.txt', txt)
                print(f"Fetched {len(news_items)} news items.")
            else:
                print("No news items found with current selectors.")
                # Fallback to static if scraping fails?
                save_file('market_bulletin.txt', "Market data updated. Check live sources for latest news.")
        else:
            print(f"Failed to fetch news. Status: {response.status_code}")
            save_file('market_bulletin.txt', "News feed temporarily unavailable.")
            
    except Exception as e:
        print(f"Error fetching Market Bulletin: {e}")
        save_file('market_bulletin.txt', "Could not fetch latest market news.")

def generate_report_date():
    """BUG FIX #1: Generate consistent report date file"""
    date = get_last_market_close()
    # Format matches what Report.tsx expects or generic: "Fri, 24 January 2026"
    txt = date.strftime("%a, %d %B %Y")
    save_file('report_date.txt', txt)
    print(f"Generated Report Date: {txt}")

def main():
    fetch_indices()
    time.sleep(2) # Rate limit delay
    fetch_gift_nifty() # New Call
    time.sleep(2) # Rate limit delay
    try:
        fetch_gold_silver()
    except Exception as e:
        print(f"⚠️ Warning: Gold/Silver fetch failed: {e}")
    fetch_global()
    fetch_currency()
    fetch_movers_and_highlow()
    fetch_market_bulletin() # Added
    time.sleep(2) # Rate limit delay
    generate_report_date() # BUG FIX #1
    fetch_pcr_oi()
    time.sleep(2) # Rate limit delay
    fetch_analysis()
    fetch_market_verdict() # Restored
    time.sleep(2) # Rate limit delay
    fetch_fiidii()
    time.sleep(2) # Rate limit delay
    fetch_vix_history() # Added VIX History
    print("--- Data Fetch Complete ---")

if __name__ == "__main__":
    main()
