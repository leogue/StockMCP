import pytest
from pydantic import ValidationError
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models import (
    JsonRpcRequest, JsonRpcResponse, MCPCapabilities, MCPServerInfo,
    MCPInitializeResult, MCPToolInputSchema, MCPTool, MCPToolsListResult,
    MCPToolCallParams, MCPContent, MCPToolCallResult, StockQuote,
    FinancialRatios, StockFundamentals, PriceBar, TotalReturnPoint
)


class TestJsonRpcModels:
    """Tests for JSON-RPC request/response models"""
    
    def test_jsonrpc_request_valid(self):
        """Test valid JSON-RPC request creation"""
        request = JsonRpcRequest(
            id=1,
            method="tools/list"
        )
        assert request.jsonrpc == "2.0"
        assert request.id == 1
        assert request.method == "tools/list"
        assert request.params is None
    
    def test_jsonrpc_request_with_params(self):
        """Test JSON-RPC request with parameters"""
        params = {"name": "get_realtime_quote", "arguments": {"symbol": "AAPL"}}
        request = JsonRpcRequest(
            id=2,
            method="tools/call",
            params=params
        )
        assert request.params == params
    
    def test_jsonrpc_request_string_id(self):
        """Test JSON-RPC request with string ID"""
        request = JsonRpcRequest(
            id="test-123",
            method="initialize"
        )
        assert request.id == "test-123"
    
    def test_jsonrpc_response_with_result(self):
        """Test JSON-RPC response with result"""
        result = {"tools": []}
        response = JsonRpcResponse(
            id=1,
            result=result
        )
        assert response.jsonrpc == "2.0"
        assert response.id == 1
        assert response.result == result
        assert response.error is None
    
    def test_jsonrpc_response_with_error(self):
        """Test JSON-RPC response with error"""
        error = {"code": -32601, "message": "Method not found"}
        response = JsonRpcResponse(
            id=1,
            error=error
        )
        assert response.error == error
        assert response.result is None


class TestMCPModels:
    """Tests for MCP protocol models"""
    
    def test_mcp_capabilities(self):
        """Test MCP capabilities model"""
        capabilities = MCPCapabilities()
        assert capabilities.tools == {"listChanged": False}
        assert capabilities.resources == {}
    
    def test_mcp_server_info(self):
        """Test MCP server info model"""
        server_info = MCPServerInfo(name="stockmcp-server", version="0.1.0")
        assert server_info.name == "stockmcp-server"
        assert server_info.version == "0.1.0"
    
    def test_mcp_initialize_result(self):
        """Test MCP initialize result model"""
        capabilities = MCPCapabilities()
        server_info = MCPServerInfo(name="test-server", version="1.0.0")
        result = MCPInitializeResult(
            capabilities=capabilities,
            serverInfo=server_info
        )
        assert result.protocolVersion == "2025-06-18"
        assert result.capabilities == capabilities
        assert result.serverInfo == server_info
    
    def test_mcp_tool_input_schema(self):
        """Test MCP tool input schema model"""
        schema = MCPToolInputSchema(
            properties={"symbol": {"type": "string"}},
            required=["symbol"]
        )
        assert schema.type == "object"
        assert schema.properties == {"symbol": {"type": "string"}}
        assert schema.required == ["symbol"]
    
    def test_mcp_tool(self):
        """Test MCP tool model"""
        schema = MCPToolInputSchema(
            properties={"symbol": {"type": "string"}},
            required=["symbol"]
        )
        tool = MCPTool(
            name="get_realtime_quote",
            title="Real-time Stock Quote",
            description="Get stock quote",
            inputSchema=schema
        )
        assert tool.name == "get_realtime_quote"
        assert tool.title == "Real-time Stock Quote"
        assert tool.description == "Get stock quote"
        assert tool.inputSchema == schema
    
    def test_mcp_tools_list_result(self):
        """Test MCP tools list result model"""
        schema = MCPToolInputSchema(
            properties={"symbol": {"type": "string"}},
            required=["symbol"]
        )
        tool = MCPTool(
            name="test_tool",
            title="Test Tool",
            description="Test",
            inputSchema=schema
        )
        result = MCPToolsListResult(tools=[tool])
        assert len(result.tools) == 1
        assert result.tools[0] == tool
    
    def test_mcp_tool_call_params(self):
        """Test MCP tool call parameters model"""
        params = MCPToolCallParams(
            name="get_realtime_quote",
            arguments={"symbol": "AAPL"}
        )
        assert params.name == "get_realtime_quote"
        assert params.arguments == {"symbol": "AAPL"}
    
    def test_mcp_content(self):
        """Test MCP content model"""
        content = MCPContent(type="text", text="Test content")
        assert content.type == "text"
        assert content.text == "Test content"
    
    def test_mcp_tool_call_result(self):
        """Test MCP tool call result model"""
        content = MCPContent(type="text", text="Result")
        result = MCPToolCallResult(content=[content])
        assert len(result.content) == 1
        assert result.content[0] == content


