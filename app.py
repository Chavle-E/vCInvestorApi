from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.endpoints import investors, investment_funds, utils
from database import engine
import models

app = FastAPI(title="Investor Database API",
              description="API for managing investors and investment funds database",
              version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(investors.router, prefix="/api/v1/investors", tags=["investors"])
app.include_router(investment_funds.router, prefix="/api/v1/funds", tags=["funds"])
app.include_router(utils.router, prefix="/api/v1", tags=["utils"])


@app.get("/health")
def health_check():
    """API health check endpoint"""
    return {"status": "healthy"}


# Create tables
models.Base.metadata.create_all(bind=engine)
