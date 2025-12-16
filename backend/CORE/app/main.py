"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings

settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI-Powered Personal Finance Assistant - Core Backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Root endpoint - API health check."""
    return {
        "message": f"{settings.app_name} API",
        "status": "operational",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "backend-core"
    }


# Router includes
from app.api import auth
app.include_router(auth.router, prefix="/api")

# Additional routers will be added as we build them
# from app.api import transactions, budgets, merchants, websocket
# app.include_router(transactions.router, prefix="/api")
# app.include_router(budgets.router, prefix="/api")
# app.include_router(merchants.router, prefix="/api")
# app.include_router(websocket.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
