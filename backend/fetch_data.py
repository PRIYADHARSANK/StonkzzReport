import yfinance as yf
import os

# Define the target directory
DATA_DIR = os.path.join(os.getcwd(), 'public', 'Data')
os.makedirs(DATA_DIR, exist_ok=True)

def fetch_and_save_data():
    print("Fetching market data...")

    # --- 1. Nifty 50 ---
    try:
        nifty = yf.Ticker("^NSEI")
        hist = nifty.history(period="2d")
        if len(hist) >= 2:
            current_close = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2]
            change = current_close - prev_close
            pct_change = (change / prev_close) * 100
            
            nifty_text = f"Nifty 50 Current Price: {current_close:.2f}\n"
            nifty_text += f"Change: {change:+.2f}\n"
            nifty_text += f"Change %: {pct_change:+.2f}%\n"
            
            with open(os.path.join(DATA_DIR, 'nifty.txt'), 'w') as f:
                f.write(nifty_text)
            
            mmi_text = f"Current MMI = 50.0\nChange in MMI from 48.0\n"
            mmi_text += f"Change in Nifty = {change:+.2f} ({pct_change:+.2f}%)"
            with open(os.path.join(DATA_DIR, 'mmi.txt'), 'w') as f:
                f.write(mmi_text)
                
            print(f"Saved Nifty data: {current_close:.2f}")
        else:
             print("Insufficient Nifty data")
    except Exception as e:
        print(f"Error fetching Nifty: {e}")

    # --- 2. India VIX ---
    try:
        vix = yf.Ticker("^INDIAVIX")
        hist = vix.history(period="2d")
        if len(hist) >= 1:
            current_vix = hist['Close'].iloc[-1]
            prev_vix = hist['Close'].iloc[-2] if len(hist) > 1 else current_vix
            change = current_vix - prev_vix
            
            vix_text = f"Current Value: {current_vix:.2f}\n"
            vix_text += f"Change: {change:+.2f}"
            
            with open(os.path.join(DATA_DIR, 'vix.txt'), 'w') as f:
                f.write(vix_text)
            print(f"Saved VIX data: {current_vix:.2f}")
    except Exception as e:
        print(f"Error fetching VIX: {e}")

    # --- 3. Gold Rates ---
    try:
        # Using generic numbers for 24K and 22K based on Gold Futures (GC=F) approx conversion to INR 10g
        # Gold Futures is USD/oz. Approx conv: Price * 83 (USDINR) / 31.1 (oz to g) * 10 (10g)
        gold = yf.Ticker("GC=F") 
        hist = gold.history(period="5d") # Fetch more for history
        
        if len(hist) >= 2:
            price_usd = hist['Close'].iloc[-1]
            prev_usd = hist['Close'].iloc[-2]
            change_usd = price_usd - prev_usd
            
            # Approx INR conversion factors
            usd_inr = 84.0 # Fixed approx
            oz_to_10g = 10 / 31.1035
            
            price_inr_24k = price_usd * usd_inr * oz_to_10g
            change_inr = change_usd * usd_inr * oz_to_10g
            price_inr_22k = price_inr_24k * 0.92
            
            arrow = "▲" if change_inr >= 0 else "▼"
            
            # Format required by goldService.ts regex: /:\s*₹\s*([\d,.]+)\s*\(Change:\s*₹\s*([+\-\d,.]+)\s*(▲|▼)\)/
            # Header: 24K Gold:
            gold_text = f"24K Gold: : ₹ {price_inr_24k:,.2f} (Change: ₹ {abs(change_inr):,.2f} {arrow})\n"
            gold_text += f"22K Gold: : ₹ {price_inr_22k:,.2f} (Change: ₹ {abs(change_inr * 0.92):,.2f} {arrow})\n"
            gold_text += "\nDate | 24K Price | 22K Price\n"
            gold_text += "---------------------------\n"
            
            # History
            # regex: /₹\s*([\d,]+)/ and /\(([-]?\d+)\)/
            for date, row in hist.tail(5).iterrows():
                p = row['Close'] * usd_inr * oz_to_10g
                open_p = row['Open'] * usd_inr * oz_to_10g # roughly
                chg = p - open_p
                
                date_str = date.strftime('%Y-%m-%d')
                gold_text += f"{date_str} | ₹ {p:,.0f} ({int(chg)}) | ₹ {p*0.92:,.0f} ({int(chg*0.92)})\n"

            with open(os.path.join(DATA_DIR, 'gold_rates.txt'), 'w') as f:
                f.write(gold_text)
            print("Saved Gold data")
    except Exception as e:
        print(f"Error fetching Gold: {e}")

    # --- 4. Silver Rates ---
    try:
        silver = yf.Ticker("SI=F")
        hist = silver.history(period="5d")
        
        if len(hist) >= 2:
            price_usd = hist['Close'].iloc[-1]
            prev_usd = hist['Close'].iloc[-2]
            change_usd = price_usd - prev_usd
            
            # Silver Futures USD/oz -> INR/kg vs INR/g
            usd_inr = 84.0
            price_inr_kg = price_usd * usd_inr / 31.1035 * 1000
            change_inr_kg = change_usd * usd_inr / 31.1035 * 1000
            price_inr_g = price_inr_kg / 1000
            change_inr_g = change_inr_kg / 1000

            arrow = "▲" if change_inr_kg >= 0 else "▼"
            
            # Format: Per Gram: : ₹ ... | Per Kg: : ₹ ...
            silver_text = f"Per Gram: : ₹ {price_inr_g:,.2f} (Change: ₹ {abs(change_inr_g):,.2f} {arrow})\n"
            silver_text += f"Per Kg: : ₹ {price_inr_kg:,.2f} (Change: ₹ {abs(change_inr_kg):,.2f} {arrow})\n"
            silver_text += "\nDate | 1 gram | 100 g | 1 kg\n"
            silver_text += "-------------------------------\n"
            
            for date, row in hist.tail(5).iterrows():
                p_kg = row['Close'] * usd_inr / 31.1035 * 1000
                p_open = row['Open'] * usd_inr / 31.1035 * 1000
                chg_kg = p_kg - p_open
                
                date_str = date.strftime('%Y-%m-%d')
                # Format: date | price1g (chg) | price100g | price1kg
                silver_text += f"{date_str} | ₹ {p_kg/1000:,.0f} ({int(chg_kg/1000)}) | ₹ {p_kg/10:,.0f} | ₹ {p_kg:,.0f}\n"
            
            with open(os.path.join(DATA_DIR, 'silver_rates.txt'), 'w') as f:
                f.write(silver_text)
            print("Saved Silver data")
    except Exception as e:
        print(f"Error fetching Silver: {e}")

    # --- 5. Currency (USD/INR and others) ---
    try:
        # currencyService.ts expects: Code | Name | Country | Rate
        # We will fetch a few key pairs.
        # YFinance symbols: INR=X (USD), EURINR=X, GBPINR=X, JPYINR=X, AEDINR=X
        currencies = {
            "INR=X": ("USD", "US Dollar", "USA"),
            "EURINR=X": ("EUR", "Euro", "Europe"),
            "GBPINR=X": ("GBP", "British Pound", "UK"),
            "JPYINR=X": ("JPY", "Japanese Yen", "Japan"),
            "AEDINR=X": ("AED", "UAE Dirham", "UAE")
        }
        
        curr_text = "Code | Name | Country | Rate\n"
        curr_text += "---\n"
        
        for ticker, info in currencies.items():
            try:
                t = yf.Ticker(ticker)
                hist = t.history(period="2d")
                if len(hist) >= 1:
                    price = hist['Close'].iloc[-1]
                    # Service only seems to read 'Rate' (value). 'Change' isn't explicitly in the 4 columns it parses?
                    # The parser reads: code, name, countryName, value (parts[3]).
                    # parts[3] is cleaned of non-numeric. 
                    # Let's provide the price.
                    
                    code, name, country = info
                    curr_text += f"{code} | {name} | {country} | {price:.2f}\n"
            except Exception as ex:
                print(f"Failed to fetch {ticker}: {ex}")
            
        with open(os.path.join(DATA_DIR, 'currency_rates.txt'), 'w') as f:
            f.write(curr_text)
            
        print(f"Saved Currency data")
    except Exception as e:
        print(f"Error fetching Currency: {e}")
        
    # --- 6. Global Markets ---
    try:
        tickers = {
            "^DJI": "Dow Jones",
            "^GSPC": "S&P 500",
            "^IXIC": "Nasdaq",
            "^FTSE": "FTSE 100",
            "^N225": "Nikkei 225" # Nikkei might not map to a flag in service but good to have
        }
        
        # Format required by globalIndicesService.ts:
        # Header: Name | LTP | Change | Change%
        # Separator: --- optional but good
        global_text = "Name | LTP | Change | Change%\n"
        global_text += "---\n"
        
        for ticker, name in tickers.items():
            t = yf.Ticker(ticker)
            hist = t.history(period="2d")
            if len(hist) >= 1:
                price = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2] if len(hist) > 1 else price
                change = price - prev
                pct = (change/prev) * 100
                
                # Format: Name | LTP | Change | Change%
                global_text += f"{name} | {price:.2f} | {change:+.2f} | {pct:+.2f}%\n"
        
        with open(os.path.join(DATA_DIR, 'global_markets.txt'), 'w') as f:
            f.write(global_text)
        print("Saved Global Markets")
            
    except Exception as e:
        print(f"Error fetching Global Markets: {e}")

if __name__ == "__main__":
    fetch_and_save_data()
