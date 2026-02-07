
import os
import re

DATA_DIR = os.path.join(os.getcwd(), 'public', 'Data')

def validate_silver():
    print("Validating Silver Check...")
    try:
        with open(os.path.join(DATA_DIR, 'silver_rates.txt'), 'r') as f:
            lines = f.readlines()
        
        # Regex from silverService.ts: /Date\s*\|\s*1 gram/
        # History line expected: Date | 1 gram | 100 g | 1 kg
        # Value format expected: ₹ 249.4 (-6.2)
        
        history_start = -1
        for i, line in enumerate(lines):
            if "Date | 1 gram" in line:
                history_start = i
                break
        
        if history_start == -1:
            print("❌ Silver: History Header NOT found.")
            return False
            
        # Check first data line
        if len(lines) > history_start + 2:
            sample = lines[history_start + 2].strip()
            # Expect: 2026-01-08 | ₹ 249.4 (-6.2) | ...
            # Regex to match the price+change format
            match = re.search(r"₹\s*[\d,.]+\s*\([+\-\d.]+\)", sample)
            if match:
                print(f"✅ Silver: History line valid ('{match.group(0)}')")
                return True
            else:
                print(f"❌ Silver: History line INVALID. Found: '{sample}'")
                print("   Expected format like: '₹ 249.4 (-6.2)'")
                return False
    except Exception as e:
        print(f"❌ Silver: File not found or error ({e})")
        return False

def validate_fiidii():
    print("Validating FII/DII...")
    try:
        with open(os.path.join(DATA_DIR, 'fii_dii_data.txt'), 'r') as f:
            content = f.read().strip()
            
        # Regex from fiiDiiService: (.+?)\s*:\s*FII\s*=\s*([-\d,.]+)\s*DII\s*=\s*([-\d,.]+)
        # It strictly DOES NOT allow '+' symbol.
        match = re.search(r"(.+?)\s*:\s*FII\s*=\s*([-\d,.]+)\s*DII\s*=\s*([-\d,.]+)", content)
        if match:
            print(f"✅ FII/DII: Valid format detected. (FII={match.group(2)}, DII={match.group(3)})")
            return True
        else:
            print(f"❌ FII/DII: Regex mismatch. Content: '{content}'")
            return False
            
    except Exception as e:
        print(f"❌ FII/DII: Error ({e})")
        return False

def validate_pcr():
    print("Validating PCR...")
    try:
        with open(os.path.join(DATA_DIR, 'pcr.txt'), 'r') as f:
            content = f.read()
        
        if "Current PCR:" in content and "0.00" not in content:
            print("✅ PCR: Data verified non-zero.")
            return True
        elif "0.00" in content:
             print("⚠️ PCR: Warning - Value is 0.00")
             return True # Not strictly a format error, just bad data
        else:
             print("❌ PCR: Missing labels.")
             return False
    except: return False

if __name__ == "__main__":
    print("--- VALIDATING DATA INTEGRITY ---")
    s = validate_silver()
    f = validate_fiidii()
    p = validate_pcr()
    
    if s and f and p:
        print("\n🎉 ALL CHECKS PASSED. The Frontend SHOULD accept this data.")
    else:
        print("\n⛔ CHECKS FAILED. Do not restart server yet.")
