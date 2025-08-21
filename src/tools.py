import yfinance as yf
from typing import Dict, Any, List
import json
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from models import (
    MCPTool, MCPToolInputSchema, StockQuote, StockFundamentals,
    IncomeStatement, BalanceSheet, CashFlowStatement, FinancialRatios,
    FundamentalsMetadata, PriceHistory, PriceBar, TotalReturnPoint,
    PriceAdjustments, DividendsAndActions, DividendRecord, DividendYield,
    DividendGrowth, CorporateAction
)


def get_available_tools() -> List[MCPTool]:
    """Return list of available MCP tools"""
    return [
        MCPTool(
            name="get_realtime_quote",
            title="Real-time Stock Quote",
            description="Retrieve current market data for a stock including price, volume, market cap, and key financial ratios. Provides up-to-date trading information essential for market analysis and investment decisions.",
            inputSchema=MCPToolInputSchema(
                type="object",
                properties={
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., 'AAPL' for Apple, 'GOOGL' for Google, 'TSLA' for Tesla)"
                    }
                },
                required=["symbol"]
            )
        ),
        MCPTool(
            name="get_fundamentals",
            title="Financial Statements and Ratios",
            description="Access comprehensive financial data including income statements, balance sheets, cash flow statements, and calculated financial ratios. Essential for fundamental analysis, valuation, and long-term investment research.",
            inputSchema=MCPToolInputSchema(
                type="object",
                properties={
                    "instrument": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., 'AAPL' for Apple, 'MSFT' for Microsoft)"
                    },
                    "period": {
                        "type": "string",
                        "description": "Reporting period for financial statements",
                        "enum": ["annual", "quarterly", "ttm"]
                    },
                    "years": {
                        "type": "integer",
                        "description": "Number of years/periods of historical data to retrieve (default: 5)",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 5
                    }
                },
                required=["instrument", "period"]
            )
        ),
        MCPTool(
            name="get_price_history",
            title="Historical Price Data",
            description="Retrieve historical OHLCV (Open, High, Low, Close, Volume) data with optional total return calculation including reinvested dividends. Ideal for backtesting, technical analysis, and performance measurement.",
            inputSchema=MCPToolInputSchema(
                type="object",
                properties={
                    "instrument": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., 'AAPL' for Apple, 'SPY' for SPDR S&P 500 ETF)"
                    },
                    "start": {
                        "type": "string",
                        "description": "Start date for historical data in YYYY-MM-DD format (e.g., '2023-01-01')",
                        "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
                    },
                    "end": {
                        "type": "string",
                        "description": "End date for historical data in YYYY-MM-DD format (e.g., '2024-12-31')",
                        "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
                    },
                    "interval": {
                        "type": "string",
                        "description": "Data frequency: daily (1d), weekly (1w), or monthly (1m). Note: 1m interval limited to last 30 days",
                        "enum": ["1d", "1w", "1m"],
                        "default": "1d"
                    },
                    "adjusted": {
                        "type": "boolean",
                        "description": "Return split and dividend adjusted prices for accurate historical analysis",
                        "default": True
                    },
                    "include_total_return": {
                        "type": "boolean",
                        "description": "Calculate total return index assuming dividend reinvestment for performance analysis",
                        "default": True
                    }
                },
                required=["instrument", "start", "end"]
            )
        ),
        MCPTool(
            name="get_dividends_and_actions",
            title="Dividend History and Corporate Actions",
            description="Analyze dividend payment history and corporate actions with quality metrics. Includes dividend yield calculations, growth rates, consistency scoring, and stock split information for income-focused investment analysis.",
            inputSchema=MCPToolInputSchema(
                type="object",
                properties={
                    "instrument": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., 'KO' for Coca-Cola, 'JNJ' for Johnson & Johnson)"
                    },
                    "start": {
                        "type": "string",
                        "description": "Start date for dividend history in YYYY-MM-DD format. If not specified, defaults to 10 years ago",
                        "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
                    },
                    "end": {
                        "type": "string",
                        "description": "End date for dividend history in YYYY-MM-DD format. If not specified, defaults to current date",
                        "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
                    }
                },
                required=["instrument"]
            )
        ),
    ]


