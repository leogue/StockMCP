from fastapi import FastAPI, Request
from mcp_handlers import handle_mcp_request


app = FastAPI(
    title="StockMCP Server",
    description="Model Context Protocol server for stock market data",
    version="0.1.0"
)


@app.post("/api/mcp")
async def mcp_endpoint(request: Request):
    """Main MCP endpoint for handling JSON-RPC requests"""
    request_data = await request.json()
    response_data = handle_mcp_request(request_data)
    return response_data


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "stockmcp"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)

