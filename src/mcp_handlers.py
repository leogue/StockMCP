from models import (
    JsonRpcRequest, JsonRpcResponse, MCPInitializeResult, 
    MCPCapabilities, MCPServerInfo, MCPToolsListResult,
    MCPToolCallParams, MCPToolCallResult, MCPContent
)
from tools import get_available_tools, execute_tool
from typing import Dict, Any
import logging


def handle_initialize(request: JsonRpcRequest) -> JsonRpcResponse:
    """Handle MCP initialize request"""
    logging.info("Handling MCP initialize request")
    
    capabilities = MCPCapabilities()
    server_info = MCPServerInfo(name="stockmcp-server", version="0.1.0")
    
    result = MCPInitializeResult(
        capabilities=capabilities,
        serverInfo=server_info
    )
    
    return JsonRpcResponse(
        id=request.id,
        result=result.model_dump()
    )


def handle_tools_list(request: JsonRpcRequest) -> JsonRpcResponse:
    """Handle tools/list request"""
    logging.debug("Handling tools/list request")
    
    tools = get_available_tools()
    logging.debug(f"Returning {len(tools)} available tools")
    result = MCPToolsListResult(tools=tools)
    
    return JsonRpcResponse(
        id=request.id,
        result=result.model_dump()
    )


def handle_tools_call(request: JsonRpcRequest) -> JsonRpcResponse:
    """Handle tools/call request"""
    try:
        if not request.params:
            return JsonRpcResponse(
                id=request.id,
                error={
                    "code": -32602,
                    "message": "Invalid params: params are required for tool calls"
                }
            )
        
        # Validate tool call parameters
        tool_params = MCPToolCallParams(**request.params)
        logging.info(f"Executing tool: {tool_params.name} with arguments: {tool_params.arguments}")
        
        # Execute the tool
        tool_result = execute_tool(tool_params.name, tool_params.arguments)
        logging.debug(f"Tool {tool_params.name} execution completed")
        
        # Create response content
        content = MCPContent(type="text", text=tool_result)
        result = MCPToolCallResult(content=[content])
        
        return JsonRpcResponse(
            id=request.id,
            result=result.model_dump()
        )
        
    except Exception as e:
        logging.error(f"Error executing tool call: {str(e)}")
        return JsonRpcResponse(
            id=request.id,
            error={
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        )


def handle_mcp_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle incoming MCP request and route to appropriate handler
    
    Args:
        request_data: Raw request data from HTTP
    
    Returns:
        Response data dictionary
    """
    try:
        # Validate and parse request
        request = JsonRpcRequest(**request_data)
        logging.debug(f"Routing MCP method: {request.method}")
        
        # Route to appropriate handler
        if request.method == "initialize":
            response = handle_initialize(request)
        elif request.method == "tools/list":
            response = handle_tools_list(request)
        elif request.method == "tools/call":
            response = handle_tools_call(request)
        else:
            logging.warning(f"Unknown MCP method requested: {request.method}")
            response = JsonRpcResponse(
                id=request.id,
                error={
                    "code": -32601,
                    "message": f"Method '{request.method}' not found"
                }
            )
        
        return response.model_dump(exclude_none=True)
        
    except Exception as e:
        # Handle validation or other errors
        logging.error(f"Error handling MCP request: {str(e)}")
        return JsonRpcResponse(
            id=request_data.get("id", 0),
            error={
                "code": -32700,
                "message": f"Parse error: {str(e)}"
            }
        ).model_dump(exclude_none=True)