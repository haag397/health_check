import asyncio
import httpx
import time
import json
from fastapi import FastAPI, Query, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional
from itertools import count

app = FastAPI(title="Payment Gateway API Service")

# Constants
API_GET_TOKEN = "https://ipg.gardeshpay.ir/v1/provider/payment/getToken"
API_REDIRECT = "https://ipg.gardeshpay.ir/v1/provider/payment/redirect"
PROVIDER_TOKEN = "mCamaJWoeSpswUnbpYZARJiJjCWGaZ"  # Token for provider

# Default load test configuration
DEFAULT_REQUESTS_PER_MINUTE = 600
DEFAULT_DURATION_MINUTES = 1
DEFAULT_CALLBACK_URL = "https://www.google.com"
DEFAULT_AMOUNT = 10000
DEFAULT_INVOICE_DATE = "1403-11-30"

# Counter for generating unique invoice numbers
invoice_counter = count(start=int(time.time()))

# Valid validation tokens (in a real app, this would be in a secure database)
VALID_VALIDATION_TOKENS = ["valid_token_123", "test_token_456"]

# Models
class LoadTestResponse(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    average_response_time: float
    results: List[Dict]

def generate_unique_invoice():
    """Generate a 10-digit unique invoice number"""
    return str(next(invoice_counter))[:10]  # Ensure it stays 10 digits

async def validate_token(validation_token: str = Query(..., description="Validation token required for API access")):
    """Validate the incoming token before processing any requests"""
    if validation_token not in VALID_VALIDATION_TOKENS:
        raise HTTPException(status_code=401, detail="Invalid validation token")
    return validation_token

async def send_payment_request(client, unique_invoice, callback_url, amount, invoice_date):
    """Send request to payment gateway and return results"""
    results = {}
    
    # Step 1: Get Token
    payload = {
        "token": PROVIDER_TOKEN,
        "invoiceNumber": unique_invoice,
        "invoiceDate": invoice_date,
        "amount": amount, 
        "callback": callback_url,
        "IpAddressNotAllowed": ""
    }
    
    start_time = time.time()
    get_token_response = await client.post(API_GET_TOKEN, json=payload)
    end_time = time.time()
    
    results["get_token"] = {
        "invoiceNumber": unique_invoice,
        "status_code": get_token_response.status_code,
        "response_time": round(end_time - start_time, 4),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    # Parse token if response is successful
    token = None
    if get_token_response.status_code == 200:
        try:
            data = get_token_response.json()
            if data.get("success") and "data" in data:
                token = data["data"].get("token")
                results["get_token"]["success"] = True
                results["get_token"]["token"] = token
        except Exception as e:
            results["get_token"]["error"] = str(e)
            results["get_token"]["success"] = False
    else:
        results["get_token"]["success"] = False
        try:
            results["get_token"]["response_body"] = get_token_response.json()
        except:
            results["get_token"]["response_body"] = get_token_response.text
    
    # Step 2: Use Token at Redirect URL if token was obtained
    if token:
        redirect_url = f"{API_REDIRECT}/{token}"
        start_time_redirect = time.time()
        redirect_response = await client.get(redirect_url)
        end_time_redirect = time.time()
        
        results["redirect"] = {
            "invoiceNumber": unique_invoice,
            "status_code": redirect_response.status_code,
            "response_time": round(end_time_redirect - start_time_redirect, 4),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "token": token
        }
        
        if redirect_response.status_code == 200:
            results["redirect"]["success"] = True
        else:
            results["redirect"]["success"] = False
            try:
                results["redirect"]["response_body"] = redirect_response.json()
            except:
                results["redirect"]["response_body"] = redirect_response.text
    else:
        results["redirect"] = {
            "success": False,
            "error": "No token obtained from getToken request"
        }
    
    # Overall success is if both steps were successful with 200 status
    results["overall_success"] = (
        results["get_token"].get("status_code") == 200 and
        "redirect" in results and 
        results["redirect"].get("status_code") == 200
    )
    
    return results

@app.get("/api/load-test", response_model=LoadTestResponse)
async def run_load_test(validation_token: str = Depends(validate_token)):
    """
    Runs a load test against the payment gateway APIs using default settings
    
    - Validates the token first
    - Sends requests at a fixed rate (600 requests per minute by default)
    - Returns statistics about successful/failed requests
    """
    # Use hardcoded default values instead of getting them from request
    requests_per_minute = DEFAULT_REQUESTS_PER_MINUTE
    duration_minutes = DEFAULT_DURATION_MINUTES
    callback_url = DEFAULT_CALLBACK_URL
    amount = DEFAULT_AMOUNT
    invoice_date = DEFAULT_INVOICE_DATE
    
    results = []
    successful_requests = 0
    total_response_time = 0
    
    async with httpx.AsyncClient() as client:
        tasks = []
        
        # Create all tasks for the load test
        for _ in range(requests_per_minute * duration_minutes):
            unique_invoice = generate_unique_invoice()
            task = asyncio.create_task(
                send_payment_request(
                    client, 
                    unique_invoice, 
                    callback_url, 
                    amount, 
                    invoice_date
                )
            )
            tasks.append(task)
            
            # Calculate delay between requests to maintain the rate
            await asyncio.sleep(60 / requests_per_minute)
        
        # Wait for all tasks to complete
        completed_results = await asyncio.gather(*tasks)
        
        # Process results
        for result in completed_results:
            results.append(result)
            if result.get("overall_success", False):
                successful_requests += 1
            
            # Add up response times for get_token requests (could add redirect times too if needed)
            if "get_token" in result and "response_time" in result["get_token"]:
                total_response_time += result["get_token"]["response_time"]
    
    # Calculate statistics
    total_requests = len(results)
    failed_requests = total_requests - successful_requests
    success_rate = (successful_requests / total_requests) * 100 if total_requests > 0 else 0
    average_response_time = total_response_time / total_requests if total_requests > 0 else 0
    
    return LoadTestResponse(
        total_requests=total_requests,
        successful_requests=successful_requests,
        failed_requests=failed_requests,
        success_rate=round(success_rate, 2),
        average_response_time=round(average_response_time, 4),
        results=results
    )

@app.get("/")
async def root():
    return {"message": "Payment Gateway API Service is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)