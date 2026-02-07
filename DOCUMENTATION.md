# 📊 StonkzzReport - Complete Technical Documentation

---

## 🎯 Introduction

**StonkzzReport** is a comprehensive market report generation system designed to automatically fetch, analyze, and visualize Indian stock market data. The application creates beautiful, multi-page market reports with real-time data from various financial sources.

### What Does It Do?

StonkzzReport aggregates data from multiple financial platforms and generates:
- **11-page professional market reports**
- **Real-time NIFTY 50 data and analysis**
- **Options chain visualization with PCR analysis**
- **FII/DII activity tracking**
- **Commodity prices (Gold/Silver)**
- **Global market indices and currency rates**
- **AI-powered market sentiment analysis**

### Key Features

| Feature | Description |
|---------|-------------|
| 📈 **Live Data Fetching** | Real-time data from Yahoo Finance, NSE, MoneyControl, Groww |
| 🤖 **AI Analysis** | GROQ-powered market sentiment analysis using LLaMA 3.3 |
| 📷 **High-Quality Export** | PNG screenshots, PDF generation, ZIP packaging |
| 🎨 **Modern UI** | React 19 with Tailwind CSS, responsive design |
| 🔄 **Multi-Source Fallback** | Automatic failover between data sources |
| 📊 **Options Analysis** | PCR calculation, support/resistance levels |

---

## 🏗️ Architecture Overview

```
StonkzzReport/
├── backend/                    # Python data fetching layer
│   ├── fetch_data_v3.py       # Main data orchestrator (2100+ lines)
│   ├── anti_gravity_vix.py    # Multi-source VIX fetcher
│   ├── scripts/               # Utility modules
│   │   ├── robust_stock_fetcher.py
│   │   └── market_utils.py
│   └── .env                   # API keys configuration
├── frontend/                   # React TypeScript application
│   ├── App.tsx                # Main application component
│   ├── components/            # React UI components (9 files)
│   │   ├── Report.tsx         # Multi-page report renderer
│   │   ├── NiftyDashboard.tsx # NIFTY data display
│   │   ├── MMIGauge.tsx       # Market Mood Index gauge
│   │   ├── OpenInterestChart.tsx
│   │   ├── FiiDiiActivity.tsx # FII/DII charts
│   │   ├── VixTrendChart.tsx  # VIX trend visualization
│   │   └── ...
│   ├── services/              # Data processing services (20 files)
│   │   ├── mmiService.ts      # MMI AI analysis
│   │   ├── niftyOiService.ts  # Options chain processing
│   │   ├── vixService.ts      # VIX data parsing
│   │   └── ...
│   └── public/Data/           # Generated data files
└── run_report.sh              # Main execution script
```

---

## 🛠️ Technology Stack

### Backend (Python)

| Package | Version | Purpose |
|---------|---------|---------|
| `yfinance` | 1.0 | Yahoo Finance API for stock/index data |
| `beautifulsoup4` | 4.14.3 | Web scraping for MoneyControl, Groww |
| `requests` | 2.32.5 | HTTP client for API calls |
| `pandas` | 2.3.3 | Data manipulation and analysis |
| `numpy` | 2.4.1 | Numerical computations |
| `python-dotenv` | 1.2.1 | Environment variable management |
| `twelvedata` | 1.2.25 | Twelve Data API client |
| `newsapi-python` | 0.2.7 | News API client |
| `nsepython` | 2.97 | NSE India data fetching |
| `lxml` | 6.0.2 | Fast XML/HTML parsing |

### Frontend (React TypeScript)

| Package | Version | Purpose |
|---------|---------|---------|
| `react` | 19.1.0 | UI framework |
| `vite` | 6.2.0 | Build tool and dev server |
| `typescript` | 5.8.2 | Type-safe JavaScript |
| `recharts` | 3.1.0 | Charting library |
| `groq-sdk` | 0.37.0 | GROQ AI API client |
| `jspdf` | 3.0.1 | PDF generation |
| `html-to-image` | 1.11.11 | Screenshot capture |
| `jszip` | 3.10.1 | ZIP file creation |
| `lucide-react` | 0.525.0 | Icon library |

---

## 🔑 API Keys Analysis

The application uses **3 external APIs** configured in `backend/.env`:

### 1. GROQ API (`GROQ_API_KEY`)

**Purpose:** AI-powered market analysis using LLaMA 3.3-70B model

**Used In:** `frontend/services/mmiService.ts`

**Functionality:**
- Generates Market Mood Index (MMI) analysis
- Creates sentiment interpretation (Fear/Greed zones)
- Compares MMI changes with NIFTY performance
- Identifies divergences between sentiment and price action

**How It Works:**
```typescript
// mmiService.ts
const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });
const completion = await groq.chat.completions.create({
    model: "llama-3.3-70b-versatile",
    messages: [{ role: "user", content: prompt }],
    temperature: 0.3,
    response_format: { type: "json_object" }
});
```

**Rate Limits:** Has fallback logic if rate-limited

---

### 2. Twelve Data API (`TWELVE_DATA_KEY`)

**Purpose:** Financial market data provider

