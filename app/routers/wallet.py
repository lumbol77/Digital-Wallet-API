from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi.responses import StreamingResponse

from app.security import get_current_user
from app.database import get_db
from app import crud, models, schemas
# Only one import of utils needed
from app.utils import check_fraud_risk, generate_transaction_pdf

router = APIRouter(prefix="/wallet", tags=["Wallet"])

@router.get("/balance")
def get_wallet_balance(current_user = Depends(get_current_user)):
    return {"balance": current_user.wallet.balance}

@router.post("/deposit")
def deposit_money(request: schemas.DepositRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    updated_wallet = crud.deposit_funds(db, current_user.wallet.id, request.amount)
    return {
        "message": "Deposit successful", 
        "amount": request.amount, 
        "new_balance": updated_wallet.balance
    }

@router.post("/withdraw")
def withdraw_money(request: schemas.WithdrawRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        updated_wallet = crud.withdraw_funds(db, current_user.wallet.id, request.amount)
        return {
            "message": "Withdrawal successful", 
            "amount": request.amount, 
            "new_balance": updated_wallet.balance
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- THE CORRECTED TRANSFER ROUTE ---
@router.post("/transfer")
async def transfer_money(
    request: schemas.TransferRequest, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    # A. Look up the receiver to get their balance for the AI
    receiver = db.query(models.User).filter(models.User.email == request.receiver_email).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    # B. Call the UPDATED Fraud Check (sending 3 numbers now)
    is_fraud = await check_fraud_risk(
        amount=request.amount, 
        sender_balance=current_user.wallet.balance,
        receiver_balance=receiver.wallet.balance
    )
    
    if is_fraud:
        raise HTTPException(status_code=403, detail="AI Security: Transaction flagged as high-risk.")

    # C. Proceed with DB transfer
    try:
        updated_wallet = crud.transfer_funds(db, current_user.wallet.id, request.receiver_email, request.amount)
        return {"message": "Transfer successful", "new_balance": updated_wallet.balance}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/transactions", response_model=list[schemas.TransactionResponse])
def get_history(
    transaction_type: str = Query(None),
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    query = db.query(models.Transaction).filter(models.Transaction.wallet_id == current_user.wallet.id)
    if transaction_type:
        query = query.filter(models.Transaction.type == transaction_type)
    return query.order_by(models.Transaction.timestamp.desc()).all()

@router.get("/transactions/{transaction_id}/receipt")
async def get_receipt(transaction_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    transaction = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.wallet_id == current_user.wallet.id
    ).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    pdf_buffer = generate_transaction_pdf(transaction, current_user.email)
    return StreamingResponse(
        pdf_buffer, 
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=receipt_{transaction_id}.pdf"}
    )