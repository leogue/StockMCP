import pytest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_handlers import (
    handle_initialize, handle_tools_list, handle_tools_call, handle_mcp_request
)
from models import JsonRpcRequest, JsonRpcResponse


class TestMCPHandlers:
    """Tests for MCP request handlers"""
    
    def test_handle_initialize(self):
        """Test MCP initialize handler"""
        request = JsonRpcRequest(id=1, method="initialize")
        response = handle_initialize(request)
        
        assert isinstance(response, JsonRpcResponse)
        assert response.id == 1
        assert response.jsonrpc == "2.0"
        assert response.error is None
        assert response.result is not None
        
        # Check result structure
        result = response.result
        assert "protocolVersion" in result
        assert "capabilities" in result
        assert "serverInfo" in result
        
        # Check server info
        server_info = result["serverInfo"]
        assert server_info["name"] == "stockmcp-server"
        assert server_info["version"] == "0.1.0"
        
        # Check capabilities
        capabilities = result["capabilities"]
        assert "tools" in capabilities
        assert capabilities["tools"]["listChanged"] == False
    
    def test_handle_tools_list(self):
        """Test tools/list handler"""
        request = JsonRpcRequest(id=2, method="tools/list")
        response = handle_tools_list(request)
        
        assert isinstance(response, JsonRpcResponse)
        assert response.id == 2
        assert response.error is None
        assert response.result is not None
        
        # Check result structure
        result = response.result
        assert "tools" in result
        assert isinstance(result["tools"], list)
        assert len(result["tools"]) > 0
        
        # Check first tool structure
        tool = result["tools"][0]
        required_fields = ["name", "title", "description", "inputSchema"]
        for field in required_fields:
            assert field in tool
        
        # Check inputSchema structure
        schema = tool["inputSchema"]
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema
        assert isinstance(schema["properties"], dict)
        assert isinstance(schema["required"], list)
    
    def test_handle_tools_call_get_realtime_quote(self):
        """Test tools/call handler with get_realtime_quote"""
        request = JsonRpcRequest(
            id=3,
            method="tools/call",
            params={
                "name": "get_realtime_quote",
                "arguments": {"symbol": "AAPL"}
            }
        )
        response = handle_tools_call(request)
        
        assert isinstance(response, JsonRpcResponse)
        assert response.id == 3
        assert response.result is not None or response.error is not None
        
        if response.result:
            # Check successful result structure
            result = response.result
            assert "content" in result
            assert isinstance(result["content"], list)
            assert len(result["content"]) > 0
            
            content = result["content"][0]
            assert content["type"] == "text"
            assert "text" in content
            assert isinstance(content["text"], str)
        else:
            # Check error structure if API call failed
            assert response.error is not None
            assert "code" in response.error
            assert "message" in response.error
    
    def test_handle_tools_call_invalid_tool(self):
        """Test tools/call handler with invalid tool name"""
        request = JsonRpcRequest(
            id=4,
            method="tools/call",
            params={
                "name": "invalid_tool",
                "arguments": {}
            }
        )
        response = handle_tools_call(request)
        
        assert isinstance(response, JsonRpcResponse)
        assert response.id == 4
        assert response.result is not None
        
        # The result should contain an error message about the invalid tool
        result = response.result
        assert "content" in result
        content = result["content"][0]
        assert "error" in content["text"] or "not found" in content["text"].lower()
    
    def test_handle_tools_call_no_params(self):
        """Test tools/call handler without parameters"""
        request = JsonRpcRequest(
            id=5,
            method="tools/call"
        )
        response = handle_tools_call(request)
        
        assert isinstance(response, JsonRpcResponse)
        assert response.id == 5
        assert response.error is not None
        assert response.error["code"] == -32602
        assert "params are required" in response.error["message"]
    
    def test_handle_tools_call_invalid_params(self):
        """Test tools/call handler with invalid parameters"""
        request = JsonRpcRequest(
            id=6,
            method="tools/call",
            params={
                "invalid_field": "value"
            }
        )
        response = handle_tools_call(request)
        
        assert isinstance(response, JsonRpcResponse)
        assert response.id == 6
        assert response.error is not None
        assert response.error["code"] == -32603


