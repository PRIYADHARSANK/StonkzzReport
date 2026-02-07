
import os
import datetime
import time
from dotenv import load_dotenv
from nsepython import nse_quote, nse_optionchain_scrapper, nse_fiidii, nsefetch
import requests
from twelvedata import TDClient
from newsapi import NewsApiClient
import yfinance as yf

# Load environment variables
load_dotenv()

# Configuration
DATA_DIR = os.path.join(os.getcwd(), 'public', 'Data')
os.makedirs(DATA_DIR, exist_ok=True)

TWELVE_DATA_KEY = os.getenv("TWELVE_DATA_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Initialize Clients
td = TDClient(apikey=TWELVE_DATA_KEY) if TWELVE_DATA_KEY and TWELVE_DATA_KEY != "YOUR_TWELVE_DATA_KEY_HERE" else None
newsapi = NewsApiClient(api_key=NEWS_API_KEY) if NEWS_API_KEY and NEWS_API_KEY != "YOUR_NEWS_API_KEY_HERE" else None

def save_file(filename, content):
    with open(os.path.join(DATA_DIR, filename), 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Saved {filename}")

def fetch_indian_indices():
    """
    Fetches Nifty 50 and India VIX. 
    Tries NSEPython first, falls back to YFinance if blocked.
    """
    print("Fetching Indian Indices...")
    nifty_price = 0
    nifty_chg = 0
    nifty_pchg = 0
    vix_price = 0
    vix_chg = 0
    
    # Try NSE
    try:
        q = nse_quote("NIFTY 50")
        if q and 'priceInfo' in q:
            nifty_price = float(str(q["priceInfo"]["lastPrice"]).replace(',', ''))
            nifty_chg = float(str(q["priceInfo"]["change"]).replace(',', ''))
            nifty_pchg = float(str(q["priceInfo"]["pChange"]).replace(',', ''))
    except:
        pass

    # Fallback Nifty
    if nifty_price == 0:
        print("NSE Nifty failed, using YFinance...")
        try:
            t = yf.Ticker("^NSEI")
            hist = t.history(period="2d")
            if len(hist) >= 1:
                nifty_price = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2] if len(hist) > 1 else nifty_price
                nifty_chg = nifty_price - prev
                nifty_pchg = (nifty_chg / prev) * 100
        except Exception as e:
            print(f"YF Nifty failed: {e}")

    # Try VIX NSE
    try:
        q = nse_quote("INDIA VIX")
        if q and 'priceInfo' in q:
            vix_price = float(str(q["priceInfo"]["lastPrice"]).replace(',', ''))
            vix_chg = float(str(q["priceInfo"]["change"]).replace(',', ''))
    except:
        pass
        
    # Fallback VIX
    if vix_price == 0:
        try:
            t = yf.Ticker("^INDIAVIX")
            hist = t.history(period="2d")
            if len(hist) >= 1:
                vix_price = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2] if len(hist) > 1 else vix_price
                vix_chg = vix_price - prev
        except:
            pass

    # Save Nifty
    nifty_text = f"Nifty 50 Current Price: {nifty_price:.2f}\n"
    nifty_text += f"Change: {nifty_chg:+.2f}\n"
    nifty_text += f"Change %: {nifty_pchg:+.2f}%\n"
    save_file('nifty.txt', nifty_text)

    # Save MMI
    mmi_text = f"Current MMI = 50.0\nChange in MMI from 48.0\n"
    mmi_text += f"Change in Nifty = {nifty_chg:+.2f} ({nifty_pchg:+.2f}%)"
    save_file('mmi.txt', mmi_text)

    # Save VIX
    vix_text = f"Current Value: {vix_price:.2f}\n"
    vix_text += f"Change: {vix_chg:+.2f}"
    save_file('vix.txt', vix_text)


