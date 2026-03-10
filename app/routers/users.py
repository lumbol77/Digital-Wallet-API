from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas, utils
from app.database import get_db
from app.security import create_access_token


router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = utils.hash_password(user.password)

    new_user = models.User(
        email=user.email,
        hashed_password=hashed_pw
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create wallet automatically
    new_wallet = models.Wallet(user_id=new_user.id)
    db.add(new_wallet)
    db.commit()

    return new_user


@router.post("/login", response_model=schemas.Token)
def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_credentials.email).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    if not utils.verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    access_token = create_access_token({"sub": user.email})

    return {"access_token": access_token, "token_type": "bearer"}