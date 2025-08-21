from fastapi import FastAPI, Request
from mcp_handlers import handle_mcp_request
import logging


app = FastAPI(
    title="StockMCP Server",
    description="Model Context Protocol server for stock market data",
    version="0.1.0"
)


@app.post("/api/mcp")
async def mcp_endpoint(request: Request):
    """Main MCP endpoint for handling JSON-RPC requests"""
    try:
        request_data = await request.json()
        logging.debug(f"Received MCP request: {request_data.get('method', 'unknown')}")
        response_data = handle_mcp_request(request_data)
        logging.debug(f"Sending MCP response for method: {request_data.get('method', 'unknown')}")
        return response_data
    except Exception as e:
        logging.error(f"Error processing MCP request: {str(e)}")
        raise


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logging.debug("Health check endpoint accessed")
    return {"status": "healthy", "service": "stockmcp"}


if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    port = 3001
    logging.info(f"Starting StockMCP server on host 0.0.0.0, port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