def fetch_option_chain():
    """
    Fetches Nifty Option Chain. Tries NSE, fallback YF.
    """
    print("Fetching Nifty Option Chain...")
    oi_text = ""
    
    # Try NSE
    try:
        payload = nse_optionchain_scrapper('NIFTY')
        if payload:
            records = payload.get('records', {})
            underlying_value = records.get('underlyingValue')
            if underlying_value:
                strikes = [d for d in records.get('data', []) if abs(d['strikePrice'] - underlying_value) < 400]
                
                oi_text = f"Nifty Spot Price: {underlying_value}\n\n"
                oi_text += "Strike | CE OI (Change) | PE OI (Change)\n"
                oi_text += "---|---|---\n"
                for item in strikes:
                    strike = item['strikePrice']
                    ce = item.get('CE', {})
                    pe = item.get('PE', {})
                    oi_text += f"{strike} | {ce.get('openInterest',0)} ({ce.get('changeinOpenInterest',0)}) | {pe.get('openInterest',0)} ({pe.get('changeinOpenInterest',0)})\n"
    except:
        pass
        
    # Fallback YF (Partial support)
    if not oi_text:
        print("NSE Option Chain failed, using YFinance...")
        try:
            tk = yf.Ticker("^NSEI")
            # Get nearest expiry
            exps = tk.options
            if exps:
                # Use first expiry
                opt = tk.option_chain(exps[0])
                hist = tk.history(period='1d')
                if not hist.empty:
                    spot = hist['Close'].iloc[-1]
                    
                    # Merge calls and puts
                    calls = opt.calls
                    puts = opt.puts
                    
                    # Filter near ATM
                    calls = calls[(calls['strike'] > spot - 400) & (calls['strike'] < spot + 400)]
                    puts = puts[(puts['strike'] > spot - 400) & (puts['strike'] < spot + 400)]
                    
                    oi_text = f"Nifty Spot Price: {spot:.2f}\n\n"
                    oi_text += "Strike | CE OI (Change) | PE OI (Change)\n"
                    oi_text += "---|---|---\n"
                    
                    all_strikes = sorted(list(set(calls['strike'].tolist() + puts['strike'].tolist())))
                    for s in all_strikes:
                        c_row = calls[calls['strike'] == s]
                        p_row = puts[puts['strike'] == s]
                        
                        c_oi = int(c_row['openInterest'].iloc[0]) if not c_row.empty else 0
                        p_oi = int(p_row['openInterest'].iloc[0]) if not p_row.empty else 0
                        
                        oi_text += f"{s} | {c_oi} (0) | {p_oi} (0)\n"
        except Exception as e:
            print(f"YF Option Chain failed: {e}")

    if oi_text:
        save_file('nifty_oi.txt', oi_text)

def fetch_fii_dii():
    print("Fetching FII/DII Data...")
    try:
        data = nse_fiidii()
         # check if dataframe
        if hasattr(data, 'to_dict'):
             data = data.to_dict('records')
        
        if data and isinstance(data, list) and len(data) > 0:
            latest = data[0]
            date_str = latest.get('date', 'Unknown')
            fii = latest.get('fii_netAmt', '0')
            dii = latest.get('dii_netAmt', '0')
            text = f"{date_str} : FII = {fii} DII = {dii}\n"
            save_file('fii_dii_data.txt', text)
        else:
            print("FII/DII Data empty/failed")
    except Exception as e:
        print(f"Error fetching FII/DII: {e}")

def fetch_global_market_data():
    print("Fetching Global Market Data (Hybrid)...")
    
    # 1. Global Indices (YFinance is better for Indices)
    try:
        indices = {
             "^DJI": "Dow Jones",
             "^IXIC": "Nasdaq",
             "^GSPC": "S&P 500",
             "^FTSE": "FTSE 100"
        }
        global_text = "Name | Close | Change | Change%\n---\n"
        
        for symbol, name in indices.items():
            try:
                t = yf.Ticker(symbol)
                hist = t.history(period="2d")
                if len(hist) >= 1:
                    price = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2] if len(hist) > 1 else price
                    change = price - prev
                    pct = (change / prev) * 100
                    global_text += f"{name} | {price:,.2f} | {change:+,.2f} | {pct:+.2f}%\n"
            except:
                pass
        
        save_file('global_markets.txt', global_text)

    except Exception as e:
        print(f"Error fetching Global Indices: {e}")


# Global variable for conversion
usd_inr_rate = 84.0