def get_realtime_quote(arguments: Dict[str, Any]) -> str:
    """
    Get real-time stock quote using yfinance
    
    Args:
        arguments: Dictionary containing 'symbol' key
    
    Returns:
        JSON string with stock data or error message
    """
    try:
        symbol = arguments.get("symbol", "").upper().strip()
        
        if not symbol:
            return json.dumps({
                "error": "Symbol is required",
                "symbol": None
            })
        
        # Get stock data
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period="1d")
        
        if hist.empty:
            return json.dumps({
                "error": f"No data found for symbol '{symbol}'. Are you sure this symbol exists?",
                "symbol": symbol
            })
        
        # Get current price from the latest close
        current_price = hist['Close'].iloc[-1] if not hist.empty else None
        
        # Calculate change from previous close if available
        change = None
        change_percent = None
        if len(hist) > 1:
            prev_close = hist['Close'].iloc[-2]
            change = current_price - prev_close
            change_percent = (change / prev_close) * 100 if prev_close != 0 else None
        
        # Create StockQuote model
        quote = StockQuote(
            symbol=symbol,
            price=float(current_price) if current_price else None,
            change=float(change) if change else None,
            change_percent=float(change_percent) if change_percent else None,
            volume=int(hist['Volume'].iloc[-1]) if not hist.empty and 'Volume' in hist else None,
            market_cap=info.get('marketCap'),
            pe_ratio=info.get('trailingPE'),
            dividend_yield=info.get('dividendYield'),
            fifty_two_week_high=info.get('fiftyTwoWeekHigh'),
            fifty_two_week_low=info.get('fiftyTwoWeekLow'),
            currency=info.get('currency', 'USD')
        )
        
        return quote.model_dump_json(indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Error fetching data for '{symbol}': {str(e)}",
            "symbol": symbol
        })


def calculate_financial_ratios(ticker: yf.Ticker, info: Dict[str, Any]) -> FinancialRatios:
    """Calculate financial ratios from yfinance data"""
    try:
        # Get financial statements
        income_stmt = ticker.financials
        balance_sheet = ticker.balance_sheet
        cashflow_stmt = ticker.cashflow
        
        ratios = FinancialRatios()
        
        # Basic ratios from info
        ratios.pe_ratio = info.get('trailingPE')
        ratios.pb_ratio = info.get('priceToBook')
        ratios.ps_ratio = info.get('priceToSalesTrailing12Months')
        ratios.ev_ebitda = info.get('enterpriseToEbitda')
        ratios.roe = info.get('returnOnEquity')
        ratios.debt_to_equity = info.get('debtToEquity')
        ratios.current_ratio = info.get('currentRatio')
        ratios.quick_ratio = info.get('quickRatio')
        ratios.gross_margin = info.get('grossMargins')
        ratios.operating_margin = info.get('operatingMargins')
        ratios.net_margin = info.get('profitMargins')
        ratios.dividend_payout_ratio = info.get('payoutRatio')
        
        # Calculate additional ratios if data available
        if not income_stmt.empty and not balance_sheet.empty:
            latest_income = income_stmt.iloc[:, 0]
            latest_balance = balance_sheet.iloc[:, 0]
            
            # ROIC calculation
            if 'Net Income' in latest_income.index and 'Total Stockholder Equity' in latest_balance.index and 'Long Term Debt' in latest_balance.index:
                net_income = latest_income.get('Net Income', 0)
                total_equity = latest_balance.get('Total Stockholder Equity', 0)
                long_term_debt = latest_balance.get('Long Term Debt', 0)
                invested_capital = total_equity + long_term_debt
                if invested_capital != 0:
                    ratios.roic = (net_income / invested_capital) * 100
        
        # FCF Yield calculation
        if not cashflow_stmt.empty and info.get('marketCap'):
            latest_cashflow = cashflow_stmt.iloc[:, 0]
            free_cash_flow = latest_cashflow.get('Free Cash Flow')
            market_cap = info.get('marketCap')
            if free_cash_flow and market_cap and market_cap != 0:
                ratios.fcf_yield = (free_cash_flow / market_cap) * 100
        
        # Asset Turnover
        if not income_stmt.empty and not balance_sheet.empty:
            latest_income = income_stmt.iloc[:, 0]
            latest_balance = balance_sheet.iloc[:, 0]
            revenue = latest_income.get('Total Revenue')
            total_assets = latest_balance.get('Total Assets')
            if revenue and total_assets and total_assets != 0:
                ratios.asset_turnover = revenue / total_assets
        
        return ratios
        
    except Exception as e:
        print(f"Error calculating ratios: {str(e)}")
        return FinancialRatios()


