
from nsepython import *
import json

print("Checking High/Low functions...")
try:
    # Most libraries have a specific getter for "52 week high/low"
    # or "live market"
    # nse_live_market_data("limit=10")?
    
    # Try fetching Nifty 50 heat map or similar which contains 52w info
    q = nse_quote("NIFTY 50")
    # This is just index data.
    
    # We need the list of stocks near 52w high.
    # On NSE website it's under 'live-analysis'
    # nsepython might not have a direct mapped function for the "View All" page.
    # But usually nsepython.nse_live_market_data() works.
    pass
except Exception as e:
    print(e)
    
# Let's try to see if we can iterate Nifty 50 constituents and check their 52w status?
# That's too slow (50 requests).
# Better to find a bulk endpoint.