class TestStockModels:
    """Tests for stock data models"""
    
    def test_stock_quote_minimal(self):
        """Test stock quote with minimal required data"""
        quote = StockQuote(symbol="AAPL")
        assert quote.symbol == "AAPL"
        assert quote.currency == "USD"  # default value
        assert quote.price is None
        assert quote.change is None
    
    def test_stock_quote_complete(self):
        """Test stock quote with all fields"""
        quote = StockQuote(
            symbol="AAPL",
            price=150.50,
            change=2.30,
            change_percent=1.55,
            volume=45000000,
            market_cap=2500000000000,
            pe_ratio=28.5,
            dividend_yield=0.0065,
            fifty_two_week_high=180.25,
            fifty_two_week_low=120.75,
            currency="USD"
        )
        assert quote.symbol == "AAPL"
        assert quote.price == 150.50
        assert quote.change == 2.30
        assert quote.change_percent == 1.55
        assert quote.volume == 45000000
        assert quote.market_cap == 2500000000000
        assert quote.pe_ratio == 28.5
        assert quote.dividend_yield == 0.0065
        assert quote.fifty_two_week_high == 180.25
        assert quote.fifty_two_week_low == 120.75
        assert quote.currency == "USD"
    
    def test_financial_ratios(self):
        """Test financial ratios model"""
        ratios = FinancialRatios(
            pe_ratio=25.5,
            pb_ratio=5.2,
            roe=0.15,
            debt_to_equity=0.3
        )
        assert ratios.pe_ratio == 25.5
        assert ratios.pb_ratio == 5.2
        assert ratios.roe == 0.15
        assert ratios.debt_to_equity == 0.3
        # Check default None values
        assert ratios.ps_ratio is None
        assert ratios.roic is None
    
    def test_price_bar(self):
        """Test price bar model"""
        bar = PriceBar(
            t="2024-01-15",
            o=150.0,
            h=152.5,
            l=149.0,
            c=151.25,
            v=25000000
        )
        assert bar.t == "2024-01-15"
        assert bar.o == 150.0
        assert bar.h == 152.5
        assert bar.l == 149.0
        assert bar.c == 151.25
        assert bar.v == 25000000
    
    def test_price_bar_with_none_values(self):
        """Test price bar with None values (gaps in data)"""
        bar = PriceBar(
            t="2024-01-15",
            o=None,
            h=None,
            l=None,
            c=150.0,
            v=None
        )
        assert bar.t == "2024-01-15"
        assert bar.o is None
        assert bar.c == 150.0
        assert bar.v is None
    
    def test_total_return_point(self):
        """Test total return point model"""
        point = TotalReturnPoint(t="2024-01-15", tr=105.25)
        assert point.t == "2024-01-15"
        assert point.tr == 105.25


class TestModelValidation:
    """Tests for model validation and error handling"""
    
    def test_jsonrpc_request_missing_method(self):
        """Test JSON-RPC request validation with missing method"""
        with pytest.raises(ValidationError) as exc_info:
            JsonRpcRequest(id=1)
        
        error = exc_info.value
        assert "method" in str(error)
    
    def test_jsonrpc_request_missing_id(self):
        """Test JSON-RPC request validation with missing id"""
        with pytest.raises(ValidationError) as exc_info:
            JsonRpcRequest(method="tools/list")
        
        error = exc_info.value
        assert "id" in str(error)
    
    def test_mcp_tool_missing_required_fields(self):
        """Test MCP tool validation with missing required fields"""
        with pytest.raises(ValidationError) as exc_info:
            MCPTool(name="test")
        
        error = exc_info.value
        assert any(field in str(error) for field in ["title", "description", "inputSchema"])
    
    def test_stock_quote_missing_symbol(self):
        """Test stock quote validation with missing symbol"""
        with pytest.raises(ValidationError) as exc_info:
            StockQuote()
        
        error = exc_info.value
        assert "symbol" in str(error)
    
    def test_model_serialization(self):
        """Test model serialization to JSON"""
        quote = StockQuote(
            symbol="AAPL",
            price=150.50,
            change=2.30
        )
        
        # Test model_dump
        data = quote.model_dump()
        assert isinstance(data, dict)
        assert data["symbol"] == "AAPL"
        assert data["price"] == 150.50
        
        # Test model_dump_json
        json_str = quote.model_dump_json()
        assert isinstance(json_str, str)
        assert "AAPL" in json_str
        assert "150.5" in json_str
    
    def test_model_deserialization(self):
        """Test model deserialization from dict"""
        data = {
            "symbol": "GOOGL",
            "price": 2800.75,
            "change": -15.25,
            "volume": 1500000
        }
        
        quote = StockQuote(**data)
        assert quote.symbol == "GOOGL"
        assert quote.price == 2800.75
        assert quote.change == -15.25
        assert quote.volume == 1500000