def process_financial_statement(df: pd.DataFrame, statement_type: str) -> List[Dict]:
    """Process a financial statement DataFrame into our format"""
    if df.empty:
        return []
    
    statements = []
    for col in df.columns:
        # Convert column name to string date
        period_ending = col.strftime('%Y-%m-%d') if hasattr(col, 'strftime') else str(col)
        
        # Convert data to dictionary with proper handling of NaN values
        data = {}
        for idx in df.index:
            value = df.loc[idx, col]
            if pd.isna(value):
                data[str(idx)] = None
            else:
                try:
                    data[str(idx)] = float(value)
                except (ValueError, TypeError):
                    data[str(idx)] = None
        
        statements.append({
            "period_ending": period_ending,
            "currency": "USD",  # Default, could be extracted from ticker info
            "data": data
        })
    
    return statements


def get_fundamentals(arguments: Dict[str, Any]) -> str:
    """
    Get comprehensive financial fundamentals for a stock
    
    Args:
        arguments: Dictionary containing 'instrument', 'period', and optionally 'years'
    
    Returns:
        JSON string with financial statements and ratios or error message
    """
    try:
        instrument = arguments.get("instrument", "").upper().strip()
        period = arguments.get("period", "annual").lower()
        years = arguments.get("years", 5)
        
        if not instrument:
            return json.dumps({
                "error": "Instrument (ticker symbol) is required",
                "instrument": None
            })
        
        if period not in ["annual", "quarterly", "ttm"]:
            return json.dumps({
                "error": "Period must be one of: annual, quarterly, ttm",
                "instrument": instrument
            })
        
        # Get ticker data
        ticker = yf.Ticker(instrument)
        info = ticker.info
        
        # Get financial statements based on period
        if period == "annual":
            income_stmt = ticker.financials
            balance_sheet = ticker.balance_sheet
            cashflow_stmt = ticker.cashflow
        elif period == "quarterly":
            income_stmt = ticker.quarterly_financials
            balance_sheet = ticker.quarterly_balance_sheet
            cashflow_stmt = ticker.quarterly_cashflow
        else:  # ttm
            # For TTM, use the most recent annual data
            income_stmt = ticker.financials
            balance_sheet = ticker.balance_sheet
            cashflow_stmt = ticker.cashflow
        
        # Limit to requested number of years/periods
        if not income_stmt.empty and income_stmt.shape[1] > years:
            income_stmt = income_stmt.iloc[:, :years]
        if not balance_sheet.empty and balance_sheet.shape[1] > years:
            balance_sheet = balance_sheet.iloc[:, :years]
        if not cashflow_stmt.empty and cashflow_stmt.shape[1] > years:
            cashflow_stmt = cashflow_stmt.iloc[:, :years]
        
        # Process financial statements
        income_statements = process_financial_statement(income_stmt, "income")
        balance_sheets = process_financial_statement(balance_sheet, "balance")
        cashflow_statements = process_financial_statement(cashflow_stmt, "cashflow")
        
        # Calculate ratios
        ratios = calculate_financial_ratios(ticker, info)
        
        # Create metadata
        meta = FundamentalsMetadata(
            currency=info.get('currency', 'USD'),
            as_of=datetime.now().strftime('%Y-%m-%d'),
            period_type=period,
            years_requested=years
        )
        
        # Create the complete fundamentals response
        fundamentals = StockFundamentals(
            symbol=instrument,
            income=[IncomeStatement(**stmt) for stmt in income_statements],
            balance=[BalanceSheet(**stmt) for stmt in balance_sheets],
            cashflow=[CashFlowStatement(**stmt) for stmt in cashflow_statements],
            ratios=ratios,
            meta=meta
        )
        
        return fundamentals.model_dump_json(indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Error fetching fundamentals for '{instrument}': {str(e)}",
            "instrument": instrument
        })


def calculate_total_return_index(price_data: pd.DataFrame, dividends: pd.DataFrame) -> List[TotalReturnPoint]:
    """
    Calculate total return index with dividends reinvested
    
    Args:
        price_data: DataFrame with price history (Close column)
        dividends: DataFrame with dividend payments
    
    Returns:
        List of TotalReturnPoint objects
    """
    if price_data.empty:
        return []
    
    total_return_data = []
    
    # Start with base index of 100
    tr_index = 100.0
    prev_close = None
    
    for date, row in price_data.iterrows():
        close_price = row['Close']
        
        if pd.isna(close_price):
            continue
            
        if prev_close is not None:
            # Calculate price return
            price_return = (close_price / prev_close) - 1
            
            # Check for dividends on this date
            dividend_yield = 0.0
            if not dividends.empty and date in dividends.index:
                dividend_amount = dividends.loc[date]  # dividends is a Series, not DataFrame
                if not pd.isna(dividend_amount) and dividend_amount > 0:
                    dividend_yield = dividend_amount / prev_close
            
            # Update total return index
            tr_index = tr_index * (1 + price_return + dividend_yield)
        
        total_return_data.append(TotalReturnPoint(
            t=date.strftime('%Y-%m-%d'),
            tr=round(tr_index, 4)
        ))
        
        prev_close = close_price
    
    return total_return_data