**Potential Uses:**
- Real-time stock quotes
- Historical price data
- Technical indicators
- Currency exchange rates

> **Note:** Currently configured but primary data comes from Yahoo Finance

---

### 3. News API (`NEWS_API_KEY`)

**Purpose:** Market news and headlines

**Potential Uses:**
- Market bulletin generation
- News sentiment analysis
- Breaking news alerts

> **Note:** Available for market bulletin feature enhancement

---

## ⚙️ Core Functionalities

### 1. Data Fetching Layer (`fetch_data_v3.py`)

The main orchestrator that fetches all market data:

#### Nifty 50 Data
```python
def fetch_indices():
    # Fetches NIFTY 50 using yfinance (^NSEI)
    # Calculates: Close, Open, High, Low, Change, 52W Range
    # Volume aggregation from constituents if index volume is 0
```

**Data Sources:** Yahoo Finance (`^NSEI`)

**Output File:** `nifty.txt`

---

#### VIX Data (Anti-Gravity System)

The VIX fetcher (`anti_gravity_vix.py`) is a sophisticated multi-source system:

```
┌─────────────────────────────────────────────────────┐
│                 VIX FETCH CHAIN                     │
├─────────────────────────────────────────────────────┤
│  1. Yahoo Finance (^INDIAVIX) - Primary            │
│          ↓ (if fails)                              │
│  2. NSE Official API - Secondary                   │
│          ↓ (if fails)                              │
│  3. Groww Scraping - Tertiary                      │
│          ↓ (if fails)                              │
│  4. MoneyControl Scraping - Last Resort            │
├─────────────────────────────────────────────────────┤
│  Cross-Validation: Compares values from sources    │
│  Staleness Check: Rejects data older than 30 mins  │
│  Anomaly Detection: VIX range 8.0 - 40.0          │
└─────────────────────────────────────────────────────┘
```

**Key Features:**
- `max_age_minutes`: Maximum data age tolerance
- `tolerance_percent`: Cross-validation variance threshold
- Weekend handling: Allows 72-hour old data on Mondays

**Output File:** `vix.txt`

---

#### Options Chain Analysis (`NSEOptionChainFetcher`)

Multi-source fetcher for NIFTY option chain:

| Source | Priority | Method |
|--------|----------|--------|
| NSE Direct API | 1 | `_fetch_from_nse()` |
| Groww | 2 | `_fetch_from_groww()` |
| MoneyControl | 3 | `_fetch_from_moneycontrol()` |

**Processing (`NiftyOIAnalyzer`):**
- Fetches raw option chain data
- Calculates PCR (Put-Call Ratio): `PCR = Total Put OI / Total Call OI`
- Identifies Max Pain strike
- Determines support/resistance levels
- Stores snapshots in SQLite database

**Output Files:**
- `nifty_oi_analysis.json`
- `nifty_pcr.txt`

---

#### GIFT Nifty Data (`GiftNiftyScraper`)

Scrapes GIFT Nifty futures data from MoneyControl:

```python
class GiftNiftyScraper:
    BASE_URL = "https://www.moneycontrol.com/live-index/gift-nifty"
    
    def _extract_data_from_soup(self, soup):
        # Method 1: Parse __NEXT_DATA__ JSON (more reliable)
        # Method 2: Fallback to HTML selectors
```

**Data Points:** Last Price, Change, Open, High, Low, 52W Range

**Output File:** `gift_nifty.txt`

---

#### Gold & Silver Prices

Scrapes commodity prices from LiveChennai:

```python
def fetch_gold_silver():
    url = "https://www.livechennai.com/gold_silverrate.asp"
    # Parses: 24K, 22K gold prices
    # Parses: 1g, 100g, 1kg silver prices
    # Includes 10-day price history
```

**Validation:** Checks if price date matches target trading day

**Output Files:**
- `gold_rates.txt`
- `silver_rates.txt`

---

#### FII/DII Activity (`fetch_fiidii()`)

Fetches Foreign and Domestic Institutional Investor data:

```python
def fetch_fiidii():
    # Scrapes MoneyControl FII/DII page
    # Fetches current + previous month for 45-day coverage
    # Returns: Date, FII Buy/Sell/Net, DII Buy/Sell/Net
```

**Data Source:** MoneyControl FII/DII activity page

**Output File:** `fii_dii.txt`

---

#### Global Markets & Currency

```python
def fetch_global():
    # Fetches major global indices using yfinance
    # ^GSPC (S&P 500), ^DJI (Dow Jones), ^IXIC (NASDAQ)
    # ^FTSE, ^N225, ^HSI, ^AXJO

def fetch_currency():
    # Fetches currency rates: USD, GBP, EUR, AED, SGD
    # Uses yfinance currency pairs (USDINR=X, etc.)
```

**Output Files:**
- `global_indices.txt`
- `currencies.txt`

---

### 2. Frontend Services Layer

The frontend has 20 specialized services for data processing:

