
from fastapi import FastAPI, HTTPException, Query
import asyncio
import httpx
import time
from itertools import count

app = FastAPI()

API_GET_TOKEN = "https://ipg.gardeshpay.ir/v1/provider/payment/getToken"
API_REDIRECT = "https://ipg.gardeshpay.ir/v1/provider/payment/redirect"
VALID_TOKENS = {"sheyda", "test123"}  # Example valid tokens
invoice_counter = count(start=int(time.time()))  # Unique invoice numbers

def generate_unique_invoice():
    return str(next(invoice_counter))[:10]

async def send_request(client, unique_invoice, user_token):
    payload = {
        # "token": user_token,
        "token": "mCamaJWoeSpswUnbpYZARJiJjCWGaZ",
        "invoiceNumber": unique_invoice,
        "invoiceDate": "1403-11-30",
        "amount": 10000,
        "callback": "https://www.google.com",
        "IpAddressNotAllowed": ""
    }
    
    start_time = time.time()
    response = await client.post(API_GET_TOKEN, json=payload)
    end_time = time.time()
    
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Error from API: {response.text}")
    data = response.json()
    # token = data.get("data", {}).get("token")
    token = data["data"].get("token")
    if not token:
        raise HTTPException(status_code=500, detail="Failed to extract token from response")
    return token

async def start_payment_process(token,requests_per_minute=600,duration_minutes=1 ):

    log_data = []
    async with httpx.AsyncClient() as client:
        for _ in range(requests_per_minute * duration_minutes):
            unique_invoice = generate_unique_invoice()  # Get unique number before sending request
            await send_request(client, log_data, unique_invoice)
            await asyncio.sleep(60 / requests_per_minute)  # Control request rate
@app.get("/process-payment")
async def process_payment(token: str = Query(..., description="User token")):
    if token not in VALID_TOKENS:
        raise HTTPException(status_code=403, detail="Invalid token")
    asyncio.create_task(start_payment_process(token))
    return {"message": "Payment process started"}