def get_price_history(arguments: Dict[str, Any]) -> str:
    """
    Get historical price data with optional total return calculation
    
    Args:
        arguments: Dictionary containing price history parameters
    
    Returns:
        JSON string with price history data or error message
    """
    try:
        instrument = arguments.get("instrument", "").upper().strip()
        start = arguments.get("start")
        end = arguments.get("end")
        interval = arguments.get("interval", "1d")
        adjusted = arguments.get("adjusted", True)
        include_total_return = arguments.get("include_total_return", True)
        
        if not instrument:
            return json.dumps({
                "error": "Instrument (ticker symbol) is required",
                "instrument": None
            })
        
        if not start or not end:
            return json.dumps({
                "error": "Both start and end dates are required (YYYY-MM-DD format)",
                "instrument": instrument
            })
        
        if interval not in ["1d", "1w", "1m"]:
            return json.dumps({
                "error": "Interval must be one of: 1d, 1w, 1m",
                "instrument": instrument
            })
        
        # Check for incompatible interval/period combinations
        from datetime import datetime as dt
        try:
            start_date = dt.strptime(start, '%Y-%m-%d')
            end_date = dt.strptime(end, '%Y-%m-%d')
            days_diff = (end_date - start_date).days
            
            # yfinance limitations for intraday data
            if interval == "1m" and days_diff > 30:
                return json.dumps({
                    "error": f"1-minute interval data is only available for the last 30 days. Your requested period is {days_diff} days. Use '1d' or '1w' for longer periods.",
                    "instrument": instrument
                })
        except ValueError as ve:
            return json.dumps({
                "error": f"Invalid date format. Use YYYY-MM-DD format. Error: {str(ve)}",
                "instrument": instrument
            })
        
        # Get ticker data
        ticker = yf.Ticker(instrument)
        
        # Get historical data
        try:
            hist = ticker.history(
                start=start,
                end=end,
                interval=interval,
                auto_adjust=adjusted,
                back_adjust=True,
                repair=True,
                keepna=False
            )
        except Exception as hist_error:
            return json.dumps({
                "error": f"Error fetching data from yfinance for '{instrument}': {str(hist_error)}. Check if the ticker symbol is valid and the date range is supported.",
                "instrument": instrument
            })
        
        if hist.empty:
            return json.dumps({
                "error": f"No price data found for '{instrument}' in the specified period ({start} to {end}) with interval '{interval}'. This could be due to: 1) Invalid ticker symbol, 2) Interval limitations (1m data only available for last 30 days), 4) Market closure dates.",
                "instrument": instrument
            })
        
        # Convert price data to bars
        bars = []
        for date, row in hist.iterrows():
            bars.append(PriceBar(
                t=date.strftime('%Y-%m-%d'),
                o=float(row['Open']) if not pd.isna(row['Open']) else None,
                h=float(row['High']) if not pd.isna(row['High']) else None,
                l=float(row['Low']) if not pd.isna(row['Low']) else None,
                c=float(row['Close']) if not pd.isna(row['Close']) else None,
                v=int(row['Volume']) if not pd.isna(row['Volume']) else None
            ))
        
        # Calculate total return if requested
        total_return = []
        if include_total_return:
            # Get dividend data
            dividends = ticker.dividends
            # Filter dividends to the same period safely
            try:
                if not dividends.empty:
                    dividends = dividends.loc[start:end]
            except Exception:
                # If date filtering fails, use all dividends
                pass
            total_return = calculate_total_return_index(hist, dividends)
        
        # Get adjustments data
        splits = ticker.splits
        stock_dividends = ticker.dividends
        
        # Filter splits and dividends to the same period safely
        splits_filtered = splits
        dividends_filtered = stock_dividends
        
        try:
            if not splits.empty:
                splits_filtered = splits.loc[start:end]
        except Exception:
            # If date filtering fails, use all splits
            pass
            
        try:
            if not stock_dividends.empty:
                dividends_filtered = stock_dividends.loc[start:end]
        except Exception:
            # If date filtering fails, use all dividends
            pass
        
        adjustments = PriceAdjustments(
            splits={date.strftime('%Y-%m-%d'): float(ratio) for date, ratio in splits_filtered.items()},
            dividends={date.strftime('%Y-%m-%d'): float(amount) for date, amount in dividends_filtered.items()},
            stock_splits={}  # Could be enhanced to separate stock splits from regular splits
        )
        
        # Create the complete price history response
        price_history = PriceHistory(
            symbol=instrument,
            bars=bars,
            total_return=total_return,
            adjustments=adjustments,
            tz="America/New_York",  # Default timezone, could be enhanced
            interval=interval,
            start_date=start,
            end_date=end
        )
        
        return price_history.model_dump_json(indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Error fetching price history for '{instrument}': {str(e)}",
            "instrument": instrument
        })


