# import time
# from itertools import count
# import asyncio
# import httpx
# from fastapi import FastAPI, Query, HTTPException
# import uvicorn
# app = FastAPI()
# API_GET_TOKEN = "https://ipg.gardeshpay.ir/v1/provider/payment/getToken"
# API_REDIRECT = "https://ipg.gardeshpay.ir/v1/provider/payment/redirect"

# # Counter for generating unique invoice numbers
# invoice_counter = count(start=int(time.time()))  # Start from current timestamp

# def generate_unique_invoice():
#     """Generate a 10-digit unique invoice number."""
#     return str(next(invoice_counter))[:10]  # Ensure it stays 10 digits

# async def send_request(client, unique_invoice):
#     """Step 1: Get Token."""
#     PAYLOAD = {
#         "token": "mCamaJWoeSpswUnbpYZARJiJjCWGaZ",
#         "invoiceNumber": unique_invoice,
#         "invoiceDate": "1403-11-30",
#         "amount": 10000,
#         "callback": "https://www.google.com",
#         "IpAddressNotAllowed": ""
#     }

#     # Debugging: Print payload before sending
#     print(f"DEBUG PAYLOAD: {PAYLOAD}")

#     start_time = time.time()
#     response = await client.post(API_GET_TOKEN, json=PAYLOAD)
#     end_time = time.time()

#     # Check if response status code is not 200
#     if response.status_code != 200:
#         raise HTTPException(
#             status_code=response.status_code,
#             detail=f"Failed to get token. Response: {response.text}"
#         )

#     # Parse token if response is successful
#     token = None
#     try:
#         data = response.json()
#         if data.get("success") and "data" in data:
#             token = data["data"].get("token")
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error parsing getToken response: {e}"
#         )

#     """Step 2: Use Token at Redirect URL."""
#     if token:
#         redirect_url = f"{API_REDIRECT}/{token}"
#         start_time_redirect = time.time()
#         redirect_response = await client.get(redirect_url)
#         end_time_redirect = time.time()

#         # Check if redirect response status code is not 200
#         if redirect_response.status_code != 200:
#             raise HTTPException(
#                 status_code=redirect_response.status_code,
#                 detail=f"Failed to redirect. Response: {redirect_response.text}"
#             )

#         return {
#             "message": "Payment processed successfully",
#             "token": token,
#             "redirect_response": redirect_response.text
#         }

# @app.get("/process-payment")
# async def process_payment(token: str = Query(..., description="Token to validate")):
#     """API endpoint to validate token and process payment."""
#     if not is_token_valid(token):  # Replace with your token validation logic
#         raise HTTPException(status_code=400, detail="Invalid token")

#     # async with httpx.AsyncClient() as client:
#     #     unique_invoice = generate_unique_invoice()
#     #     result = await send_request(client, unique_invoice)
        
#     log_data = []
#     async with httpx.AsyncClient() as client:
#         for _ in range(400):
#             unique_invoice = generate_unique_invoice()  # Get unique number before sending request
#             result= await send_request(client, unique_invoice)
#             await asyncio.sleep(60 / 1)  # Control request rate

#     return result

# def is_token_valid(token: str) -> bool:
#     """Validate the token (replace with your validation logic)."""
#     # Example: Check if the token matches a predefined value
#     return token == "sheyda"

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
    
import time
from itertools import count
import asyncio
import httpx
import json
from fastapi import FastAPI, Query, HTTPException

app = FastAPI()

# API endpoints
API_GET_TOKEN = "https://ipg.gardeshpay.ir/v1/provider/payment/getToken"
API_REDIRECT = "https://ipg.gardeshpay.ir/v1/provider/payment/redirect"

# Counter for generating unique invoice numbers
invoice_counter = count(start=int(time.time()))  # Start from current timestamp

def generate_unique_invoice():
    """Generate a 10-digit unique invoice number."""
    return str(next(invoice_counter))[:10]  # Ensure it stays 10 digits

async def send_request(client, unique_invoice):
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

    # Check if response status code is not 200
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to get token. Response: {response.text}"
        )

    # Parse token if response is successful
    token = None
    try:
        data = response.json()
        if data.get("success") and "data" in data:
            token = data["data"].get("token")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error parsing getToken response: {e}"
        )

    """Step 2: Use Token at Redirect URL."""
    if token:
        redirect_url = f"{API_REDIRECT}/{token}"
        start_time_redirect = time.time()
        redirect_response = await client.get(redirect_url)
        end_time_redirect = time.time()

        # Check if redirect response status code is not 200
        if redirect_response.status_code != 200:
            raise HTTPException(
                status_code=redirect_response.status_code,
                detail=f"Failed to redirect. Response: {redirect_response.text}"
            )

        return {
            "message": "Payment processed successfully",
            "token": token,
            "redirect_response": redirect_response.text
        }

async def load_test(requests_per_minute=600, duration_minutes=1):
    """Load test function to send requests at a controlled rate."""
    log_data = []
    async with httpx.AsyncClient() as client:
        for _ in range(requests_per_minute * duration_minutes):
            unique_invoice = generate_unique_invoice()  # Get unique number before sending request
            await send_request(client, log_data, unique_invoice)
            await asyncio.sleep(60 / requests_per_minute)  # Control request rate
            
@app.get("/process-payment")
async def process_payment(token: str = Query(..., description="Token to validate")):
    """API endpoint to validate token and process payment."""
    if not is_token_valid(token):  # Replace with your token validation logic
        raise HTTPException(status_code=400, detail="Invalid token")

    async with httpx.AsyncClient() as client:
        unique_invoice = generate_unique_invoice()
        result = await send_request(client, unique_invoice)

    return result

def is_token_valid(token: str) -> bool:
    """Validate the token (replace with your validation logic)."""
    # Example: Check if the token matches a predefined value
    return token == "sheyda"

@app.get("/run-load-test")
async def run_load_test():
    """Endpoint to run the load test."""
    log_data = await load_test(600)  # Send 600 requests in 1 minute
    return {"message": "Load test completed", "log_data": log_data}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)