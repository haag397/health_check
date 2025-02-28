import asyncio
import httpx
import time
import json
import uuid 
import random

API_GET_TOKEN = "https://ipg.gardeshpay.ir/v1/provider/payment/getToken"
API_REDIRECT = "https://ipg.gardeshpay.ir/v1/provider/payment/redirect"
unique = str(random.randint(10**9, 10**10 - 1))  # Random 10-digit number


PAYLOAD = {
    "token": "mCamaJWoeSpswUnbpYZARJiJjCWGaZ",
    # "invoiceNumber": unique,
    "invoiceDate": "1403-11-30",
    "amount": 10000,
    "callback": "https://www.google.com",
    "IpAddressNotAllowed": ""
}

async def send_request(client, log_list):
    """ Step 1: Get Token """
    unique = str(random.randint(10**9, 10**10 - 1))  # Random 10-digit number
    payload = PAYLOAD.copy()
    payload["invoiceNumber"] = unique
    print(f"DEBUG PAYLOAD: {payload}")
    start_time = time.time()
    # pay = PAYLOAD
    response = await client.post(API_GET_TOKEN, json=PAYLOAD)
    # response = await client.post(API_GET_TOKEN, json=pay)
    end_time = time.time()
    # print("==========")
    # print(pay)

    token = None
    log_entry = {
        "type": "getToken",
        # "token" : pay,
        "invoiceNumber": unique,  # Log the unique invoice number
        "status_code": response.status_code,
        "response_time": round(end_time - start_time, 4),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "response_body": response.text
    }
    print(f"LOG: {log_entry}")  # Print log immediately after calling getToken
    log_list.append(log_entry)

    # Parse token if response is successful
    if response.status_code == 200:
        try:
            data = response.json()
            if data.get("success") and "data" in data:
                token = data["data"].get("token")
        except Exception as e:
            print(f"Error parsing getToken response: {e}")

    """ Step 2: Use Token at Redirect URL """
    if token:
        redirect_url = f"{API_REDIRECT}/{token}"
        start_time_redirect = time.time()
        redirect_response = await client.get(redirect_url)
        end_time_redirect = time.time()

        log_entry_redirect = {
            "type": "redirect",
            # "invoiceNumber": unique_invoice,
            "status_code": redirect_response.status_code,
            "response_time": round(end_time_redirect - start_time_redirect, 4),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "response_body": redirect_response.text,
            "token": token
        }
        print(f"LOG: {log_entry_redirect}")  # Print log immediately after calling redirect
        log_list.append(log_entry_redirect)

async def load_test(requests_per_minute, duration_minutes=1):
    log_data = []
    async with httpx.AsyncClient() as client:
        for _ in range(requests_per_minute * duration_minutes):
            await send_request(client, log_data)
            await asyncio.sleep(60 / requests_per_minute)  # Control request rate
    
    # Save logs after test is completed
    with open(f"test_log_{requests_per_minute}RPM.json", "w") as log_file:
        json.dump(log_data, log_file, indent=4)
    
    print(f"Test completed for {requests_per_minute} requests per minute.")

async def main():
    await load_test(600)
    
asyncio.run(main())
