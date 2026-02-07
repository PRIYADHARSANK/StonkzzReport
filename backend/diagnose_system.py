
import os
import requests
import nsepython
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()

def test_nsepython():
    print("\n--- Testing NSEPython ---")
    try:
        # Test basic quote
        q = nsepython.nse_quote_ltp("RELIANCE")
        print(f"NSE Quote (RELIANCE): {q}")
        if q and q > 0:
            print("STATUS: SUCCESS")
        else:
            print("STATUS: FAIL (Empty/Zero)")
            
        # Test Option Chain
        print("Testing Option Chain (NIFTY)...")
        oc = nsepython.nse_optionchain_scrapper('NIFTY')
        if oc and 'records' in oc:
            print("STATUS: SUCCESS (Option Chain found)")
        else:
            print("STATUS: FAIL (Option Chain empty/banned)")
            
    except Exception as e:
        print(f"STATUS: CRITICAL FAIL ({e})")

def test_yfinance():
    print("\n--- Testing YFinance ---")
    try:
        t = yf.Ticker("^NSEI")
        hist = t.history(period="1d")
        if not hist.empty:
            print(f"YF Nifty Close: {hist['Close'].iloc[-1]}")
            print("STATUS: SUCCESS")
        else:
            print("STATUS: FAIL (No data)")
    except Exception as e:
        print(f"STATUS: CRITICAL FAIL ({e})")

def test_twelvedata():
    print("\n--- Testing Twelve Data ---")
    key = os.getenv("TWELVE_DATA_KEY")
    if not key:
        print("STATUS: FAIL (No API Key)")
        return
        
    try:
        # Test simple quote
        url = f"https://api.twelvedata.com/price?symbol=USD/INR&apikey={key}"
        r = requests.get(url)
        data = r.json()
        print(f"Response: {data}")
        if 'price' in data:
            print("STATUS: SUCCESS")
        elif 'code' in data and data['code'] == 429:
             print("STATUS: FAIL (Rate Limit)")
        else:
             print("STATUS: FAIL (Error response)")
    except Exception as e:
        print(f"STATUS: CRITICAL FAIL ({e})")

def test_newsapi():
    print("\n--- Testing NewsAPI ---")
    key = os.getenv("NEWS_API_KEY")
    if not key:
        print("STATUS: FAIL (No API Key)")
        return
        
    try:
        url = f"https://newsapi.org/v2/top-headlines?country=in&category=business&apiKey={key}"
        r = requests.get(url)
        data = r.json()
        if data.get('status') == 'ok':
            print(f"Articles found: {data.get('totalResults')}")
            print("STATUS: SUCCESS")
        else:
            print(f"STATUS: FAIL ({data.get('message')})")
    except Exception as e:
        print(f"STATUS: CRITICAL FAIL ({e})")

if __name__ == "__main__":
    print("Running Deep Diagnostic...")
    test_nsepython()
    test_yfinance()
    test_twelvedata()
    test_newsapi()
    print("\nDiagnostic Complete.")