def calculate_dividend_cagr(dividends_series: pd.Series, years: float) -> float:
    """Calculate dividend CAGR over specified period"""
    if len(dividends_series) < 2 or years <= 0:
        return None
    
    # Get annual dividend sums
    annual_dividends = dividends_series.groupby(dividends_series.index.year).sum()
    
    if len(annual_dividends) < 2:
        return None
    
    first_year_dividend = annual_dividends.iloc[0]
    last_year_dividend = annual_dividends.iloc[-1]
    
    if first_year_dividend <= 0 or last_year_dividend <= 0:
        return None
    
    # CAGR = (Ending Value / Beginning Value)^(1/years) - 1
    cagr = ((last_year_dividend / first_year_dividend) ** (1 / years)) - 1
    return round(cagr * 100, 2)


def calculate_dividend_consistency(dividends_series: pd.Series) -> float:
    """Calculate dividend consistency score (0-100)"""
    if len(dividends_series) < 4:  # Need at least 4 quarters of data
        return None
    
    # Group by year and check for dividend payments
    annual_dividends = dividends_series.groupby(dividends_series.index.year).sum()
    
    # Check for dividend cuts or omissions
    years_with_dividends = len(annual_dividends[annual_dividends > 0])
    total_years = len(annual_dividends)
    
    if total_years == 0:
        return 0
    
    # Base consistency score
    consistency_score = (years_with_dividends / total_years) * 100
    
    # Penalty for dividend cuts
    dividend_cuts = 0
    for i in range(1, len(annual_dividends)):
        if annual_dividends.iloc[i] < annual_dividends.iloc[i-1] * 0.95:  # 5% tolerance
            dividend_cuts += 1
    
    # Reduce score for each cut
    consistency_score = max(0, consistency_score - (dividend_cuts * 15))
    
    return round(consistency_score, 1)


def calculate_dividend_yield_metrics(dividends_series: pd.Series, current_price: float) -> DividendYield:
    """Calculate dividend yield metrics"""
    yield_metrics = DividendYield()
    
    if current_price <= 0 or dividends_series.empty:
        return yield_metrics
    
    # Convert datetime to timezone-aware if needed
    def make_timezone_aware(dt):
        if dividends_series.index.tz is not None:
            import pytz
            if dt.tzinfo is None:
                return pytz.timezone('America/New_York').localize(dt)
            return dt
        return dt
    
    # TTM yield
    one_year_ago = make_timezone_aware(datetime.now() - timedelta(days=365))
    ttm_dividends = dividends_series[dividends_series.index >= one_year_ago].sum()
    if ttm_dividends > 0:
        yield_metrics.ttm = round((ttm_dividends / current_price) * 100, 2)
    
    # 5-year average yield (approximation using available data)
    if len(dividends_series) >= 5:
        five_year_ago = make_timezone_aware(datetime.now() - timedelta(days=365 * 5))
        five_year_dividends = dividends_series[dividends_series.index >= five_year_ago]
        
        if not five_year_dividends.empty:
            annual_avg_dividend = five_year_dividends.sum() / 5
            yield_metrics.five_year_avg = round((annual_avg_dividend / current_price) * 100, 2)
    
    return yield_metrics


