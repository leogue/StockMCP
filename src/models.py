from pydantic import BaseModel
from typing import Any, Dict, List, Optional, Union


class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[str, int]
    method: str
    params: Optional[Dict[str, Any]] = None


class JsonRpcResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[str, int]
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class MCPCapabilities(BaseModel):
    tools: Dict[str, Any] = {"listChanged": False}
    resources: Dict[str, Any] = {}


class MCPServerInfo(BaseModel):
    name: str
    version: str


class MCPInitializeResult(BaseModel):
    protocolVersion: str = "2025-06-18"
    capabilities: MCPCapabilities
    serverInfo: MCPServerInfo


class MCPToolInputSchema(BaseModel):
    type: str = "object"
    properties: Dict[str, Any]
    required: List[str]


class MCPTool(BaseModel):
    name: str
    title: str
    description: str
    inputSchema: MCPToolInputSchema


class MCPToolsListResult(BaseModel):
    tools: List[MCPTool]


class MCPToolCallParams(BaseModel):
    name: str
    arguments: Dict[str, Any]


class MCPContent(BaseModel):
    type: str
    text: str


class MCPToolCallResult(BaseModel):
    content: List[MCPContent]


class StockQuote(BaseModel):
    symbol: str
    price: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[int] = None
    market_cap: Optional[int] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    currency: Optional[str] = "USD"


class FinancialStatement(BaseModel):
    """Base financial statement model"""
    period_ending: Optional[str]
    currency: Optional[str]
    data: Dict[str, Optional[float]]


class IncomeStatement(FinancialStatement):
    """Income statement specific fields"""
    pass


class BalanceSheet(FinancialStatement):
    """Balance sheet specific fields"""
    pass


class CashFlowStatement(FinancialStatement):
    """Cash flow statement specific fields"""
    pass


class FinancialRatios(BaseModel):
    """Financial ratios calculated from statements"""
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    ps_ratio: Optional[float] = None
    ev_ebitda: Optional[float] = None
    roe: Optional[float] = None
    roic: Optional[float] = None
    fcf_yield: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    asset_turnover: Optional[float] = None
    dividend_payout_ratio: Optional[float] = None


class FundamentalsMetadata(BaseModel):
    """Metadata for fundamentals response"""
    currency: Optional[str]
    as_of: Optional[str]
    period_type: str
    years_requested: int


class StockFundamentals(BaseModel):
    """Complete fundamentals response"""
    symbol: str
    income: List[IncomeStatement]
    balance: List[BalanceSheet]
    cashflow: List[CashFlowStatement]
    ratios: FinancialRatios
    meta: FundamentalsMetadata


class PriceBar(BaseModel):
    """Individual price bar (OHLCV)"""
    t: str  # timestamp
    o: Optional[float]  # open
    h: Optional[float]  # high
    l: Optional[float]  # low
    c: Optional[float]  # close
    v: Optional[int]    # volume


class TotalReturnPoint(BaseModel):
    """Total return data point"""
    t: str              # timestamp
    tr: Optional[float] # total return index


class PriceAdjustments(BaseModel):
    """Stock adjustments information"""
    splits: Dict[str, float] = {}
    dividends: Dict[str, float] = {}
    stock_splits: Dict[str, float] = {}


class PriceHistory(BaseModel):
    """Complete price history response"""
    symbol: str
    bars: List[PriceBar]
    total_return: List[TotalReturnPoint]
    adjustments: PriceAdjustments
    tz: str
    interval: str
    start_date: str
    end_date: str


class DividendRecord(BaseModel):
    """Individual dividend record"""
    ex_date: str
    amount: float
    currency: str = "USD"


class DividendYield(BaseModel):
    """Dividend yield metrics"""
    ttm: Optional[float] = None      # Trailing twelve months yield
    five_year_avg: Optional[float] = None  # 5-year average yield


class DividendGrowth(BaseModel):
    """Dividend growth metrics"""
    cagr_5y: Optional[float] = None  # 5-year compound annual growth rate
    consistency_score: Optional[float] = None  # Regularity score (0-100)


class CorporateAction(BaseModel):
    """Corporate action record"""
    type: str  # "split", "spinoff", "merger", etc.
    effective_date: str
    factor: Optional[float] = None
    description: Optional[str] = None


class DividendsAndActions(BaseModel):
    """Complete dividends and corporate actions response"""
    symbol: str
    dividends: List[DividendRecord]
    yield_metrics: DividendYield
    growth_metrics: DividendGrowth
    actions: List[CorporateAction]
    period_start: Optional[str] = None
    period_end: Optional[str] = None