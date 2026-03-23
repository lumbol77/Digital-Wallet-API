import io
import httpx
from datetime import datetime # Added for the ML feature
from passlib.context import CryptContext
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# --- 1. PASSWORD SECURITY ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# --- 2. UPDATED ML API CONNECTOR ---
async def check_fraud_risk(amount: float, sender_balance: float, receiver_balance: float):
    # Your live Render URL
    FRAUD_API_URL = "https://fraud-api-t9wy.onrender.com/predict" 
    
    # 1. Build the payload to match the Fraud API's Transaction Schema
    payload = {
        "amount": amount,
        "sender_balance": sender_balance,
        "receiver_balance": receiver_balance,
        "hour_of_day": datetime.now().hour,
        "is_international": 0 # Defaulting to 0/False for now
    }
    
    print(f"\n📡 [REAL AI CHECK] Calling Render for ${amount}...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                FRAUD_API_URL, 
                json=payload,
                timeout=50.0  
            )
            
            # If the API is successful
            if response.status_code == 200:
                result = response.json()
                # Check for "prediction" (our ML key) or "is_fraud"
                is_fraud = result.get("prediction") == 1
                print(f"🤖 [AI RESPONSE]: {'🚫 FRAUD' if is_fraud else '✅ SAFE'}")
                return is_fraud
            
            # Log specific error if validation failed (422) or server errored (500)
            print(f"⚠️ [AI ERROR]: Server returned {response.status_code} - {response.text}")
            return False # Fail-safe (allow transaction if AI is glitchy)
            
    except Exception as e:
        print(f"❌ [CONNECTION FAILED]: {e}")
        return False # Fail-safe

# PDF GENERATOR 
def generate_transaction_pdf(transaction, email):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, "TRANSACTION RECEIPT")
    p.setFont("Helvetica", 12)
    p.drawString(100, 720, f"User: {email}")
    amount = getattr(transaction, 'amount', 0)
    p.drawString(100, 700, f"Amount: ${amount}")
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer