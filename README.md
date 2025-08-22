# Market Report Generator

A React TypeScript application for generating and capturing multi-page market reports with multiple export options.

## Features

- 📊 Generate comprehensive market reports with 11 pages
- 📷 High-quality screenshot capture (3x scale)
- 📱 View reports as responsive web pages
- 📥 Download report pages as PNG files in ZIP format
- 📄 Export reports as PDFs
- ⚡ Fast and efficient data processing
- 🎨 Beautiful and consistent design with Tailwind CSS

## Screenshot Methods

The application provides three ways to capture report content:

1. **View as Website**: Opens report in a new window with optimized layout
2. **Capture All Pages**: Captures all 11 pages directly from the preview
3. **Capture from Website**: Opens and captures pages from the website view

## Report Pages

1. NIFTY Overview & Technical Analysis
2. Market Mood Index (MMI)
3. NIFTY Options Analysis
4. Market Heatmap
5. Market Bulletin & Key Stocks
6. FII/DII Activity
7. VIX Analysis & 52W High/Low
8. Global Markets & Currency
9. Gold Market Analysis
10. Silver Market Analysis
11. Legal Information

## Technical Details

- React 19 with TypeScript
- Tailwind CSS for styling
- html-to-image for high-quality captures
- JSZip for file packaging
- File-saver for downloads
- Vite for development and building

## Project Structure

```
├── components/          # React components
│   ├── MMIGauge.tsx
│   ├── NiftyDashboard.tsx
│   ├── OpenInterestChart.tsx
│   ├── PdfGenerator.tsx
│   └── Report.tsx
├── services/           # Data fetching and processing
├── Data/              # Mock data files
└── App.tsx            # Main application
```

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd market-report-generator
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start development server:
   ```bash
   npm run dev
   ```

4. Build for production:
   ```bash
   npm run build
   ```

## Usage

1. Load the application
2. Wait for data to load
3. Use the control buttons to:
   - View as website
   - Save as PDF
   - Capture screenshots
   - Toggle preview

## Screenshot Tips

For best results when capturing pages:
- Wait for all images and fonts to load
- Ensure stable internet connection
- Keep window focused during capture
- Allow extra time for charts to render

## Data Sources

Market data is sourced from:
- NSE
- BSE
- Moneycontrol
- Investing.com
- Trendlyne
- Sensibull

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License. See LICENSE file for details.
