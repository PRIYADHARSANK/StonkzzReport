import yfinance as yf
import pandas as pd

def test_yf_options():
    print("Testing YFinance Option Chain for ^NSEI...")
    try:
        nifty = yf.Ticker("^NSEI")
        expirations = nifty.options
        print(f"Expirations: {expirations}")
        
        if not expirations:
            print("No expirations found via YF.")
            return

        nearest = expirations[0]
        print(f"Fetching chain for {nearest}...")
        
        chain = nifty.option_chain(nearest)
        print("Calls head:")
        print(chain.calls.head())
        print("\nPuts head:")
        print(chain.puts.head())
        
        print("\nSuccess! YFinance Option Chain works.")
    except Exception as e:
        print(f"YFinance Error: {e}")

if __name__ == "__main__":
    test_yf_options()
