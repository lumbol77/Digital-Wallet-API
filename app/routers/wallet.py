from fastapi import APIRouter, Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.security import get_current_user
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/wallet", tags=["Wallet"])
@router.get("/balance")
def get_wallet_balance(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    wallet = current_user.wallet
    return {"balance": wallet.balance}

# Add a deposit route in wallet.py

@router.post("/deposit")
def deposit_money(
    request: schemas.DepositRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # get user's wallet
    wallet = current_user.wallet

    # update balance
    wallet.balance += request.amount

    # record transaction
    transaction = models.Transaction(
        amount=request.amount,
        type="deposit",
        wallet_id=wallet.id
    )
    db.add(transaction)
    db.commit()
    db.refresh(wallet)
    return {"message": "Deposit successful", "new_balance": wallet.balance}

#Add Withdrawal Endpoint {withdrawal fuction}

@router.post("/withdraw")
def withdraw_money(
    request: schemas.WithdrawRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    wallet = current_user.wallet

    # Amount must be positive
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Withdrawal amount must be positive")

    # Check if user has enough balance
    if wallet.balance < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # Subtract the amount
    wallet.balance -= request.amount

    # Record transaction
    transaction = models.Transaction(
        amount=request.amount,
        type="withdrawal",
        wallet_id=wallet.id
    )
    db.add(transaction)

    db.commit()
    db.refresh(wallet)

    return {"message": "Withdrawal successful", "new_balance": wallet.balance}

# Add History Endpoint

@router.get("/transactions", response_model=list[schemas.TransactionResponse])
def get_transaction_history(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    wallet = current_user.wallet

    history = db.query(models.Transaction)\
                .filter(models.Transaction.wallet_id == wallet.id)\
                .order_by(models.Transaction.timestamp.desc())\
                .all()

    return history

# Add Transfer Endpoint
@router.post("/transfer")
def transfer_money(
    request: schemas.TransferRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    sender = current_user
    sender_wallet = sender.wallet

    # Cannot send to self
    if sender.email == request.receiver_email:
        raise HTTPException(status_code=400, detail="You cannot transfer to yourself")

    # Retrieve receiver
    receiver = db.query(models.User).filter(models.User.email == request.receiver_email).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    receiver_wallet = receiver.wallet

    # Validate amount
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    # Check balance
    if sender_wallet.balance < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # Perform transfer
    sender_wallet.balance -= request.amount
    receiver_wallet.balance += request.amount

    # Record sender transaction
    debit_txn = models.Transaction(
        amount=request.amount,
        type="transfer_sent",
        wallet_id=sender_wallet.id
    )
    db.add(debit_txn)

    # Record receiver transaction
    credit_txn = models.Transaction(
        amount=request.amount,
        type="transfer_received",
        wallet_id=receiver_wallet.id
    )
    db.add(credit_txn)

    db.commit()
    db.refresh(sender_wallet)
    db.refresh(receiver_wallet)

    return {
        "message": "Transfer successful",
        "sent_amount": request.amount,
        "to": request.receiver_email,
        "new_balance": sender_wallet.balance
    }

# Add Transfer History Endpoint

@router.get("/transfers", response_model=list[schemas.TransferHistoryResponse])
def get_transfer_history(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    wallet = current_user.wallet

    # Only get transfer_sent or transfer_received
    transfers = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.wallet_id == wallet.id,
            models.Transaction.type.in_(["transfer_sent", "transfer_received"])
        )
        .order_by(models.Transaction.timestamp.desc())
        .all()
    )

    return transfers
