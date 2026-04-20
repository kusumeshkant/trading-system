from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.config.settings import get_settings
from app.core.logger import setup_logging, logger
from app.core.exceptions import TradingSystemError
from app.middleware.logging_middleware import LoggingMiddleware
from app.api.routes import trading
from app.api.routes import analytics

settings = get_settings()

setup_logging()

app = FastAPI(
    title="Trading System",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(LoggingMiddleware)

app.include_router(trading.router)
app.include_router(analytics.router)


@app.exception_handler(TradingSystemError)
async def trading_error_handler(request: Request, exc: TradingSystemError):
    logger.error("trading_error", error=str(exc), path=request.url.path)
    return JSONResponse(status_code=400, content={"error": str(exc)})


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.app_env}


@app.on_event("startup")
async def startup():
    from app.analytics.scheduler import setup_analytics_scheduler
    from app.api.routes.analytics import _records
    setup_analytics_scheduler(lambda: _records)
    logger.info("app_started", env=settings.app_env, port=settings.app_port)


@app.on_event("shutdown")
async def shutdown():
    logger.info("app_stopped")
