import yfinance as yf
import requests

def test_yf_options():
    print("Testing YFinance Options...")
    
    # Use default session (yfinance handles this better now)
    # session = requests.Session()
    
    # Try RELIANCE first (Stock Option)
    try:
        print("\n1. Fetching RELIANCE options...")
        reliance = yf.Ticker("RELIANCE.NS")
        exps = reliance.options
        print(f"RELIANCE Expiries: {exps}")
        if exps:
            chain = reliance.option_chain(exps[0])
            print(f"RELIANCE Chain Data Head:\n{chain.calls.head()}")
    except Exception as e:
        print(f"RELIANCE Failed: {e}")
        
    # Try NIFTY (Index Option) - Symbol might be ^NSEI or NIFTY.NS?? 
    # Usually ^NSEI for Nifty 50 index
    try:
        print("\n2. Fetching ^NSEI (Nifty 50) options...")
        nifty = yf.Ticker("^NSEI")
        exps = nifty.options
        print(f"NIFTY Expiries: {exps}")
        if exps:
            chain = nifty.option_chain(exps[0])
            print(f"NIFTY Chain Data Head:\n{chain.calls.head()}")
    except Exception as e:
        print(f"NIFTY Failed: {e}")

if __name__ == "__main__":
    test_yf_options()
