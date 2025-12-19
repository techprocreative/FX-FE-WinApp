"""
Local FastAPI Server
Runs within the Windows connector to handle backend operations
"""

import asyncio
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from loguru import logger

from core.config import Config
from api.subscription_checker import SubscriptionChecker
from api.llm_router import LLMRouter


# Pydantic models for API
class HealthResponse(BaseModel):
    status: str
    version: str
    mt5_connected: bool


class SubscriptionStatus(BaseModel):
    is_active: bool
    tier: str
    expires_at: Optional[str]
    features: list[str]


class StrategyRequest(BaseModel):
    prompt: str
    symbol: str
    timeframe: str
    model: Optional[str] = None


class StrategyResponse(BaseModel):
    strategy: str
    model_used: str
    tokens_used: int


class TradeRequest(BaseModel):
    symbol: str
    order_type: str  # 'buy' or 'sell'
    volume: float
    sl: Optional[float] = None
    tp: Optional[float] = None
    magic: int = 12345
    comment: str = "NexusTrade"


class TradeResponse(BaseModel):
    success: bool
    ticket: Optional[int] = None
    message: str


# Global instances
config: Optional[Config] = None
subscription_checker: Optional[SubscriptionChecker] = None
llm_router: Optional[LLMRouter] = None
mt5_client = None  # Will be set from main window


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for startup/shutdown"""
    logger.info("API Server starting up...")
    yield
    logger.info("API Server shutting down...")


# Create FastAPI app
app = FastAPI(
    title="NexusTrade Local API",
    description="Local backend API for NexusTrade Windows Connector",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def verify_subscription(x_api_key: str = Header(None)) -> SubscriptionStatus:
    """Verify user subscription from API key"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    if not subscription_checker:
        raise HTTPException(status_code=500, detail="Subscription checker not initialized")
    
    status = await subscription_checker.verify(x_api_key)
    if not status.is_active:
        raise HTTPException(status_code=403, detail="Subscription expired or inactive")
    
    return status


# ==================== Endpoints ====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    mt5_connected = mt5_client.is_connected if mt5_client else False
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        mt5_connected=mt5_connected
    )


@app.get("/subscription/status", response_model=SubscriptionStatus)
async def get_subscription_status(x_api_key: str = Header(...)):
    """Get current subscription status"""
    if not subscription_checker:
        raise HTTPException(status_code=500, detail="Service not ready")
    
    return await subscription_checker.verify(x_api_key)


@app.post("/llm/generate-strategy", response_model=StrategyResponse)
async def generate_strategy(
    request: StrategyRequest,
    subscription: SubscriptionStatus = Depends(verify_subscription)
):
    """Generate trading strategy using LLM"""
    # Check if user can use LLM
    if "llm_access" not in subscription.features and subscription.tier == "free":
        raise HTTPException(
            status_code=403, 
            detail="LLM access requires Basic subscription or higher"
        )
    
    if not llm_router:
        raise HTTPException(status_code=500, detail="LLM router not initialized")
    
    try:
        result = await llm_router.generate_strategy(
            prompt=request.prompt,
            symbol=request.symbol,
            timeframe=request.timeframe,
            model=request.model
        )
        return result
    except Exception as e:
        logger.exception(f"Strategy generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trade/open", response_model=TradeResponse)
async def open_trade(
    request: TradeRequest,
    subscription: SubscriptionStatus = Depends(verify_subscription)
):
    """Open a new trade via MT5"""
    if not mt5_client or not mt5_client.is_connected:
        raise HTTPException(status_code=503, detail="MT5 not connected")
    
    try:
        ticket = mt5_client.open_position(
            symbol=request.symbol,
            order_type=request.order_type,
            volume=request.volume,
            sl=request.sl,
            tp=request.tp,
            magic=request.magic,
            comment=request.comment
        )
        
        if ticket:
            return TradeResponse(
                success=True,
                ticket=ticket,
                message=f"Position opened: {ticket}"
            )
        else:
            return TradeResponse(
                success=False,
                message="Failed to open position"
            )
    except Exception as e:
        logger.exception(f"Trade execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trade/close/{ticket}", response_model=TradeResponse)
async def close_trade(
    ticket: int,
    subscription: SubscriptionStatus = Depends(verify_subscription)
):
    """Close a trade by ticket"""
    if not mt5_client or not mt5_client.is_connected:
        raise HTTPException(status_code=503, detail="MT5 not connected")
    
    try:
        success = mt5_client.close_position(ticket)
        return TradeResponse(
            success=success,
            ticket=ticket if success else None,
            message="Position closed" if success else "Failed to close position"
        )
    except Exception as e:
        logger.exception(f"Trade close failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/positions")
async def get_positions(
    subscription: SubscriptionStatus = Depends(verify_subscription)
):
    """Get all open positions"""
    if not mt5_client or not mt5_client.is_connected:
        raise HTTPException(status_code=503, detail="MT5 not connected")
    
    positions = mt5_client.get_positions()
    return {"positions": [vars(p) for p in positions]}


@app.get("/account")
async def get_account(
    subscription: SubscriptionStatus = Depends(verify_subscription)
):
    """Get account information"""
    if not mt5_client or not mt5_client.is_connected:
        raise HTTPException(status_code=503, detail="MT5 not connected")
    
    info = mt5_client.get_account_info()
    if info:
        return vars(info)
    raise HTTPException(status_code=500, detail="Failed to get account info")


# ==================== Server Startup ====================

def set_mt5_client(client):
    """Set MT5 client reference from main window"""
    global mt5_client
    mt5_client = client


async def start_api_server(app_config: Config):
    """Start the FastAPI server"""
    global config, subscription_checker, llm_router
    
    config = app_config
    subscription_checker = SubscriptionChecker(config.supabase)
    llm_router = LLMRouter(config.openrouter)
    
    server_config = uvicorn.Config(
        app,
        host=config.api_server.host,
        port=config.api_server.port,
        log_level="warning"
    )
    server = uvicorn.Server(server_config)
    
    logger.info(f"Starting API server on {config.api_server.host}:{config.api_server.port}")
    await server.serve()