def get_dividends_and_actions(arguments: Dict[str, Any]) -> str:
    """
    Get dividend history, corporate actions, and dividend quality metrics
    
    Args:
        arguments: Dictionary containing dividend and actions parameters
    
    Returns:
        JSON string with dividends, actions, and metrics or error message
    """
    try:
        instrument = arguments.get("instrument", "").upper().strip()
        start = arguments.get("start")
        end = arguments.get("end")
        
        if not instrument:
            return json.dumps({
                "error": "Instrument (ticker symbol) is required",
                "instrument": None
            })
        
        # Default date range: 10 years
        if not end:
            end = datetime.now().strftime('%Y-%m-%d')
        if not start:
            start = (datetime.now() - timedelta(days=365 * 10)).strftime('%Y-%m-%d')
        
        # Get ticker data
        ticker = yf.Ticker(instrument)
        
        # Get dividend data
        try:
            dividends_series = ticker.dividends
            if not dividends_series.empty:
                # Convert start and end to datetime for filtering
                start_dt = pd.to_datetime(start)
                end_dt = pd.to_datetime(end)
                
                # Make dates timezone-aware if needed
                if dividends_series.index.tz is not None:
                    import pytz
                    tz = dividends_series.index.tz
                    if start_dt.tz is None:
                        start_dt = tz.localize(start_dt)
                    if end_dt.tz is None:
                        end_dt = tz.localize(end_dt)
                
                # Filter by date range
                dividends_series = dividends_series[(dividends_series.index >= start_dt) & (dividends_series.index <= end_dt)]
        except Exception as e:
            print(f"Error getting dividends: {e}")
            dividends_series = pd.Series(dtype=float)
        
        # Get stock splits and actions
        try:
            splits = ticker.splits
            if not splits.empty:
                # Convert start and end to datetime for filtering
                start_dt = pd.to_datetime(start)
                end_dt = pd.to_datetime(end)
                
                # Make dates timezone-aware if needed
                if splits.index.tz is not None:
                    import pytz
                    tz = splits.index.tz
                    if start_dt.tz is None:
                        start_dt = tz.localize(start_dt)
                    if end_dt.tz is None:
                        end_dt = tz.localize(end_dt)
                
                # Filter by date range
                splits = splits[(splits.index >= start_dt) & (splits.index <= end_dt)]
        except Exception as e:
            print(f"Error getting splits: {e}")
            splits = pd.Series(dtype=float)
        
        # Get current price for yield calculation
        try:
            current_info = ticker.info
            current_price = current_info.get('regularMarketPrice') or current_info.get('currentPrice') or 0
        except Exception:
            current_price = 0
        
        # Process dividends
        dividend_records = []
        for date, amount in dividends_series.items():
            dividend_records.append(DividendRecord(
                ex_date=date.strftime('%Y-%m-%d'),
                amount=round(float(amount), 4),
                currency="USD"  # Default, could be enhanced
            ))
        
        # Calculate yield metrics
        yield_metrics = calculate_dividend_yield_metrics(dividends_series, current_price)
        
        # Calculate growth metrics
        growth_metrics = DividendGrowth()
        if len(dividends_series) >= 2:
            years_of_data = (dividends_series.index[-1] - dividends_series.index[0]).days / 365.25
            if years_of_data >= 1:
                growth_metrics.cagr_5y = calculate_dividend_cagr(
                    dividends_series, min(years_of_data, 5)
                )
                growth_metrics.consistency_score = calculate_dividend_consistency(dividends_series)
        
        # Process corporate actions
        actions = []
        for date, ratio in splits.items():
            actions.append(CorporateAction(
                type="split",
                effective_date=date.strftime('%Y-%m-%d'),
                factor=round(float(ratio), 4),
                description=f"Stock split {ratio}:1"
            ))
        
        # Create the complete response
        dividends_and_actions = DividendsAndActions(
            symbol=instrument,
            dividends=dividend_records,
            yield_metrics=yield_metrics,
            growth_metrics=growth_metrics,
            actions=actions,
            period_start=start,
            period_end=end
        )
        
        return dividends_and_actions.model_dump_json(indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Error fetching dividends and actions for '{instrument}': {str(e)}",
            "instrument": instrument
        })


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Execute a tool by name with given arguments
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Arguments to pass to the tool
    
    Returns:
        Tool execution result as string
    """
    tools_map = {
        "get_realtime_quote": get_realtime_quote,
        "get_fundamentals": get_fundamentals,
        "get_price_history": get_price_history,
        "get_dividends_and_actions": get_dividends_and_actions,
    }
    
    tool_function = tools_map.get(tool_name)
    if not tool_function:
        return json.dumps({
            "error": f"Tool '{tool_name}' not found",
            "available_tools": list(tools_map.keys())
        })
    
    return tool_function(arguments)