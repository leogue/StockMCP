# 📈 StockMCP

> **A comprehensive Model Context Protocol (MCP) server for real-time stock market data using Yahoo Finance**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-85%20passed-brightgreen.svg)](#testing)

StockMCP provides a powerful, JSON-RPC 2.0 compliant interface for accessing comprehensive stock market data, built on the Model Context Protocol standard. Perfect for AI applications, financial analysis tools, and trading bots.

## ✨ Features

### 🎯 Core Capabilities
- **Real-time Stock Quotes** - Live price data with volume, market cap, and key ratios
- **Historical Price Data** - OHLCV data with customizable date ranges and intervals
- **Financial Fundamentals** - Income statements, balance sheets, and cash flow data
- **Dividend Analysis** - Complete dividend history with growth metrics and consistency scoring
- **Total Return Calculation** - Performance tracking with dividend reinvestment
- **Corporate Actions** - Stock splits and other corporate events

### 🏗️ Technical Features
- **MCP Protocol Compliant** - Full JSON-RPC 2.0 support with proper error handling
- **FastAPI Backend** - High-performance async API with automatic OpenAPI documentation
- **Docker Ready** - Containerized deployment with optimized Python environment
- **Type Safety** - Complete Pydantic validation for all data models
- **Comprehensive Testing** - 85+ tests covering all components and edge cases
- **Modern Python** - Built with Python 3.10+ and cutting-edge libraries

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/StockMCP.git
cd StockMCP

# Build and run with Docker
docker build -t stockmcp .
docker run -p 3001:3001 stockmcp
```

### Local Development

```bash
# Install dependencies with uv (fastest)
uv sync

# Or with pip
pip install -e .

# Run the server
python src/main.py
# Server runs on http://localhost:3001
```

## 📖 API Documentation

### MCP Tool Discovery

List all available tools:

```bash
curl -X POST http://localhost:3001/api/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'
```

### Available Tools

#### 📊 Real-time Stock Quote

Get current market data for any stock:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "get_realtime_quote",
    "arguments": {
      "symbol": "AAPL"
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [{
      "type": "text",
      "text": "{
        \"symbol\": \"AAPL\",
        \"price\": 175.25,
        \"change\": 2.30,
        \"change_percent\": 1.33,
        \"volume\": 45230100,
        \"market_cap\": 2750000000000,
        \"pe_ratio\": 28.5,
        \"dividend_yield\": 0.0052,
        \"fifty_two_week_high\": 198.23,
        \"fifty_two_week_low\": 164.08,
        \"currency\": \"USD\"
      }"
    }]
  }
}
```

#### 📈 Historical Price Data

Retrieve OHLCV data with total return calculation:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "get_price_history",
    "arguments": {
      "instrument": "AAPL",
      "start": "2024-07-01",
      "end": "2024-08-21",
      "interval": "1d",
      "adjusted": true,
      "include_total_return": true
    }
  }
}
```

**Features:**
- 📅 **Flexible Date Ranges** - Daily, weekly, or monthly intervals
- 💰 **Total Return Index** - Performance with dividend reinvestment
- 🔄 **Corporate Actions** - Automatic adjustment for splits and dividends
- ⚡ **High Performance** - Optimized data processing and caching

#### 📋 Financial Fundamentals

Access comprehensive financial statements:

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "get_fundamentals",
    "arguments": {
      "instrument": "AAPL",
      "period": "annual",
      "years": 5
    }
  }
}
```

**Includes:**
- 💼 **Income Statements** - Revenue, expenses, and profitability
- 🏦 **Balance Sheets** - Assets, liabilities, and equity
- 💸 **Cash Flow Statements** - Operating, investing, and financing activities
- 📊 **Financial Ratios** - P/E, ROE, debt ratios, and more

#### 💎 Dividend Analysis

Comprehensive dividend history and quality metrics:

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "tools/call",
  "params": {
    "name": "get_dividends_and_actions",
    "arguments": {
      "instrument": "AAPL",
      "start": "2020-01-01",
      "end": "2024-08-21"
    }
  }
}
```

**Features:**
- 📈 **Growth Analysis** - CAGR calculation over multiple periods
- 🎯 **Consistency Scoring** - Dividend reliability metrics (0-100 scale)
- 📅 **Payment History** - Complete ex-dividend dates and amounts
- 🔄 **Corporate Actions** - Stock splits and special dividends

## 🛠️ Development

### Project Structure

```
StockMCP/
├── src/
│   ├── main.py              # FastAPI server and endpoints
│   ├── models.py            # Pydantic models for MCP and stock data
│   ├── mcp_handlers.py      # MCP protocol request handlers
│   └── tools.py             # Stock market tools implementation
├── tests/                   # Comprehensive test suite (85+ tests)
├── Dockerfile              # Container configuration
├── pyproject.toml          # Project dependencies and configuration
└── README.md              # This file
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_api.py

# Run with coverage
uv run pytest --cov=src
```

### Dependencies

**Core Dependencies:**
- **FastAPI** - Modern web framework for APIs
- **Pydantic** - Data validation using Python type hints
- **yfinance** - Yahoo Finance data retrieval
- **pandas** - Data manipulation and analysis
- **scipy** - Scientific computing (required by yfinance)

**Development Dependencies:**
- **pytest** - Testing framework
- **httpx** - HTTP client for testing
- **pytest-mock** - Mocking utilities

## 🐳 Docker Deployment

### Build and Run

```bash
# Build the image
docker build -t stockmcp .

# Run the container
docker run -p 3001:3001 stockmcp

# Run in background
docker run -d -p 3001:3001 --name stockmcp-server stockmcp
```

### Environment Configuration

The container exposes the API on port 3001 by default. You can customize this:

```bash
# Custom port mapping
docker run -p 8080:3001 stockmcp

# With environment variables
docker run -p 3001:3001 -e LOG_LEVEL=DEBUG stockmcp
```

## 🔧 Configuration

### Server Configuration

The server can be configured through environment variables:

- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 3001)

### API Limits

Yahoo Finance has rate limits. For production use, consider:
- Implementing request caching
- Adding retry logic with exponential backoff
- Using multiple data sources for redundancy

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes** with proper tests
4. **Run the test suite** (`uv run pytest`)
5. **Commit your changes** (`git commit -m 'Add amazing feature'`)
6. **Push to the branch** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

### Development Guidelines

- **Type Hints** - All functions should have proper type annotations
- **Tests** - New features must include comprehensive tests
- **Documentation** - Update README and docstrings for any API changes
- **Code Style** - Follow PEP 8 and use meaningful variable names

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Yahoo Finance** - For providing free stock market data
- **Model Context Protocol** - For the excellent protocol specification
- **FastAPI** - For the amazing web framework
- **Pydantic** - For robust data validation

## 📞 Support

- 🐛 **Bug Reports** - [Open an issue](https://github.com/leogue/StockMCP/issues)
- 💡 **Feature Requests** - [Start a discussion](https://github.com/leogue/StockMCP/discussions)
- 📖 **Documentation** - Check our comprehensive API docs
- 💬 **Community** - Join our discussions for help and ideas

---

<div align="center">

**Made with ❤️ for the financial data community**

[⭐ Star this repo](https://github.com/leogue/StockMCP) | [🍴 Fork it](https://github.com/leogue/StockMCP/fork) | [📖 Docs](https://github.com/leogue/StockMCP/wiki)

</div>