from sqlalchemy.orm import Session
from . import models

def deposit_funds(db: Session, wallet_id: int, amount: float):
    with db.begin_nested():
        # Lock the specific wallet row
        wallet = db.query(models.Wallet).filter(models.Wallet.id == wallet_id).with_for_update().first()
        wallet.balance += amount
        
        db.add(models.Transaction(amount=amount, type="deposit", wallet_id=wallet_id))
    db.commit()
    return wallet

def withdraw_funds(db: Session, wallet_id: int, amount: float):
    with db.begin_nested():
        wallet = db.query(models.Wallet).filter(models.Wallet.id == wallet_id).with_for_update().first()
        
        if wallet.balance < amount:
            raise ValueError("Insufficient funds")
            
        wallet.balance -= amount
        db.add(models.Transaction(amount=amount, type="withdrawal", wallet_id=wallet_id))
    db.commit()
    return wallet

def transfer_funds(db: Session, sender_wallet_id: int, receiver_email: str, amount: float):
    with db.begin_nested():
        # 1. Lock Sender Wallet
        sender_wallet = db.query(models.Wallet).filter(models.Wallet.id == sender_wallet_id).with_for_update().first()
        
        # 2. Get Receiver Wallet via Email Join
        receiver_wallet = db.query(models.Wallet).join(models.User).filter(models.User.email == receiver_email).with_for_update().first()
        
        if not receiver_wallet:
            raise ValueError("Receiver not found")
        if sender_wallet.id == receiver_wallet.id:
            raise ValueError("You cannot transfer to yourself")
        if sender_wallet.balance < amount:
            raise ValueError("Insufficient funds")

        # 3. Perform the Atomic swap
        sender_wallet.balance -= amount
        receiver_wallet.balance += amount

        # 4. Record both sides of the ledger
        db.add(models.Transaction(amount=amount, type="transfer_sent", wallet_id=sender_wallet.id))
        db.add(models.Transaction(amount=amount, type="transfer_received", wallet_id=receiver_wallet.id))
        
    db.commit()
    return sender_wallet