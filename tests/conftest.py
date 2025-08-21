import pytest
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture(scope="session")
def test_data():
    """Provide test data for use across tests"""
    return {
        "valid_symbols": ["AAPL", "GOOGL", "MSFT", "TSLA"],
        "invalid_symbols": ["INVALID", "FAKE123", ""],
        "sample_stock_data": {
            "symbol": "AAPL",
            "price": 150.50,
            "change": 2.30,
            "change_percent": 1.55,
            "volume": 45000000,
            "market_cap": 2500000000000,
            "pe_ratio": 28.5,
            "dividend_yield": 0.0065,
            "fifty_two_week_high": 180.25,
            "fifty_two_week_low": 120.75,
            "currency": "USD"
        },
        "sample_mcp_requests": {
            "initialize": {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize"
            },
            "tools_list": {
                "jsonrpc": "2.0", 
                "id": 2,
                "method": "tools/list"
            },
            "tools_call_quote": {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "get_realtime_quote",
                    "arguments": {"symbol": "AAPL"}
                }
            },
            "tools_call_fundamentals": {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "get_fundamentals",
                    "arguments": {
                        "instrument": "AAPL",
                        "period": "annual",
                        "years": 3
                    }
                }
            }
        }
    }


@pytest.fixture
def sample_json_rpc_requests():
    """Sample JSON-RPC requests for testing"""
    return {
        "valid_initialize": {
            "jsonrpc": "2.0",
            "id": "init-1", 
            "method": "initialize"
        },
        "valid_tools_list": {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        },
        "valid_tools_call": {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_realtime_quote",
                "arguments": {"symbol": "AAPL"}
            }
        },
        "invalid_missing_id": {
            "jsonrpc": "2.0",
            "method": "tools/list"
        },
        "invalid_missing_method": {
            "jsonrpc": "2.0",
            "id": 4
        },
        "invalid_unknown_method": {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "unknown/method"
        }
    }


@pytest.fixture
def mock_yfinance_data():
    """Mock yfinance data for testing"""
    import pandas as pd
    from datetime import datetime, timedelta
    
    # Generate sample price data
    dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='D')
    price_data = pd.DataFrame({
        'Open': [150.0, 151.0, 152.0, 151.5, 153.0, 154.0, 153.5, 155.0, 156.0, 157.0],
        'High': [152.0, 153.0, 154.0, 153.0, 155.0, 156.0, 155.5, 157.0, 158.0, 159.0],
        'Low': [149.0, 150.0, 151.0, 150.5, 152.0, 153.0, 152.5, 154.0, 155.0, 156.0],
        'Close': [151.0, 152.0, 153.0, 152.0, 154.0, 155.0, 154.5, 156.0, 157.0, 158.0],
        'Volume': [1000000, 1100000, 1200000, 1050000, 1300000, 1400000, 1350000, 1500000, 1600000, 1700000]
    }, index=dates)
    
    # Generate sample dividend data
    dividend_dates = pd.date_range(start='2023-01-01', periods=4, freq='3M')
    dividend_data = pd.Series([0.23, 0.24, 0.24, 0.25], index=dividend_dates)
    
    # Generate sample splits data
    split_data = pd.Series([2.0], index=[pd.Timestamp('2022-06-01')])
    
    return {
        'price_data': price_data,
        'dividend_data': dividend_data,
        'split_data': split_data,
        'info_data': {
            'marketCap': 2500000000000,
            'trailingPE': 28.5,
            'priceToBook': 5.2,
            'dividendYield': 0.0065,
            'fiftyTwoWeekHigh': 180.25,
            'fiftyTwoWeekLow': 120.75,
            'currency': 'USD',
            'regularMarketPrice': 158.0,
            'returnOnEquity': 0.28,
            'debtToEquity': 0.15,
            'currentRatio': 1.1,
            'grossMargins': 0.38,
            'operatingMargins': 0.25,
            'profitMargins': 0.23
        }
    }


@pytest.fixture(autouse=True)
def cleanup_imports():
    """Cleanup imports after each test to avoid conflicts"""
    yield
    # Clean up any modules that might have been imported during tests
    modules_to_remove = [m for m in sys.modules.keys() if m.startswith(('models', 'tools', 'mcp_handlers', 'main'))]
    for module in modules_to_remove:
        if module in sys.modules:
            del sys.modules[module]


@pytest.fixture
def error_test_cases():
    """Common error test cases for various functions"""
    return {
        'json_rpc_errors': [
            {
                'code': -32700,
                'name': 'Parse error',
                'description': 'Invalid JSON was received by the server'
            },
            {
                'code': -32600,
                'name': 'Invalid Request',
                'description': 'The JSON sent is not a valid Request object'
            },
            {
                'code': -32601,
                'name': 'Method not found',
                'description': 'The method does not exist / is not available'
            },
            {
                'code': -32602,
                'name': 'Invalid params',
                'description': 'Invalid method parameter(s)'
            },
            {
                'code': -32603,
                'name': 'Internal error',
                'description': 'Internal JSON-RPC error'
            }
        ],
        'stock_symbol_errors': [
            '',  # Empty string
            None,  # None value
            '   ',  # Whitespace only
            'TOOLONG123456789',  # Too long
            '123',  # All numbers
            'INVALID!@#',  # Special characters
        ],
        'date_format_errors': [
            '2024-13-01',  # Invalid month
            '2024-01-32',  # Invalid day
            '24-01-01',  # Wrong year format
            '2024/01/01',  # Wrong separator
            'January 1, 2024',  # Text format
            '2024-1-1',  # Single digit month/day
        ]
    }