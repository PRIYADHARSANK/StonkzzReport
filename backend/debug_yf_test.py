import yfinance as yf
import pandas as pd

def test_yfinance():
    print("\n--- Testing GIFT Nifty Proxy (SGX Nifty / NSE IX) ---")
    # GIFT Nifty symbols on YF? 
    # Usually ^NSEI is Nifty 50. 
    # GIFT Nifty might be "GIFTMNI.NS" (unlikely) or just future from somewhere else?
    # Let's try to find a proxy or just use Nifty 50 Futures if available?
    # Actually, GIFT Nifty on YF is often tracked via "NIFTY_F" or similar? No.
    # Let's check "^NSEI" (Nifty 50) and see if we can get futures?
    
    symbols = ["^NSEI", "NIFTY_F", "SGXNIFTY", "IN=F"]
    for s in symbols:
        try:
            print(f"Checking {s}...")
            ticker = yf.Ticker(s)
            hist = ticker.history(period="1d")
            if not hist.empty:
                print(f"  SUCCESS: {s} Last Price: {hist['Close'].iloc[-1]}")
            else:
                print(f"  Empty history for {s}")
        except Exception as e:
            print(f"  Error for {s}: {e}")

    print("\n--- Testing FII/DII Data ---")
    # YF doesn't have FII/DII.
    # We might need to use `nsepython` library if installed, or direct NSE API which we have code for.
    try:
        from nsepython import nse_fno, nse_fiidii
        print("Attempting nsepython.nse_fiidii()...")
        print(nse_fiidii())
    except ImportError:
        print("nsepython not installed/importable")
    except Exception as e:
        print(f"nsepython error: {e}")

if __name__ == "__main__":
    test_yfinance()
