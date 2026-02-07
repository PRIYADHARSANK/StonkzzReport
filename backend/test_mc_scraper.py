from bs4 import BeautifulSoup
import re

def test_scraper():
    print("Loading mc_options.html...")
    with open("mc_options.html", "r") as f:
        html = f.read()
        
    soup = BeautifulSoup(html, 'html.parser')
    
    # Inspect all tables
    tables = soup.find_all('table')
    print(f"Total tables: {len(tables)}")
    
    # Focus on the Option Chain Table
    table = soup.find('table', {'class': 'tblopt'})
    if not table:
        print("FAIL: tblopt not found")
        return
        
    print("SUCCESS: Target table found.")
    
    rows = table.find_all('tr')
    print(f"Total Rows: {len(rows)}")
    
    # Print header structure
    headers = [th.get_text(strip=True) for th in table.find_all('th')]
    print(f"All Headers: {headers}")
    
    # Print first few data rows
    for i, row in enumerate(rows[:5]):
        cols = row.find_all('td')
        texts = [c.get_text(strip=True) for c in cols]
        print(f"Row {i}: len={len(cols)} | {texts}")

if __name__ == "__main__":
    test_scraper()
