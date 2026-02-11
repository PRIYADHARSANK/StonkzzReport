from fetch_data_v3 import fetch_gift_nifty, fetch_fiidii
import logging

# Configure logging to stdout
logging.basicConfig(level=logging.INFO)

print("--- Testing Refactored GIFT Nifty Fetch ---")
try:
    fetch_gift_nifty()
except Exception as e:
    print(f"CRITICAL ERROR in GIFT Nifty: {e}")

print("\n--- Testing Refactored FII/DII Fetch ---")
try:
    fetch_fiidii()
except Exception as e:
    print(f"CRITICAL ERROR in FII/DII: {e}")