def fetch_currency_rates():
    global usd_inr_rate
    print("Fetching Currency Data...")
    # 2. Currency (Hybrid: Twelve Data -> YFinance)
    try:
        curr_text = "Code | Name | Country | Rate\n---\n"
        
        pairs = {
            "USD/INR": ("USD", "US Dollar", "USA", "USDINR=X"),
            "EUR/INR": ("EUR", "Euro", "Europe", "EURINR=X"),
            "GBP/INR": ("GBP", "British Pound", "UK", "GBPINR=X"),
            "JPY/INR": ("JPY", "Japanese Yen", "Japan", "JPYINR=X")
        }
        
        has_data = False
        
        # Try Twelve Data first
        if td:
             for pair, info in pairs.items():
                 try:
                     ts = td.time_series(symbol=pair, interval="1day", outputsize=1).as_json()
                     if ts and isinstance(ts, list):
                         p = float(ts[0]['close'])
                         curr_text += f"{info[0]} | {info[1]} | {info[2]} | {p:.2f}\n"
                         has_data = True
                         if pair == "USD/INR": usd_inr_rate = p
                 except: pass

        # Fallback YFinance
        if not has_data:
            print("Twelve Data Currency empty, using YFinance...")
            curr_text = "Code | Name | Country | Rate\n---\n"
            for pair, info in pairs.items():
                 try:
                     yf_sym = info[3]
                     t = yf.Ticker(yf_sym)
                     hist = t.history(period="1d")
                     if not hist.empty:
                         p = hist['Close'].iloc[-1]
                         curr_text += f"{info[0]} | {info[1]} | {info[2]} | {p:.2f}\n"
                         has_data = True
                         if pair == "USD/INR": usd_inr_rate = p
                 except Exception as ex: 
                     print(f"YF {pair} failed: {ex}")
        
        if has_data:
            save_file('currency_rates.txt', curr_text)
        else:
             print("Currency Data Fetch Failed completely.")

    except Exception as e:
        print(f"Error fetching Currency: {e}")

def fetch_commodities():
    # 3. Commodities (Gold/Silver) - YFinance is reliable for Futures
    global usd_inr_rate
    try:
        print("Fetching Commodities (YFinance)...")
        # Gold
        gold = yf.Ticker("GC=F")
        hist_g = gold.history(period="5d")
        
        # Silver
        silver = yf.Ticker("SI=F")
        hist_s = silver.history(period="5d")
        
        if not hist_g.empty:
            latest_g = hist_g['Close'].iloc[-1]
            prev_g = hist_g['Close'].iloc[-2]
            
            # USD/oz -> INR/10g
            def to_inr_10g(usd): return (usd * usd_inr_rate / 31.1035) * 10
            
            p_24k = to_inr_10g(latest_g)
            chg = to_inr_10g(latest_g - prev_g)
            arrow = "▲" if chg >= 0 else "▼"
            
            gold_text = f"24K Gold: : ₹ {p_24k:,.2f} (Change: ₹ {abs(chg):,.2f} {arrow})\n"
            gold_text += f"22K Gold: : ₹ {p_24k*0.916:,.2f} (Change: ₹ {abs(chg*0.916):,.2f} {arrow})\n\n"
            gold_text += "Date | 24K Price | 22K Price\n---------------------------\n"
            
            for date, row in hist_g.tail(5).iterrows():
                dt = date.strftime('%Y-%m-%d')
                val = to_inr_10g(row['Close'])
                diff = to_inr_10g(row['Close'] - row['Open'])
                gold_text += f"{dt} | ₹ {val:,.0f} ({int(diff)}) | ₹ {val*0.916:,.0f} ({int(diff*0.916)})\n"
            save_file('gold_rates.txt', gold_text)
            
        if not hist_s.empty:
            latest_s = hist_s['Close'].iloc[-1]
            prev_s = hist_s['Close'].iloc[-2]
            
            # USD/oz -> INR/kg
            def to_inr_kg(usd): return (usd * usd_inr_rate / 31.1035) * 1000
            
            p_kg = to_inr_kg(latest_s)
            chg_s = to_inr_kg(latest_s - prev_s)
            arrow_s = "▲" if chg_s >= 0 else "▼"
            
            silver_text = f"Per Gram: : ₹ {p_kg/1000:,.2f} (Change: ₹ {abs(chg_s/1000):,.2f} {arrow_s})\n"
            silver_text += f"Per Kg: : ₹ {p_kg:,.2f} (Change: ₹ {abs(chg_s):,.2f} {arrow_s})\n\n"
            silver_text += "Date | 1 gram | 100 g | 1 kg\n-------------------------------\n"
            
            for date, row in hist_s.tail(5).iterrows():
                dt = date.strftime('%Y-%m-%d')
                val = to_inr_kg(row['Close'])
                diff = to_inr_kg(row['Close'] - row['Open'])
                silver_text += f"{dt} | ₹ {val/1000:,.0f} ({int(diff/1000)}) | ₹ {val/10:,.0f} | ₹ {val:,.0f}\n"
            save_file('silver_rates.txt', silver_text)

    except Exception as e:
        print(f"Error fetching Commodities: {e}")

