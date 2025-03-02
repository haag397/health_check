import asyncio
import httpx
import time
from fastapi import FastAPI, Query, HTTPException, Depends
from pydantic import BaseModel
from itertools import count
from datetime import datetime

app = FastAPI(title="Payment Gateway API Service")

# *Constants
API_GET_TOKEN = "https://ipg.gardeshpay.ir/v1/provider/payment/getToken"
API_REDIRECT = "https://ipg.gardeshpay.ir/v1/provider/payment/redirect"
PROVIDER_TOKEN = "mCamaJWoeSpswUnbpYZARJiJjCWGaZ"  # Token for provider

# *Default load test configuration
DEFAULT_REQUESTS_PER_MINUTE = 600
DEFAULT_DURATION_MINUTES = 1
DEFAULT_CALLBACK_URL = "https://www.google.com"
DEFAULT_AMOUNT = 10000
DEFAULT_INVOICE_DATE = "1403-11-30"

# *Counter for generating unique invoice numbers
invoice_counter = count(start=int(time.time()))

# *Valid validation tokens (in a real app, this would be in a secure database)
VALID_VALIDATION_TOKENS = ["valid_token_123", "test_token_456"]

# *Models
class ErrorResponse(BaseModel):
    error: str
    status_code: int
    invoice_number: str
    successful_requests_before_error: int
    start_time: str
    last_request_time: str
class SuccessResponse(BaseModel):
    message: str
    total_successful_requests: int

def generate_unique_invoice():
    """Generate a 10-digit unique invoice number"""
    return str(next(invoice_counter))[:10]  # Ensure it stays 10 digits

async def validate_token(validation_token: str = Query(..., description="Validation token required for API access")):
    """Validate the incoming token before processing any requests"""
    if validation_token not in VALID_VALIDATION_TOKENS:
        raise HTTPException(status_code=401, detail="Invalid validation token")
    return validation_token

async def send_payment_request(client, unique_invoice, callback_url, amount, invoice_date):
    """Send request to payment gateway and check for errors"""
    # *Step 1: Get Token
    payload = {
        "token": PROVIDER_TOKEN,
        "invoiceNumber": unique_invoice,
        "invoiceDate": invoice_date,
        "amount": amount, 
        "callback": callback_url,
        "IpAddressNotAllowed": ""
    }
    
    get_token_response = await client.post(API_GET_TOKEN, json=payload)
    
    # *Check if get_token failed
    if get_token_response.status_code != 200:
        return {
            "error": "GetToken API failed",
            "status_code": get_token_response.status_code,
            "invoice_number": unique_invoice
        }
    
    # *Parse token from response
    token = None
    try:
        data = get_token_response.json()
        if data.get("success") and "data" in data:
            token = data["data"].get("token")
        else:
            return {
                "error": "Token not found in response",
                "status_code": get_token_response.status_code,
                "invoice_number": unique_invoice
            }
    except Exception as e:
        return {
            "error": f"Error parsing response: {str(e)}",
            "status_code": get_token_response.status_code,
        }
    
    # *Step 2: Use Token at Redirect URL
    redirect_url = f"{API_REDIRECT}/{token}"
    redirect_response = await client.get(redirect_url)
    
    # *Check if redirect failed
    if redirect_response.status_code != 200:
        return {
            "error": "Redirect API failed",
            "status_code": redirect_response.status_code,
        }
    
    # *If we get here, both requests were successful
    return {"success": True}

@app.get("/metrics", response_model=SuccessResponse)
async def run_load_test(validation_token: str = Depends(validate_token)):
    """
    Runs a load test against the payment gateway APIs
    
    - Stops immediately if any request returns a non-200 status code
    - Returns the total number of successful requests before an error
    """
    # *Use hardcoded default values
    requests_per_minute = DEFAULT_REQUESTS_PER_MINUTE
    duration_minutes = DEFAULT_DURATION_MINUTES
    callback_url = DEFAULT_CALLBACK_URL
    amount = DEFAULT_AMOUNT
    invoice_date = DEFAULT_INVOICE_DATE
    
    successful_requests = 0
    start_time = datetime.now().isoformat()
    last_request_time = None
    
    async with httpx.AsyncClient() as client:
        # * Calculate total requests to make
        total_planned_requests = requests_per_minute * duration_minutes
        
        for _ in range(total_planned_requests):
            unique_invoice = generate_unique_invoice()
            last_request_time = datetime.now().isoformat()
            result = await send_payment_request(
                client, 
                unique_invoice, 
                callback_url, 
                amount, 
                invoice_date
            )
            
            # * If error occurred, return immediately
            if "error" in result:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": result["error"],
                        "status_code": result["status_code"],
                        "successful_requests_before_error": successful_requests,
                        "start_time": start_time,
                        "last_request_time": last_request_time
                    }
                )
            
            # *Increment successful requests counter
            successful_requests += 1
            
            # *Sleep to maintain the specified rate
            await asyncio.sleep(60 / requests_per_minute)
    
    # *If we get here, all requests were successful
    return SuccessResponse(
        message="All API calls completed successfully",
        total_successful_requests=successful_requests
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9090)
