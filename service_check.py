import time
from itertools import count
import asyncio
import httpx
import json
from fastapi import FastAPI, Query, HTTPException
import uvicorn

app = FastAPI()

# API endpoints
API_GET_TOKEN = "https://ipg.gardeshpay.ir/v1/provider/payment/getToken"
API_REDIRECT = "https://ipg.gardeshpay.ir/v1/provider/payment/redirect"

# Counter for generating unique invoice numbers
invoice_counter = count(start=int(time.time()))  # Start from current timestamp

def generate_unique_invoice():
    """Generate a 10-digit unique invoice number."""
    return str(next(invoice_counter))[:10]  # Ensure it stays 10 digits

async def send_request(client, log_list, unique_invoice):
    """Step 1: Get Token."""
    PAYLOAD = {
        "token": "mCamaJWoeSpswUnbpYZARJiJjCWGaZ",
        "invoiceNumber": unique_invoice,
        "invoiceDate": "1403-11-30",
        "amount": 10000,
        "callback": "https://www.google.com",
        "IpAddressNotAllowed": ""
    }

    # Debugging: Print payload before sending
    print(f"DEBUG PAYLOAD: {PAYLOAD}")

    start_time = time.time()
    response = await client.post(API_GET_TOKEN, json=PAYLOAD)
    end_time = time.time()

    log_entry = {
        "type": "getToken",
        "invoiceNumber": unique_invoice,
        "status_code": response.status_code,
        "response_time": round(end_time - start_time, 4),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "response_body": response.text
    }
    print(f"LOG: {log_entry}")
    log_list.append(log_entry)

    # Parse token if response is successful
    token = None
    if response.status_code == 200:
        try:
            data = response.json()
            if data.get("success") and "data" in data:
                token = data["data"].get("token")
        except Exception as e:
            print(f"Error parsing getToken response: {e}")

    """Step 2: Use Token at Redirect URL."""
    if token:
        redirect_url = f"{API_REDIRECT}/{token}"
        start_time_redirect = time.time()
        redirect_response = await client.get(redirect_url)
        end_time_redirect = time.time()

        log_entry_redirect = {
            "type": "redirect",
            "invoiceNumber": unique_invoice,
            "status_code": redirect_response.status_code,
            "response_time": round(end_time_redirect - start_time_redirect, 4),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "response_body": redirect_response.text,
            "token": token
        }
        print(f"LOG: {log_entry_redirect}")
        log_list.append(log_entry_redirect)

@app.get("/process-payment")
async def process_payment(token: str = Query(..., description="Token to validate")):
    """API endpoint to validate token and process payment."""
    if not is_token_valid(token):  # Replace with your token validation logic
        raise HTTPException(status_code=400, detail="Invalid token")

    log_data = []
    async with httpx.AsyncClient() as client:
        unique_invoice = generate_unique_invoice()
        await send_request(client, log_data, unique_invoice)

    return {"message": "Payment processed successfully", "log_data": log_data}

def is_token_valid(token: str) -> bool:
    """Validate the token (replace with your validation logic)."""
    # Example: Check if the token matches a predefined value
    return token == "mCamaJWoeSpswUnbpYZARJiJjCWGaZ"

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)