def fetch_news():
    if not newsapi: return
    print("Fetching News...")
    try:
        top = newsapi.get_top_headlines(category='business', country='in')
        articles = top.get('articles', [])
        lines = [a['title'] for a in articles if a['title']]
        save_file('market_bulletin.txt', '\n'.join(lines[:15]))
    except Exception as e:
        print(f"Error fetching News: {e}")

def fetch_high_low():
    print("Fetching 52 Week High/Low...")
    
    output = ""
    # Try NSE
    try:
        # NSE URLs
        url_high = "https://www.nseindia.com/api/live-analysis-variations?index=yearHigh"
        url_low = "https://www.nseindia.com/api/live-analysis-variations?index=yearLow"
        
        def get_data(url):
            try:
                res = nsefetch(url)
                if isinstance(res, dict): return res
                return None
            except: return None

        data_high = get_data(url_high)
        data_low = get_data(url_low)
        
        # Process High
        output += "52 Week High\n"
        has_high = False
        if data_high:
            rows = []
            if 'NIFTY 50' in data_high and isinstance(data_high['NIFTY 50'], dict):
                 rows = data_high['NIFTY 50'].get('data', [])
            elif 'data' in data_high:
                 rows = data_high['data']
            
            if isinstance(rows, list):
                for r in rows[:7]:
                    if isinstance(r, dict):
                         s = r.get('symbol', 'UNK')
                         p = r.get('ltp', 0)
                         c = r.get('change', 0)
                         v = r.get('value', 0)
                         output += f"{s} - {p} - {c} - {v}\n"
                         has_high = True
        
        if not has_high: raise Exception("NSE High empty")

        # Process Low
        output += "\n52 Week Low\n"
        has_low = False
        if data_low:
             rows = []
             if 'NIFTY 50' in data_low and isinstance(data_low['NIFTY 50'], dict):
                  rows = data_low['NIFTY 50'].get('data', [])
             elif 'data' in data_low:
                  rows = data_low['data']
             
             if isinstance(rows, list):
                 for r in rows[:7]:
                     if isinstance(r, dict):
                         s = r.get('symbol', 'UNK')
                         p = r.get('ltp', 0)
                         c = r.get('change', 0)
                         v = r.get('value', 0)
                         output += f"{s} - {p} - {c} - {v}\n"
                         has_low = True
        
        if not has_low: raise Exception("NSE Low empty")
        
        save_file('highlow.txt', output)
        return # Success

    except Exception as e:
        print(f"NSE High/Low failed ({e}), trying YF Fallback (scanning Nifty 50)...")

    # Fallback YF
    try:
        # We will scan top 10 Nifty stocks or a manual list to check 52w high
        # Scanning 50 stocks takes time, let's do top 15 weights
        tickers = [
            "RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "ITC.NS", "TCS.NS",
            "LICI.NS", "BHARTIARTL.NS", "SBIN.NS", "HINDUNILVR.NS", "LT.NS", "BAJFINANCE.NS",
            "MARUTI.NS", "AXISBANK.NS", "SUNPHARMA.NS"
        ]
        
        highs = []
        lows = []
        
        for t in tickers:
            try:
                tk = yf.Ticker(t)
                info = tk.info
                current = info.get('currentPrice', 0)
                h52 = info.get('fiftyTwoWeekHigh', 0)
                l52 = info.get('fiftyTwoWeekLow', 0)
                
                # Check within 2% of high
                if h52 > 0 and current >= h52 * 0.98:
                    highs.append( (t.replace('.NS',''), current) )
                
                # Check within 2% of low
                if l52 > 0 and current <= l52 * 1.02:
                    lows.append( (t.replace('.NS',''), current) )
            except: pass
            
        output = "52 Week High\n"
        for h in highs:
            output += f"{h[0]} - {h[1]} - 0 - 0\n"
            
        output += "\n52 Week Low\n"
        for l in lows:
            output += f"{l[0]} - {l[1]} - 0 - 0\n"
            
        if not highs and not lows:
             output += "None - 0 - 0 - 0\n"
             
        save_file('highlow.txt', output)
        
    except Exception as ex:
        print(f"YF High/Low failed: {ex}")