| Service | Purpose |
|---------|---------|
| `niftyDashboardService.ts` | Parse NIFTY data for dashboard |
| `mmiService.ts` | MMI analysis with GROQ AI |
| `niftyOiService.ts` | Options chain visualization |
| `pcrService.ts` | PCR calculations and analysis |
| `vixService.ts` | VIX data parsing |
| `fiiDiiService.ts` | FII/DII chart data |
| `goldService.ts` | Gold price history |
| `silverService.ts` | Silver price history |
| `globalIndicesService.ts` | Global market data |
| `currencyService.ts` | Currency rate data |
| `heatmapService.ts` | Market heatmap generation |
| `highLowService.ts` | 52W high/low analysis |
| `giftNiftyService.ts` | GIFT Nifty data |
| `verdictService.ts` | Market verdict parsing |
| `marketBulletinService.ts` | News bulletin |
| `keyStocksService.ts` | Key stock highlights |
| `realTimeOiService.ts` | Real-time OI updates |
| `pdfService.ts` | PDF generation |
| `types.ts` | TypeScript type definitions |

---

### 3. Report Components

The frontend renders 11 report pages:

| Page | Component/Section | Data Source |
|------|-------------------|-------------|
| 1 | NIFTY Overview & Technical Analysis | `nifty.txt` |
| 2 | Market Mood Index (MMI) | `mmi.txt` + GROQ AI |
| 3 | NIFTY Options Analysis | `nifty_oi_analysis.json` |
| 4 | Market Heatmap | Stock data aggregation |
| 5 | Market Bulletin & Key Stocks | `bulletin.txt` |
| 6 | FII/DII Activity | `fii_dii.txt` |
| 7 | VIX Analysis & 52W High/Low | `vix.txt` |
| 8 | Global Markets & Currency | `global_indices.txt`, `currencies.txt` |
| 9 | Gold Market Analysis | `gold_rates.txt` |
| 10 | Silver Market Analysis | `silver_rates.txt` |
| 11 | Legal Information | Static content |

---

## 🔄 Data Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                        DATA FLOW                                 │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   EXTERNAL SOURCES              BACKEND               FRONTEND  │
│   ─────────────────      ───────────────────     ────────────── │
│                                                                  │
│   Yahoo Finance ──────┐                                          │
│   NSE API ───────────┤                                          │
│   MoneyControl ──────┼──▶ fetch_data_v3.py ──▶ /public/Data/*.txt│
│   Groww ─────────────┤         │                    │           │
│   LiveChennai ───────┘         ▼                    ▼           │
│                        anti_gravity_vix.py     services/*.ts     │
│                                │                    │           │
│                                ▼                    ▼           │
│                        SQLite DB ◀────────▶   React Components  │
│                     (PCR snapshots)              │           │
│                                                     ▼           │
│                                              Report.tsx          │
│                                                     │           │
│                                                     ▼           │
│                                            PDF/PNG/ZIP Export    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🚀 How to Run

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm 9+

### Setup

1. **Install Backend Dependencies:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure API Keys:**
   Create `backend/.env`:
   ```env
   GROQ_API_KEY=your_groq_api_key
   TWELVE_DATA_KEY=your_twelve_data_key
   NEWS_API_KEY=your_news_api_key
   ```

3. **Install Frontend Dependencies:**
   ```bash
   cd frontend
   npm install
   ```

### Run the Application

```bash
# From project root
./run_report.sh
```

This will:
1. Execute `fetch_data_v3.py` to fetch latest market data
2. Generate data files in `frontend/public/Data/`
3. Start the Vite dev server on `http://localhost:5173`

---

## 📁 Generated Data Files

| File | Content | Format |
|------|---------|--------|
| `nifty.txt` | NIFTY 50 price, change, volume | Plain text |
| `vix.txt` | India VIX value, change | Plain text |
| `mmi.txt` | Market Mood Index data | Plain text |
| `nifty_oi_analysis.json` | Options chain analysis | JSON |
| `nifty_pcr.txt` | Put-Call Ratio | Plain text |
| `fii_dii.txt` | FII/DII activity data | Plain text |
| `gold_rates.txt` | Gold prices with history | Plain text |
| `silver_rates.txt` | Silver prices with history | Plain text |
| `global_indices.txt` | Global market indices | Plain text |
| `currencies.txt` | Currency exchange rates | Plain text |
| `gift_nifty.txt` | GIFT Nifty futures data | Plain text |
| `movers.txt` | Top gainers/losers | Plain text |
| `highlow.txt` | 52W high/low stocks | Plain text |

---

## 🧪 Reliability Features

### Multi-Source Fallback
Every data point has multiple sources. If primary fails, automatic fallback:
- **VIX:** Yahoo → NSE → Groww → MoneyControl
- **Options:** NSE API → Groww → MoneyControl
- **Stocks:** Yahoo Finance with rate limiting

### Error Handling
- Comprehensive try-catch blocks
- Logging with timestamps
- Retry logic with exponential backoff
- Graceful degradation (partial data still rendered)

### Data Validation
- Freshness checks (reject stale data)
- Cross-source validation for VIX
- Anomaly detection (VIX range 8-40)
- Weekend/holiday handling

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details.

---

*Documentation generated for StonkzzReport Market Analysis System*
