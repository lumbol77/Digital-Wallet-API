import httpx
import asyncio
import time

# UPDATE THESE WITH YOUR ACTUAL RENDER URLS
WALLET_API_URL = "https://your-wallet-api.onrender.com" 

async def test_full_flow():
    print("Starting Live Integration Test...")
    
    # 1. Check if Wallet is awake
    async with httpx.AsyncClient() as client:
        try:
            print(" Checking Wallet Health...")
            health = await client.get(f"{WALLET_API_URL}/")
            print(f" Wallet Status: {health.json()}")

            # 2. Simulate a Login (Replace with a real test user in your DB)
            print("\n Logging in...")
            login_data = {"email": "testuser@gmail.com", "password": "password123"}
            auth_res = await client.post(f"{WALLET_API_URL}/users/login", json=login_data)
            
            if auth_res.status_code != 200:
                print(f" Login Failed: {auth_res.text}")
                return

            token = auth_res.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}

            # 3. Trigger a Transfer (This hits the Fraud ML API)
            print("\n Triggering Fraud Check via Transfer...")
            transfer_data = {
                "receiver_email": "receiver@gmail.com",
                "amount": 500.0
            }
            
            start_time = time.time()
            # 60s timeout to allow for Render's potential cold start
            response = await client.post(
                f"{WALLET_API_URL}/wallet/transfer", 
                json=transfer_data, 
                headers=headers,
                timeout=60.0
            )
            
            duration = time.time() - start_time
            print(f" Request took {duration:.2f} seconds")

            if response.status_code == 200:
                print("SUCCESS: Transfer processed and approved by AI.")
            elif response.status_code == 403:
                print(" BLOCKED: AI correctly flagged this as suspicious.")
            else:
                print(f" UNEXPECTED: {response.status_code} - {response.text}")

        except Exception as e:
            print(f" TEST FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_full_flow())