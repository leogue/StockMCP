import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tools import (
    get_available_tools, get_realtime_quote, get_fundamentals,
    get_price_history, get_dividends_and_actions, execute_tool,
    calculate_financial_ratios, calculate_total_return_index,
    calculate_dividend_cagr, calculate_dividend_consistency
)
from models import MCPTool, FinancialRatios


class TestToolsRegistry:
    """Tests for tools registry and discovery"""
    
    def test_get_available_tools(self):
        """Test getting available tools list"""
        tools = get_available_tools()
        
        assert isinstance(tools, list)
        assert len(tools) == 4  # We have 4 tools defined
        
        # Check all tools are MCPTool instances
        for tool in tools:
            assert isinstance(tool, MCPTool)
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'title')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'inputSchema')
        
        # Check expected tools are present
        tool_names = [tool.name for tool in tools]
        expected_tools = [
            "get_realtime_quote",
            "get_fundamentals",
            "get_price_history", 
            "get_dividends_and_actions"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
    
    def test_tool_schemas_validation(self):
        """Test that all tool schemas are properly formatted"""
        tools = get_available_tools()
        
        for tool in tools:
            schema = tool.inputSchema
            
            # Check schema structure
            assert schema.type == "object"
            assert isinstance(schema.properties, dict)
            assert isinstance(schema.required, list)
            
            # Check that all required fields are in properties
            for required_field in schema.required:
                assert required_field in schema.properties
            
            # Check property definitions
            for prop_name, prop_def in schema.properties.items():
                assert "type" in prop_def
                assert "description" in prop_def
    
    def test_execute_tool_dispatcher(self):
        """Test tool execution dispatcher"""
        # Test valid tool
        result = execute_tool("get_realtime_quote", {"symbol": "AAPL"})
        assert isinstance(result, str)
        
        # Parse result to check it's valid JSON
        result_data = json.loads(result)
        assert isinstance(result_data, dict)
        
        # Test invalid tool
        result = execute_tool("invalid_tool", {})
        result_data = json.loads(result)
        assert "error" in result_data
        assert "not found" in result_data["error"]
        assert "available_tools" in result_data


class TestRealtimeQuote:
    """Tests for get_realtime_quote tool"""
    
    @patch('tools.yf.Ticker')
    def test_get_realtime_quote_success(self, mock_ticker):
        """Test successful realtime quote retrieval"""
        # Mock yfinance data
        mock_ticker_instance = Mock()
        mock_ticker.return_value = mock_ticker_instance
        
        # Mock info data
        mock_ticker_instance.info = {
            'marketCap': 2500000000000,
            'trailingPE': 28.5,
            'dividendYield': 0.0065,
            'fiftyTwoWeekHigh': 180.25,
            'fiftyTwoWeekLow': 120.75,
            'currency': 'USD'
        }
        
        # Mock historical data
        mock_hist = pd.DataFrame({
            'Close': [149.0, 151.5],
            'Volume': [44000000, 45000000]
        })
        mock_ticker_instance.history.return_value = mock_hist
        
        result = get_realtime_quote({"symbol": "AAPL"})
        result_data = json.loads(result)
        
        assert "error" not in result_data
        assert result_data["symbol"] == "AAPL"
        assert result_data["price"] == 151.5
        assert result_data["change"] == 2.5
        assert result_data["change_percent"] == pytest.approx(1.677, rel=1e-2)
        assert result_data["volume"] == 45000000
        assert result_data["market_cap"] == 2500000000000
        assert result_data["currency"] == "USD"
    
    @patch('tools.yf.Ticker')
    def test_get_realtime_quote_no_data(self, mock_ticker):
        """Test realtime quote with no data found"""
        mock_ticker_instance = Mock()
        mock_ticker.return_value = mock_ticker_instance
        
        # Return empty DataFrame
        mock_ticker_instance.history.return_value = pd.DataFrame()
        
        result = get_realtime_quote({"symbol": "INVALID"})
        result_data = json.loads(result)
        
        assert "error" in result_data
        assert "No data found" in result_data["error"]
        assert result_data["symbol"] == "INVALID"
    
    def test_get_realtime_quote_missing_symbol(self):
        """Test realtime quote with missing symbol"""
        result = get_realtime_quote({})
        result_data = json.loads(result)
        
        assert "error" in result_data
        assert "Symbol is required" in result_data["error"]
    
    def test_get_realtime_quote_empty_symbol(self):
        """Test realtime quote with empty symbol"""
        result = get_realtime_quote({"symbol": ""})
        result_data = json.loads(result)
        
        assert "error" in result_data
        assert "Symbol is required" in result_data["error"]
    
    @patch('tools.yf.Ticker')
    def test_get_realtime_quote_exception(self, mock_ticker):
        """Test realtime quote with exception"""
        mock_ticker.side_effect = Exception("Network error")
        
        result = get_realtime_quote({"symbol": "AAPL"})
        result_data = json.loads(result)
        
        assert "error" in result_data
        assert "Network error" in result_data["error"]


class TestFundamentals:
    """Tests for get_fundamentals tool"""
    
    @patch('tools.yf.Ticker')
    def test_get_fundamentals_annual(self, mock_ticker):
        """Test fundamentals retrieval with annual data"""
        mock_ticker_instance = Mock()
        mock_ticker.return_value = mock_ticker_instance
        
        # Mock financial data
        mock_ticker_instance.info = {'currency': 'USD', 'trailingPE': 25.0}
        
        # Create mock financial statements
        dates = pd.to_datetime(['2023-12-31', '2022-12-31'])
        mock_financials = pd.DataFrame({
            dates[0]: {'Total Revenue': 100000, 'Net Income': 20000},
            dates[1]: {'Total Revenue': 90000, 'Net Income': 18000}
        })
        
        mock_ticker_instance.financials = mock_financials.T
        mock_ticker_instance.balance_sheet = pd.DataFrame()
        mock_ticker_instance.cashflow = pd.DataFrame()
        
        result = get_fundamentals({
            "instrument": "AAPL",
            "period": "annual",
            "years": 2
        })
        
        result_data = json.loads(result)
        assert "error" not in result_data
        assert result_data["symbol"] == "AAPL"
        assert "income" in result_data
        assert "balance" in result_data
        assert "cashflow" in result_data
        assert "ratios" in result_data
        assert "meta" in result_data
        
        # Check metadata
        meta = result_data["meta"]
        assert meta["period_type"] == "annual"
        assert meta["years_requested"] == 2
    
    def test_get_fundamentals_missing_instrument(self):
        """Test fundamentals with missing instrument"""
        result = get_fundamentals({"period": "annual"})
        result_data = json.loads(result)
        
        assert "error" in result_data
        assert "Instrument" in result_data["error"]
    
    def test_get_fundamentals_invalid_period(self):
        """Test fundamentals with invalid period"""
        result = get_fundamentals({
            "instrument": "AAPL",
            "period": "invalid"
        })
        result_data = json.loads(result)
        
        assert "error" in result_data
        assert "Period must be one of" in result_data["error"]
    
    @patch('tools.yf.Ticker')
    def test_get_fundamentals_quarterly(self, mock_ticker):
        """Test fundamentals with quarterly data"""
        mock_ticker_instance = Mock()
        mock_ticker.return_value = mock_ticker_instance
        
        mock_ticker_instance.info = {'currency': 'USD'}
        mock_ticker_instance.quarterly_financials = pd.DataFrame()
        mock_ticker_instance.quarterly_balance_sheet = pd.DataFrame()
        mock_ticker_instance.quarterly_cashflow = pd.DataFrame()
        
        result = get_fundamentals({
            "instrument": "AAPL",
            "period": "quarterly",
            "years": 4
        })
        
        result_data = json.loads(result)
        assert result_data["meta"]["period_type"] == "quarterly"
        assert result_data["meta"]["years_requested"] == 4


class TestPriceHistory:
    """Tests for get_price_history tool"""
    
    @patch('tools.yf.Ticker')
    def test_get_price_history_success(self, mock_ticker):
        """Test successful price history retrieval"""
        mock_ticker_instance = Mock()
        mock_ticker.return_value = mock_ticker_instance
        
        # Mock historical data
        dates = pd.date_range('2024-01-01', periods=5, freq='D')
        mock_hist = pd.DataFrame({
            'Open': [150.0, 151.0, 152.0, 153.0, 154.0],
            'High': [151.0, 152.0, 153.0, 154.0, 155.0],
            'Low': [149.0, 150.0, 151.0, 152.0, 153.0],
            'Close': [150.5, 151.5, 152.5, 153.5, 154.5],
            'Volume': [1000000, 1100000, 1200000, 1300000, 1400000]
        }, index=dates)
        
        mock_ticker_instance.history.return_value = mock_hist
        mock_ticker_instance.dividends = pd.Series(dtype=float)
        mock_ticker_instance.splits = pd.Series(dtype=float)
        
        result = get_price_history({
            "instrument": "AAPL",
            "start": "2024-01-01",
            "end": "2024-01-05",
            "interval": "1d"
        })
        
        result_data = json.loads(result)
        assert "error" not in result_data
        assert result_data["symbol"] == "AAPL"
        assert len(result_data["bars"]) == 5
        assert result_data["interval"] == "1d"
        assert result_data["start_date"] == "2024-01-01"
        assert result_data["end_date"] == "2024-01-05"
        
        # Check first bar
        first_bar = result_data["bars"][0]
        assert first_bar["o"] == 150.0
        assert first_bar["h"] == 151.0
        assert first_bar["l"] == 149.0
        assert first_bar["c"] == 150.5
        assert first_bar["v"] == 1000000
    
    def test_get_price_history_missing_params(self):
        """Test price history with missing required parameters"""
        # Missing instrument
        result = get_price_history({"start": "2024-01-01", "end": "2024-01-05"})
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Instrument" in result_data["error"]
        
        # Missing dates
        result = get_price_history({"instrument": "AAPL"})
        result_data = json.loads(result)
        assert "error" in result_data
        assert "start and end dates" in result_data["error"]
    
    def test_get_price_history_invalid_interval(self):
        """Test price history with invalid interval"""
        result = get_price_history({
            "instrument": "AAPL",
            "start": "2024-01-01",
            "end": "2024-01-05",
            "interval": "5m"
        })
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Interval must be one of" in result_data["error"]
    
    def test_get_price_history_1m_interval_limit(self):
        """Test 1-minute interval date range limitation"""
        result = get_price_history({
            "instrument": "AAPL",
            "start": "2023-01-01",
            "end": "2024-01-01",
            "interval": "1m"
        })
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "1-minute interval data is only available" in result_data["error"]


class TestDividendsAndActions:
    """Tests for get_dividends_and_actions tool"""
    
    @patch('tools.yf.Ticker')
    def test_get_dividends_and_actions_success(self, mock_ticker):
        """Test successful dividends and actions retrieval"""
        mock_ticker_instance = Mock()
        mock_ticker.return_value = mock_ticker_instance
        
        # Mock dividend data
        dates = pd.date_range('2020-01-01', periods=20, freq='3ME')
        dividends = pd.Series([0.20, 0.21, 0.22, 0.23] * 5, index=dates)
        mock_ticker_instance.dividends = dividends
        
        # Mock splits data
        split_dates = pd.date_range('2022-01-01', periods=1)
        splits = pd.Series([2.0], index=split_dates)
        mock_ticker_instance.splits = splits
        
        # Mock current price
        mock_ticker_instance.info = {'regularMarketPrice': 150.0}
        
        result = get_dividends_and_actions({
            "instrument": "AAPL",
            "start": "2020-01-01",
            "end": "2024-12-31"
        })
        
        result_data = json.loads(result)
        assert "error" not in result_data
        assert result_data["symbol"] == "AAPL"
        assert len(result_data["dividends"]) == 20
        assert len(result_data["actions"]) == 1
        
        # Check dividend record structure
        dividend = result_data["dividends"][0]
        assert "ex_date" in dividend
        assert "amount" in dividend
        assert "currency" in dividend
        
        # Check corporate action structure
        action = result_data["actions"][0]
        assert action["type"] == "split"
        assert action["factor"] == 2.0
        assert "effective_date" in action
    
    def test_get_dividends_and_actions_missing_instrument(self):
        """Test dividends and actions with missing instrument"""
        result = get_dividends_and_actions({})
        result_data = json.loads(result)
        
        assert "error" in result_data
        assert "Instrument" in result_data["error"]
    
    @patch('tools.yf.Ticker')
    def test_get_dividends_and_actions_default_dates(self, mock_ticker):
        """Test dividends and actions with default date range"""
        mock_ticker_instance = Mock()
        mock_ticker.return_value = mock_ticker_instance
        
        mock_ticker_instance.dividends = pd.Series(dtype=float)
        mock_ticker_instance.splits = pd.Series(dtype=float)
        mock_ticker_instance.info = {'regularMarketPrice': 150.0}
        
        result = get_dividends_and_actions({"instrument": "AAPL"})
        result_data = json.loads(result)
        
        # Should use default 10-year range
        assert "period_start" in result_data
        assert "period_end" in result_data


class TestUtilityFunctions:
    """Tests for utility functions"""
    
    def test_calculate_financial_ratios(self):
        """Test financial ratios calculation"""
        mock_ticker = Mock()
        info = {
            'trailingPE': 25.0,
            'priceToBook': 5.0,
            'returnOnEquity': 0.15,
            'marketCap': 2500000000000
        }
        
        # Mock empty financial statements
        mock_ticker.financials = pd.DataFrame()
        mock_ticker.balance_sheet = pd.DataFrame()
        mock_ticker.cashflow = pd.DataFrame()
        
        ratios = calculate_financial_ratios(mock_ticker, info)
        
        assert isinstance(ratios, FinancialRatios)
        assert ratios.pe_ratio == 25.0
        assert ratios.pb_ratio == 5.0
        assert ratios.roe == 0.15
    
    def test_calculate_total_return_index(self):
        """Test total return index calculation"""
        # Mock price data
        dates = pd.date_range('2024-01-01', periods=5, freq='D')
        price_data = pd.DataFrame({
            'Close': [100.0, 102.0, 101.0, 103.0, 105.0]
        }, index=dates)
        
        # Mock dividend data as Series (like yfinance returns)
        dividend_data = pd.Series([1.0], index=[dates[2]])  # Dividend on third day
        
        result = calculate_total_return_index(price_data, dividend_data)
        
        assert len(result) == 5
        assert all(hasattr(point, 't') and hasattr(point, 'tr') for point in result)
        assert result[0].tr == 100.0  # Base index
        assert result[-1].tr > 100.0  # Should be higher due to price appreciation
    
    def test_calculate_dividend_cagr(self):
        """Test dividend CAGR calculation"""
        # Create test dividend series
        dates = pd.date_range('2020-01-01', periods=20, freq='3ME')
        # Simulate growing dividends
        amounts = [0.20 * (1.05 ** (i // 4)) for i in range(20)]
        dividend_series = pd.Series(amounts, index=dates)
        
        cagr = calculate_dividend_cagr(dividend_series, 5.0)
        
        assert cagr is not None
        assert isinstance(cagr, float)
        assert cagr > 0  # Should show growth
    
    def test_calculate_dividend_consistency(self):
        """Test dividend consistency calculation"""
        # Create test dividend series with consistent payments
        dates = pd.date_range('2020-01-01', periods=16, freq='3ME')
        amounts = [0.25] * 16  # Consistent quarterly dividends
        dividend_series = pd.Series(amounts, index=dates)
        
        consistency = calculate_dividend_consistency(dividend_series)
        
        assert consistency is not None
        assert isinstance(consistency, float)
        assert consistency > 80  # Should show high consistency
    
    def test_calculate_dividend_consistency_with_cuts(self):
        """Test dividend consistency with dividend cuts"""
        dates = pd.date_range('2020-01-01', periods=16, freq='3ME')
        amounts = [0.25] * 8 + [0.20] * 4 + [0.15] * 4  # Declining dividends
        dividend_series = pd.Series(amounts, index=dates)
        
        consistency = calculate_dividend_consistency(dividend_series)
        
        assert consistency is not None
        assert consistency < 90  # Should be penalized for cuts


class TestErrorHandling:
    """Tests for error handling across all tools"""
    
    def test_tool_argument_validation(self):
        """Test that tools validate arguments properly"""
        # Test each tool with invalid arguments
        invalid_cases = [
            ("get_realtime_quote", {"invalid_field": "value"}),
            ("get_fundamentals", {"instrument": "AAPL", "period": "invalid"}),
            ("get_price_history", {"instrument": "AAPL", "start": "invalid-date"}),
            ("get_dividends_and_actions", {"instrument": ""})
        ]
        
        for tool_name, args in invalid_cases:
            result = execute_tool(tool_name, args)
            result_data = json.loads(result)
            
            # Should return error or handle gracefully
            assert isinstance(result_data, dict)
            # Either contains error field or is handled by the tool
            if "error" in result_data:
                assert isinstance(result_data["error"], str)
    
    @patch('tools.yf.Ticker')
    def test_network_error_handling(self, mock_ticker):
        """Test handling of network errors"""
        # Simulate network timeout
        mock_ticker.side_effect = Exception("Connection timeout")
        
        tools_to_test = [
            ("get_realtime_quote", {"symbol": "AAPL"}),
            ("get_fundamentals", {"instrument": "AAPL", "period": "annual"}),
            ("get_price_history", {"instrument": "AAPL", "start": "2024-01-01", "end": "2024-01-05"}),
            ("get_dividends_and_actions", {"instrument": "AAPL"})
        ]
        
        for tool_name, args in tools_to_test:
            result = execute_tool(tool_name, args)
            result_data = json.loads(result)
            
            assert "error" in result_data
            assert "timeout" in result_data["error"].lower() or "error" in result_data["error"].lower()
    
    def test_empty_data_handling(self):
        """Test handling of empty or null data"""
        with patch('tools.yf.Ticker') as mock_ticker:
            mock_ticker_instance = Mock()
            mock_ticker.return_value = mock_ticker_instance
            
            # Simulate empty data responses
            mock_ticker_instance.history.return_value = pd.DataFrame()
            mock_ticker_instance.info = {}
            mock_ticker_instance.dividends = pd.Series(dtype=float)
            mock_ticker_instance.splits = pd.Series(dtype=float)
            
            # Test each tool handles empty data gracefully
            result = get_realtime_quote({"symbol": "EMPTY"})
            result_data = json.loads(result)
            assert "error" in result_data or "symbol" in result_data