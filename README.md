# Trading Journal CLI

> **[中文版 README](README_CN.md)** | **English**

A lightweight command-line tool for analyzing Binance trading records with intelligent PnL calculation, stablecoin normalization, and comprehensive multi-currency analysis.

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

### 🧮 **Smart PnL Calculation**
- **Weighted Average Cost Method**: Accurate realized profit/loss calculation
- **Real-time Cost Basis Tracking**: See how your average cost changes with each trade
- **Detailed Trade Analysis**: View PnL calculation process for each transaction

### 🏦 **Stablecoin Normalization**
- **Automatic Conversion**: FDUSD, USDC, BUSD → USDT standardization
- **Cross-Stablecoin Trading**: Handle trades bought with FDUSD but sold in USDT
- **Unified Reporting**: All PnL displayed in USDT equivalent

### 💱 **Multi-Currency Analysis**
- **Per-Currency Reports**: Detailed analysis for individual cryptocurrencies
- **Portfolio Overview**: Complete trading statistics across all assets
- **Trade History Viewing**: Comprehensive transaction logs with cost basis

### 📁 **File Format Support**
- **Bilingual Excel Support**: Both English and Chinese Binance export formats
- **Smart Column Mapping**: Automatic detection of column structure
- **Error Handling**: Robust parsing with helpful error messages

## 🚀 Quick Start

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/tti6o/trading-journal-cli.git
cd trading-journal-cli

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize database
python main.py init
```

### Basic Usage

```bash
# Import your Binance trading history
python main.py import your_binance_trades.xlsx

# View overall trading report
python main.py report

# Analyze specific cryptocurrency
python main.py currency BTC

# View detailed trade history with cost basis
python main.py currency XRP --details

# List all traded currencies
python main.py list-currencies
```

## 📋 Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `init` | Initialize database | `python main.py init` |
| `import <file>` | Import Excel trading records | `python main.py import trades.xlsx` |
| `report` | Generate overall trading summary | `python main.py report` |
| `currency <symbol>` | View currency-specific analysis | `python main.py currency BTC` |
| `currency <symbol> --details` | Show detailed trade history | `python main.py currency ETH --details` |
| `list-currencies` | List all traded currencies | `python main.py list-currencies` |

## 🏗️ Architecture

This project follows a clean 4-layer architecture:

```
├── CLI Layer (main.py)           # Click-based command interface
├── Business Logic (journal_core.py)  # Core trading logic
├── Utilities (utilities.py)     # Calculations and formatting
└── Data Access (database_setup.py)   # SQLite operations
```

## 📊 Sample Output

### Currency Analysis with Cost Basis
```
====================================================================================================
XRP All Trade Details (with Average Cost Calculation)
====================================================================================================
Total: 10 trades

No.  Date         Pair       Side  Quantity        Price      Amount       Fee       Avg Cost     PnL
----------------------------------------------------------------------------------------------------
1    2025-05-23   XRPUSDT    BUY   5037.1000      2.2953     11561.66     0         2.2953       -
2    2025-05-23   XRPUSDT    BUY   1676.4000      2.2953     3847.84      0         2.2953       -
...
7    2025-06-08   XRPUSDT    SELL  3153.8000      2.2199     7001.12      0         2.2686       -153.51
8    2025-06-08   XRPUSDT    SELL  1594.9000      2.2199     3540.52      0         2.2686       -77.63
----------------------------------------------------------------------------------------------------

📊 Trading Summary:
  Buy Trades: 6  |  Sell Trades: 4
  Total Bought: 9497.5000 XRP
  Total Sold: 7123.1000 XRP
  Current Holdings: 2374.4000 XRP
  Current Average Cost: 2.2686 USDT/XRP
  Position Value: 5386.50 USDT
  Realized PnL: -235.75 USDT
```

## 🔒 Privacy & Security

- **✅ Local Processing**: All data processed locally, nothing uploaded
- **✅ No API Keys**: No exchange API access required
- **✅ Data Protection**: Comprehensive .gitignore prevents accidental data exposure
- **✅ Sample Data Only**: Repository contains only test data

## 📚 Documentation

- **[Architecture Guide](project_docs/ARCHITECTURE.md)** - System design and structure
- **[Core Logic](project_docs/CORE_LOGIC.md)** - PnL calculation methodology  
- **[Usage Guide](project_docs/USAGE_GUIDE.md)** - Detailed usage instructions
- **[Test Scripts](scripts/README.md)** - Validation and demo scripts

## 🛠️ Development

### Project Structure
```
trading-journal-cli/
├── main.py                 # CLI entry point
├── journal_core.py         # Business logic layer
├── database_setup.py       # Data access layer
├── utilities.py            # Utility functions
├── requirements.txt        # Python dependencies
├── sample_trades.xlsx      # Test data
├── scripts/               # Test and demo scripts
├── project_docs/          # Comprehensive documentation
└── user_data/            # Your private trading data (gitignored)
```

### Running Tests
```bash
# Run all demo scripts
python scripts/demo_all_features.py

# Test with sample data
python scripts/test_sample.py

# Verify stablecoin normalization
python scripts/verify_stable_coins.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## ⚠️ Disclaimer

This tool is for personal trading analysis only. Please ensure the security of your trading data and use at your own discretion.

---

**Made with ❤️ for crypto traders** 