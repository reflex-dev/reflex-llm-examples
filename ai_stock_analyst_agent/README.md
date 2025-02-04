# AI Stock Analyst Agent using Gemini 2.0 Flash (exp)

The **AI Stock Analyst Agent** leverages **Reflex**, **Agno** and **Gemini 2.0 Flash (exp)** to provide advanced financial analysis. It allows users to get comprehensive insights into stock market performance by analyzing individual stocks and their metrics. The app queries relevant data from stock sources, including historical prices, market analysis, and recommendations, to answer user queries about stocks and financial performance.

## Note

Educational Purpose Only: This project is intended for educational purposes only to demonstrate the power of AI in stock analysis.

---

## Features

- **Stock Analysis:** Analyze individual stocks, including key metrics like P/E ratio, market cap, EPS, and 52-week highs and lows.
- **Watchlist Management:** Add or remove stocks from your personalized watchlist for easy monitoring.
- **Gemini 2.0 Flash Integration:** Utilizes Google's Gemini 2.0 Flash for fast, accurate, and dynamic responses.
- **Real-Time Market Data:** Get live stock data, analyst recommendations, and company news from reliable sources like Yahoo Finance.
- **Custom Financial Reports:** In-depth analysis, including executive summaries, professional insights, and risk disclosures.

---

## Getting Started

### 1. Clone the Repository  
Clone the GitHub repository to your local machine:  
```bash  
git clone https://github.com/reflex-dev/reflex-llm-examples.git  
cd reflex-llm-examples/ai_stock_analyst_agent
```  

### 2. Install Dependencies  
Install the required dependencies:  
```bash  
pip install -r requirements.txt  
```  

### 3. Set Up Gemini API Key  
To use the Gemini 2.0 Flash model, you need a **Google API Key**. Follow these steps:  
Go to [Google AI Studio](https://aistudio.google.com/apikey), get your API Key, and set it as an environment variable:  
   ```bash  
   export GOOGLE_API_KEY="your-api-key-here"  
   ```  

### 4. Run the Reflex App  
Start the application:  
```bash  
reflex run  
```  

---

## How It Works  

1. **Stock Query:** Ask questions like "Analyze AAPL's performance" or any other stock symbol.
2. **Gemini 2.0 Flash:** The app generates a detailed report with metrics like the latest stock price, P/E ratio, market cap, analyst recommendations, and more.
3. **Real-Time Data:** The app integrates with Yahoo Finance and other tools to get real-time market insights.
4. **Watchlist:** Add stocks to your watchlist for easy monitoring and analysis over time.

---

## Why AI Stock Agent?

- **Real-Time Data Access:** Provides live stock information, analyst insights, and historical data to give you a full picture of stock performance.
- **Smart Financial Analysis:** The agent uses the power of Gemini 2.0 Flash and Yahoo Finance tools to give you comprehensive, accurate financial reports.
- **User-Friendly:** Seamless user experience with easy stock addition/removal, and clear, actionable insights.

---

## Contributing

We welcome contributions! Feel free to open issues or submit pull requests to improve the app.

---