def main():
    print("Starting Hybrid Data Fetch (v2)...")
    fetch_indian_indices()
    fetch_high_low()
    fetch_option_chain()
    fetch_fii_dii()
    fetch_global_market_data()
    fetch_currency_rates()
    fetch_commodities()


def fetch_pcr():
    print("Fetching PCR Data (from nifty_oi.txt)...")
    try:
        pcr = 0.0
        total_pe_oi = 0
        total_ce_oi = 0
        
        # Reuse data from nifty_oi.txt if available
        if os.path.exists(os.path.join(DATA_DIR, 'nifty_oi.txt')):
            with open(os.path.join(DATA_DIR, 'nifty_oi.txt'), 'r') as f:
                content = f.read()
                
            # Parse "Total Call OI:   1,888.02 L"
            # We need to handle the "L" (Lakhs) and commas.
            import re
            ce_match = re.search(r"Total Call OI:\s*([\d,.]+)", content)
            pe_match = re.search(r"Total Put OI:\s*([\d,.]+)", content)
            
            if ce_match and pe_match:
                ce_val = float(ce_match.group(1).replace(',', ''))
                pe_val = float(pe_match.group(1).replace(',', ''))
                
                if ce_val > 0:
                    pcr = pe_val / ce_val
                    total_ce_oi = ce_val * 100000 # Convert Lakhs to actual if needed, but ratio is same
                    total_pe_oi = pe_val * 100000
        
        # --- NEW: Calculate Change from previous file ---
        prev_pcr = pcr # Default if no previous file
        pcr_change = 0.0
        pcr_change_percent = 0.0
        
        pcr_file_path = os.path.join(DATA_DIR, 'pcr.txt')
        if os.path.exists(pcr_file_path):
            try:
                with open(pcr_file_path, 'r') as f:
                    old_content = f.read()
                    # Extract "Current PCR: 0.74"
                    match = re.search(r"Current PCR:\s*([\d.]+)", old_content)
                    if match:
                        prev_pcr = float(match.group(1))
                        if prev_pcr > 0:
                            pcr_change = pcr - prev_pcr
                            pcr_change_percent = (pcr_change / prev_pcr) * 100
                            print(f"Previous PCR: {prev_pcr}, New PCR: {pcr:.4f}, Change: {pcr_change:+.4f} ({pcr_change_percent:+.2f}%)")
            except Exception as e:
                print(f"Warning reading previous PCR: {e}")

        # Format:
        # Current PCR: 0.74
        # Change: +0.13
        # Change %: +19.2%
        # Total Put OI: 140197000
        # Total Call OI: 188802000
        text = f"Current PCR: {pcr:.4f}\n"
        text += f"Change: {pcr_change:+.4f}\n"
        text += f"Change %: {pcr_change_percent:+.2f}%\n"
        text += f"Total Put OI: {int(total_pe_oi)}\n"
        text += f"Total Call OI: {int(total_ce_oi)}\n"
        
        save_file('pcr.txt', text)
        print(f"Saved PCR: {pcr:.4f}")
        
    except Exception as e:
        print(f"Error fetching PCR: {e}")

