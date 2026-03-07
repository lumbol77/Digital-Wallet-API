from fastapi import FastAPI
from app.database import engine, Base
from app import models
from app.routers import users, wallet

app = FastAPI()

# Include Routers
app.include_router(users.router)
app.include_router(wallet.router)

@app.on_event("startup")
def on_startup():
    print("Connecting to database...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

@app.get("/")
def root():
    return {"message": "Digital Wallet API running"}
