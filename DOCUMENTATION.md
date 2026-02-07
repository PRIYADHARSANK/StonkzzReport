# 📊 StonkzzReport - Complete Technical Documentation

---

## 🎯 Introduction

**StonkzzReport** is a comprehensive market report generation system designed to automatically fetch, analyze, and visualize Indian stock market data. The application creates beautiful, multi-page market reports with real-time data from various financial sources and **automatically emails the PDF report to configured recipients**.

### What Does It Do?

StonkzzReport aggregates data from multiple financial platforms and generates:
- **11-page professional market reports**
- **Real-time NIFTY 50 data and analysis**
- **Options chain visualization with PCR analysis**
- **FII/DII activity tracking**
- **Commodity prices (Gold/Silver)**
- **Global market indices and currency rates**
- **AI-powered market sentiment analysis**
- **Automated PDF generation and Email delivery**

### Key Features

| Feature | Description |
|---------|-------------|
| 📈 **Live Data Fetching** | Real-time data from Yahoo Finance, NSE, MoneyControl, Groww |
| 🤖 **AI Analysis** | GROQ-powered market sentiment analysis using LLaMA 3.3 |
| 📧 **Email Automation** | Auto-generates PDF and emails it to recipients immediately |
| 📷 **High-Quality Export** | PDF generation via Headless Browser (Playwright) |
| 🎨 **Modern UI** | React 19 with Tailwind CSS, responsive design |
| 🔄 **Multi-Source Fallback** | Automatic failover between data sources |
| 📊 **Options Analysis** | PCR calculation, support/resistance levels |

---

## 🏗️ Architecture Overview

```
StonkzzReport/
├── generate_pdf_report.py     # PDF generation & email orchestrator [NEW]
├── backend/                   # Python data fetching layer
│   ├── fetch_data_v3.py       # Main data orchestrator (2100+ lines)
│   ├── anti_gravity_vix.py    # Multi-source VIX fetcher
│   ├── scripts/               # Utility modules
│   │   ├── email_notifier.py  # Email sending service [NEW]
│   │   ├── robust_stock_fetcher.py
│   │   └── market_utils.py
│   └── .env                   # API keys & Email config
├── frontend/                  # React TypeScript application
│   ├── App.tsx                # Main application component
│   ├── components/            # React UI components
│   │   ├── Report.tsx         # Multi-page report renderer
│   │   └── ...
│   └── public/Data/           # Generated data files
└── run_report.sh              # Main execution script (Fetch -> PDF -> Email)
```

---

## 🛠️ Technology Stack

### Backend (Python)

| Package | Version | Purpose |
|---------|---------|---------|
| `yfinance` | 1.0 | Yahoo Finance API for stock/index data |
| `playwright` | 1.49+ | Headless browser for PDF generation |
| `beautifulsoup4` | 4.12+ | Web scraping for MoneyControl, Groww |
| `requests` | 2.32+ | HTTP client for API calls |
| `pandas` | 2.2+ | Data manipulation and analysis |
| `python-dotenv` | 1.0+ | Environment variable management |
| `smtplib` | Built-in | Email sending (Gmail/SMTP) |

### Frontend (React TypeScript)

| Package | Version | Purpose |
|---------|---------|---------|
| `react` | 19.x | UI framework |
| `vite` | 6.x | Build tool and dev server |
| `typescript` | 5.x | Type-safe JavaScript |
| `recharts` | 3.x | Charting library |
| `groq-sdk` | 0.x | GROQ AI API client |
| `tailwindcss` | 3.x | Styling |

---

## 🔑 Configuration (.env)

The application uses `backend/.env` for all configuration.

### 1. API Keys
```env
GROQ_API_KEY=your_groq_api_key
TWELVE_DATA_KEY=your_twelve_data_key
NEWS_API_KEY=your_news_api_key
```

### 2. Email Configuration [NEW]
Required for automated reporting:
```env
EMAIL_SENDER=your_email@gmail.com
EMAIL_APP_PASSWORD=your_app_password
EMAIL_RECIPIENTS=recipient1@example.com,recipient2@example.com
EMAIL_ENABLED=true
```

---

## ⚙️ Core Functionalities

### 1. Data Fetching Layer (`fetch_data_v3.py`)
The main orchestrator that fetches all market data from Nifty, VIX, Options Chain, FII/DII, and Commodities. It creates JSON/Text files in `frontend/public/Data/`.

### 2. PDF & Email Automation (`generate_pdf_report.py`)
Automates the reporting workflow:
1.  **Starts Frontend**: Launches a local Vite server (if not running).
2.  **Generates PDF**: Uses Playwright to render the dashboard in a headless Chromium browser and saves it as a PDF.
3.  **Sends Email**: Uses `email_notifier.py` to send the generated PDF to configured recipients.

### 3. Frontend Services Layer
Parses the raw data files and renders the 11-page report using React components.

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
   playwright install chromium  # Required for PDF generation
   ```

2. **Configure `.env`:**
   Update `backend/.env` with your API keys and Email credentials.

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

**What happens:**
1.  **Fetch Data**: Executes `fetch_data_v3.py` to get latest market data.
2.  **Generate & Email**: Executes `generate_pdf_report.py`.
    -   Starts local server.
    -   Creates PDF report.
    -   Emails it to `EMAIL_RECIPIENTS`.
    -   Stops local server.

---

## 📁 Generated Data Files

| File | Content | Format |
|------|---------|--------|
| `nifty.txt` | NIFTY 50 price, change, volume | Plain text |
| `vix.txt` | India VIX value, change | Plain text |
| `mmi.txt` | Market Mood Index data | Plain text |
| `nifty_oi_analysis.json` | Options chain analysis | JSON |
| ... | ... | ... |
| `generated_reports/*.pdf` | **The final PDF report** | PDF |

---

## 🧪 Reliability Features

### Multi-Source Fallback
Every data point has multiple sources. If primary fails, automatic fallback:
- **VIX:** Yahoo → NSE → Groww → MoneyControl
- **Options:** NSE API → Groww → MoneyControl

### Automated Reporting
- **Headless Generation**: Does not require a visible browser window.
- **Retry Logic**: Email sending and Browser launching have built-in retries.
- **Port Management**: Automatically handles port 5173 conflicts.

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details.