class TestMCPRequestRouter:
    """Tests for the main MCP request router"""
    
    def test_handle_mcp_request_initialize(self):
        """Test routing initialize request"""
        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize"
        }
        response_data = handle_mcp_request(request_data)
        
        assert isinstance(response_data, dict)
        assert response_data["jsonrpc"] == "2.0"
        assert response_data["id"] == 1
        assert "result" in response_data
        assert response_data.get("error") is None
    
    def test_handle_mcp_request_tools_list(self):
        """Test routing tools/list request"""
        request_data = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        response_data = handle_mcp_request(request_data)
        
        assert isinstance(response_data, dict)
        assert response_data["jsonrpc"] == "2.0"
        assert response_data["id"] == 2
        assert "result" in response_data
        assert "tools" in response_data["result"]
    
    def test_handle_mcp_request_tools_call(self):
        """Test routing tools/call request"""
        request_data = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_realtime_quote",
                "arguments": {"symbol": "AAPL"}
            }
        }
        response_data = handle_mcp_request(request_data)
        
        assert isinstance(response_data, dict)
        assert response_data["jsonrpc"] == "2.0"
        assert response_data["id"] == 3
        assert "result" in response_data or "error" in response_data
    
    def test_handle_mcp_request_unknown_method(self):
        """Test routing unknown method"""
        request_data = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "unknown/method"
        }
        response_data = handle_mcp_request(request_data)
        
        assert isinstance(response_data, dict)
        assert response_data["jsonrpc"] == "2.0"
        assert response_data["id"] == 4
        assert "error" in response_data
        assert response_data["error"]["code"] == -32601
        assert "not found" in response_data["error"]["message"]
    
    def test_handle_mcp_request_invalid_json_rpc(self):
        """Test handling invalid JSON-RPC request"""
        request_data = {
            "invalid": "request"
        }
        response_data = handle_mcp_request(request_data)
        
        assert isinstance(response_data, dict)
        assert response_data["jsonrpc"] == "2.0"
        assert "error" in response_data
        assert response_data["error"]["code"] == -32700
        assert "Parse error" in response_data["error"]["message"]
    
    def test_handle_mcp_request_missing_id(self):
        """Test handling request with missing ID"""
        request_data = {
            "jsonrpc": "2.0",
            "method": "tools/list"
        }
        response_data = handle_mcp_request(request_data)
        
        assert isinstance(response_data, dict)
        assert "error" in response_data
        assert response_data["error"]["code"] == -32700
    
    def test_handle_mcp_request_missing_method(self):
        """Test handling request with missing method"""
        request_data = {
            "jsonrpc": "2.0",
            "id": 1
        }
        response_data = handle_mcp_request(request_data)
        
        assert isinstance(response_data, dict)
        assert "error" in response_data
        assert response_data["error"]["code"] == -32700


class TestMCPResponseFormat:
    """Tests for MCP response format compliance"""
    
    def test_initialize_response_format(self):
        """Test initialize response matches expected MCP format"""
        request_data = {
            "jsonrpc": "2.0",
            "id": "init-1",
            "method": "initialize"
        }
        response_data = handle_mcp_request(request_data)
        
        # Check JSON-RPC 2.0 compliance
        assert response_data["jsonrpc"] == "2.0"
        assert response_data["id"] == "init-1"
        
        # Check MCP initialize format
        result = response_data["result"]
        assert isinstance(result["protocolVersion"], str)
        assert isinstance(result["capabilities"], dict)
        assert isinstance(result["serverInfo"], dict)
        
        # Check server info format
        server_info = result["serverInfo"]
        assert isinstance(server_info["name"], str)
        assert isinstance(server_info["version"], str)
    
    def test_tools_list_response_format(self):
        """Test tools/list response matches expected MCP format"""
        request_data = {
            "jsonrpc": "2.0",
            "id": "list-1",
            "method": "tools/list"
        }
        response_data = handle_mcp_request(request_data)
        
        # Check JSON-RPC 2.0 compliance
        assert response_data["jsonrpc"] == "2.0"
        assert response_data["id"] == "list-1"
        
        # Check tools list format
        result = response_data["result"]
        assert "tools" in result
        tools = result["tools"]
        assert isinstance(tools, list)
        
        for tool in tools:
            # Each tool should have required fields
            assert isinstance(tool["name"], str)
            assert isinstance(tool["title"], str)
            assert isinstance(tool["description"], str)
            assert isinstance(tool["inputSchema"], dict)
            
            # Check inputSchema format
            schema = tool["inputSchema"]
            assert schema["type"] == "object"
            assert isinstance(schema["properties"], dict)
            assert isinstance(schema["required"], list)
    
    def test_tools_call_response_format(self):
        """Test tools/call response matches expected MCP format"""
        request_data = {
            "jsonrpc": "2.0",
            "id": "call-1",
            "method": "tools/call",
            "params": {
                "name": "get_realtime_quote",
                "arguments": {"symbol": "AAPL"}
            }
        }
        response_data = handle_mcp_request(request_data)
        
        # Check JSON-RPC 2.0 compliance
        assert response_data["jsonrpc"] == "2.0"
        assert response_data["id"] == "call-1"
        
        # Should have either result or error, not both
        has_result = "result" in response_data
        has_error = "error" in response_data
        assert has_result or has_error
        assert not (has_result and has_error)
        
        if has_result:
            # Check content format
            result = response_data["result"]
            assert "content" in result
            content_list = result["content"]
            assert isinstance(content_list, list)
            
            for content in content_list:
                assert isinstance(content["type"], str)
                assert "text" in content
    
    def test_error_response_format(self):
        """Test error response matches JSON-RPC 2.0 format"""
        request_data = {
            "jsonrpc": "2.0",
            "id": "error-1",
            "method": "nonexistent/method"
        }
        response_data = handle_mcp_request(request_data)
        
        # Check JSON-RPC 2.0 compliance
        assert response_data["jsonrpc"] == "2.0"
        assert response_data["id"] == "error-1"
        
        # Check error format
        assert "error" in response_data
        assert "result" not in response_data
        
        error = response_data["error"]
        assert isinstance(error["code"], int)
        assert isinstance(error["message"], str)
        
        # Check error code is valid JSON-RPC error code
        assert error["code"] in [-32700, -32600, -32601, -32602, -32603] or error["code"] < -32000