import asyncio
import httpx
import time
import json

API_GET_TOKEN = "https://ipg.gardeshpay.ir/v1/provider/payment/getToken"
PAYLOAD = {
    "token": "mCamaJWoeSpswUnbpYZARJiJjCWGaZ",
    "invoiceNumber": "Testsheyda",
    "invoiceDate": "1403-11-30",
    "amount": 10000,
    "callback": "https://www.google.com",
    "IpAddressNotAllowed": ""
}

async def send_request(client, log_list):
    """ Step 1: Get Token """
    start_time = time.time()
    response = await client.post(API_GET_TOKEN, json=PAYLOAD)
    end_time = time.time()

    token = None
    log_entry = {
        "type": "getToken",
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

async def load_test(requests_per_minute, duration=1):
    log_data = []
    async with httpx.AsyncClient() as client:
        for _ in range(requests_per_minute * duration):
            await send_request(client, log_data)
            await asyncio.sleep(60 / requests_per_minute)  # Control the request rate
    
    with open(f"test_log_{requests_per_minute}.json", "w") as log_file:
        json.dump(log_data, log_file, indent=4)
    
    print(f"Test completed for {requests_per_minute} requests per minute.")

async def main():
    await load_test(600)

asyncio.run(main())
