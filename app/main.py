from fastapi import FastAPI
from app.database import engine, Base
from app.routers import users, wallet
import logging

# 1. Setup Professional Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 2. Initialize FastAPI
app = FastAPI(
    title="Digital Wallet & AI Fraud Detection System",
    description="A secure fintech backend with microservices integration.",
    version="1.0.0"
)

# 3. Database Startup Event
# This automatically creates your PostgreSQL tables if they don't exist
@app.on_event("startup")
def on_startup():
    logger.info("Initializing Database...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created successfully.")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")

# 4. Include Routers
# This 'plugs in' the code from your app/routers/ files
app.include_router(users.router)
app.include_router(wallet.router)

# 5. Root Health Check
@app.get("/")
def root():
    return {
        "status": "Online",
        "service": "Digital Wallet API",
        "documentation": "/docs"
    }

# 6. Global Exception Handler (Optional but Recommended)
# This prevents the app from leaking sensitive raw error traces to the user
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global error caught: {exc}")
    return {"detail": "An internal server error occurred. Please check logs."}