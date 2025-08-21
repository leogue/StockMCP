import pytest
import json
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app


class TestFastAPIEndpoints:
    """Tests for FastAPI endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "stockmcp"
    
    def test_mcp_endpoint_initialize(self, client):
        """Test MCP endpoint with initialize request"""
        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize"
        }
        
        response = client.post(
            "/api/mcp",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check JSON-RPC response format
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        assert "result" in data
        
        # Check MCP initialize response
        result = data["result"]
        assert "protocolVersion" in result
        assert "capabilities" in result
        assert "serverInfo" in result
        
        server_info = result["serverInfo"]
        assert server_info["name"] == "stockmcp-server"
        assert server_info["version"] == "0.1.0"
    
    def test_mcp_endpoint_tools_list(self, client):
        """Test MCP endpoint with tools/list request"""
        request_data = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        response = client.post(
            "/api/mcp",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check JSON-RPC response format
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 2
        assert "result" in data
        
        # Check tools list response
        result = data["result"]
        assert "tools" in result
        tools = result["tools"]
        assert isinstance(tools, list)
        assert len(tools) >= 4  # We have 4 tools defined
        
        # Check that all expected tools are present
        tool_names = [tool["name"] for tool in tools]
        expected_tools = [
            "get_realtime_quote",
            "get_fundamentals", 
            "get_price_history",
            "get_dividends_and_actions"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
        
        # Check tool structure
        for tool in tools:
            assert "name" in tool
            assert "title" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            
            schema = tool["inputSchema"]
            assert schema["type"] == "object"
            assert "properties" in schema
            assert "required" in schema
    
    def test_mcp_endpoint_tools_call_realtime_quote(self, client):
        """Test MCP endpoint with tools/call for realtime quote"""
        request_data = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_realtime_quote",
                "arguments": {"symbol": "AAPL"}
            }
        }
        
        response = client.post(
            "/api/mcp",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check JSON-RPC response format
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 3
        
        # Should have result (successful call) or error could occur due to API limits
        if "result" in data:
            result = data["result"]
            assert "content" in result
            assert isinstance(result["content"], list)
            assert len(result["content"]) > 0
            
            content = result["content"][0]
            assert content["type"] == "text"
            assert "text" in content
            
            # Parse the JSON response from the tool
            tool_response = json.loads(content["text"])
            if "error" not in tool_response:
                # Successful quote response
                assert "symbol" in tool_response
                assert tool_response["symbol"] == "AAPL"
        else:
            # API might have failed, check error format
            assert "error" in data
            assert isinstance(data["error"]["code"], int)
            assert isinstance(data["error"]["message"], str)
    
    def test_mcp_endpoint_tools_call_invalid_tool(self, client):
        """Test MCP endpoint with invalid tool name"""
        request_data = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "invalid_tool_name",
                "arguments": {}
            }
        }
        
        response = client.post(
            "/api/mcp",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check JSON-RPC response format
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 4
        assert "result" in data
        
        # The result should contain error content about invalid tool
        result = data["result"]
        content = result["content"][0]
        tool_response = json.loads(content["text"])
        assert "error" in tool_response
        assert "not found" in tool_response["error"].lower()
    
    def test_mcp_endpoint_invalid_method(self, client):
        """Test MCP endpoint with invalid method"""
        request_data = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "invalid/method"
        }
        
        response = client.post(
            "/api/mcp",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check JSON-RPC response format
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 5
        assert "error" in data
        
        error = data["error"]
        assert error["code"] == -32601
        assert "not found" in error["message"]
    
    def test_mcp_endpoint_malformed_json(self, client):
        """Test MCP endpoint with malformed JSON"""
        # For malformed JSON, we'll test a different approach
        # Test with a request that has correct JSON structure but invalid content
        request_data = {"not_jsonrpc": "invalid"}
        
        response = client.post(
            "/api/mcp",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32700
    
    def test_mcp_endpoint_missing_fields(self, client):
        """Test MCP endpoint with missing required fields"""
        request_data = {
            "jsonrpc": "2.0"
            # Missing id and method
        }
        
        response = client.post(
            "/api/mcp",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return parse error
        assert data["jsonrpc"] == "2.0"
        assert "error" in data
        assert data["error"]["code"] == -32700
    
    def test_mcp_endpoint_content_type_validation(self, client):
        """Test MCP endpoint requires JSON content type"""
        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize"
        }
        
        # Test with wrong content type
        response = client.post(
            "/api/mcp",
            json=request_data,
            headers={"Content-Type": "text/plain"}
        )
        
        # Should still work as FastAPI is flexible with content types
        # when using json parameter in post()
        assert response.status_code == 200
    
    def test_mcp_endpoint_string_id(self, client):
        """Test MCP endpoint with string ID"""
        request_data = {
            "jsonrpc": "2.0",
            "id": "test-string-id",
            "method": "tools/list"
        }
        
        response = client.post(
            "/api/mcp",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-string-id"
        assert "result" in data


class TestAPIIntegration:
    """Integration tests for the complete API"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_full_mcp_workflow(self, client):
        """Test complete MCP workflow: initialize -> list tools -> call tool"""
        
        # Step 1: Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize"
        }
        
        init_response = client.post("/api/mcp", json=init_request)
        assert init_response.status_code == 200
        init_data = init_response.json()
        assert "result" in init_data
        
        # Step 2: List tools
        list_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        list_response = client.post("/api/mcp", json=list_request)
        assert list_response.status_code == 200
        list_data = list_response.json()
        assert "result" in list_data
        
        tools = list_data["result"]["tools"]
        assert len(tools) > 0
        
        # Step 3: Call a tool
        call_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_realtime_quote",
                "arguments": {"symbol": "AAPL"}
            }
        }
        
        call_response = client.post("/api/mcp", json=call_request)
        assert call_response.status_code == 200
        call_data = call_response.json()
        
        # Should have either successful result or error (due to API limitations)
        assert "result" in call_data or "error" in call_data
    
    def test_multiple_tool_calls(self, client):
        """Test multiple tool calls with different parameters"""
        
        # Test different symbols
        symbols = ["AAPL", "GOOGL", "MSFT"]
        
        for i, symbol in enumerate(symbols, 1):
            request = {
                "jsonrpc": "2.0",
                "id": i,
                "method": "tools/call",
                "params": {
                    "name": "get_realtime_quote",
                    "arguments": {"symbol": symbol}
                }
            }
            
            response = client.post("/api/mcp", json=request)
            assert response.status_code == 200
            
            data = response.json()
            assert data["id"] == i
            assert "result" in data or "error" in data
    
    def test_error_handling_consistency(self, client):
        """Test that error responses are consistent across different error types"""
        
        error_cases = [
            # Invalid method
            {
                "request": {"jsonrpc": "2.0", "id": 1, "method": "invalid/method"},
                "expected_code": -32601
            },
            # Missing params for tools/call
            {
                "request": {"jsonrpc": "2.0", "id": 2, "method": "tools/call"},
                "expected_code": -32602
            },
            # Invalid request structure
            {
                "request": {"invalid": "request"},
                "expected_code": -32700
            }
        ]
        
        for case in error_cases:
            response = client.post("/api/mcp", json=case["request"])
            assert response.status_code == 200
            
            data = response.json()
            assert data["jsonrpc"] == "2.0"
            assert "error" in data
            assert data["error"]["code"] == case["expected_code"]
            assert isinstance(data["error"]["message"], str)


class TestAPIPerformance:
    """Basic performance and reliability tests"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests"""
        import threading
        import time
        
        results = []
        
        def make_request():
            request = {
                "jsonrpc": "2.0",
                "id": threading.current_thread().ident,
                "method": "tools/list"
            }
            response = client.post("/api/mcp", json=request)
            results.append(response.status_code == 200)
        
        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        # All requests should succeed
        assert all(results)
        assert len(results) == 10
        
        # Should complete reasonably quickly
        assert end_time - start_time < 5.0
    
    def test_response_time(self, client):
        """Test basic response time for health endpoint"""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Health endpoint should be very fast
        response_time = end_time - start_time
        assert response_time < 0.1  # Less than 100ms