def fetch_nifty_movers():
    print("Fetching Nifty Movers (YFinance Scan)...")
    try:
        # Top weights in Nifty 50 to scan (approx list for speed)
        tickers = [
            "RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "ITC.NS", "TCS.NS", 
            "LICI.NS", "BHARTIARTL.NS", "SBIN.NS", "HINDUNILVR.NS", "LT.NS", "BAJFINANCE.NS",
            "MARUTI.NS", "AXISBANK.NS", "SUNPHARMA.NS", "TITAN.NS", 
            "ULTRACEMCO.NS", "ASIANPAINT.NS", "NTPC.NS", "M&M.NS", "HCLTECH.NS", "KOTAKBANK.NS",
            "POWERGRID.NS", "ONGC.NS", "ADANIENT.NS", "TATASTEEL.NS", "COALINDIA.NS", "WIPRO.NS"
        ]
        
        data = []
        for t in tickers:
            try:
                tk = yf.Ticker(t)
                hist = tk.history(period="2d")
                if len(hist) >= 1:
                    price = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2] if len(hist) > 1 else price
                    change = price - prev
                    pct = (change/prev) * 100
                    name = t.replace('.NS', '')
                    data.append({ 'name': name, 'value': price, 'change': f"{change:+.2f}", 'pct': pct })
            except: pass
            
        # Sort by pct gain
        data.sort(key=lambda x: x['pct'], reverse=True)
        top_gainers = data[:5]
        top_losers = data[-5:]
        top_losers.reverse() 
        
        output = "Top 5 Gainers:\n====\nName Value Change\n----\n"
        for d in top_gainers:
            output += f"{d['name']} {d['value']:.2f} {d['pct']:.2f}%\n"
            
        output += "\nTop 5 Losers:\n====\nName Value Change\n----\n"
        for d in top_losers:
            output += f"{d['name']} {d['value']:.2f} {d['pct']:.2f}%\n"
            
        save_file('nifty50_movers.txt', output)

    except Exception as e:
        print(f"Error fetching Nifty Movers: {e}")

def fetch_key_stocks():
    print("Fetching Key Stocks...")
    try:
        # Removed TATAMOTORS.NS and ZOMATO.NS due to persisting 404 errors
        stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", 
                  "SBIN.NS", "ADANIENT.NS", "MRF.NS", "LICI.NS"]
        
        output = ""
        for s in stocks:
            try:
                tk = yf.Ticker(s)
                hist = tk.history(period="2d")
                if len(hist) >= 1:
                    price = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2] if len(hist) > 1 else price
                    chg = price - prev
                    pct = (chg/prev)*100
                    name = s.replace('.NS', '')
                    output += f"{name} ({pct:+.2f}%)\n"
            except: pass
            
        save_file('key_stocks_to_watch.txt', output)
        
    except Exception as e:
        print(f"Error fetching Key Stocks: {e}")

def fetch_nifty_analysis():
    print("Generating Nifty Tech Analysis...")
    try:
        tk = yf.Ticker("^NSEI")
        hist = tk.history(period="5d")
        if not hist.empty:
            last = hist.iloc[-1]
            high = last['High']
            low = last['Low']
            close = last['Close']
            
            pivot = (high + low + close) / 3
            r1 = (2 * pivot) - low
            s1 = (2 * pivot) - high
            r2 = pivot + (high - low)
            s2 = pivot - (high - low)
            
            ma20 = hist['Close'].mean()
            trend = "Bullish" if close > ma20 else "Bearish"
            
            text = f"Resistance 1: {r1:.2f}\n"
            text += f"Resistance 2: {r2:.2f}\n"
            text += f"Support 1: {s1:.2f}\n"
            text += f"Support 2: {s2:.2f}\n"
            text += f"Trend: {trend}\n"
            
            save_file('nifty_analysis.txt', text)
            
    except Exception as e:
        print(f"Error generating Tech Analysis: {e}")

def fetch_nifty_dashboard_data():
    pass

def main():
    print("Starting Hybrid Data Fetch (v2)...")
    fetch_indian_indices()
    fetch_high_low()
    fetch_option_chain()
    fetch_fii_dii()
    fetch_global_market_data()
    fetch_currency_rates()
    fetch_commodities()
    fetch_news()
    
    # New additions
    fetch_pcr()
    fetch_nifty_movers()
    fetch_key_stocks()
    fetch_nifty_analysis()
    
    print("Done. Check public/Data/ for output.")

if __name__ == "__main__":
    main()
