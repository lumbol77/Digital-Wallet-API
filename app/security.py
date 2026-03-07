import os  # <-- Add this
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from dotenv import load_dotenv # <-- Add this

load_dotenv() # <-- Load your .env file

# =========================================================
# CONFIGURATION
# =========================================================

# Instead of a hardcoded string, pull it from .env
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

security = HTTPBearer()

# ... rest of your code stays exactly the same ...