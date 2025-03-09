

import asyncio
import httpx
import time
from fastapi import FastAPI, Response, BackgroundTasks
from contextlib import asynccontextmanager
from pydantic import BaseModel
from itertools import count
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Global variables for task management
hourly_task = None
metrics_data = ""
last_test_run_time = 0

# Constants
API_GET_TOKEN = "https://ipg.gardeshpay.ir/v1/provider/payment/getToken"
PROVIDER_TOKEN = "mCamaJWoeSpswUnbpYZARJiJjCWGaZ"
DEFAULT_REQUESTS_PER_MINUTE = 800
DEFAULT_DURATION_SECONDS = 60
DEFAULT_CALLBACK_URL = "https://www.google.com"
DEFAULT_AMOUNT = 10000
DEFAULT_INVOICE_DATE = "1403-11-30"

invoice_counter = count(start=int(time.time()))

# Prometheus Metrics setup
REQUEST_COUNT = Counter("payment_api_requests_total", "Total API requests", ["status"])
REQUEST_DURATION = Histogram(
    "payment_api_request_duration_seconds",
    "API request duration",
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)
SUCCESS_RATE = Gauge("payment_api_success_rate", "API success rate (%)")
P50_LATENCY = Gauge("payment_api_latency_p50", "p50 latency (median)")
P90_LATENCY = Gauge("payment_api_latency_p90", "p90 latency")
P99_LATENCY = Gauge("payment_api_latency_p99", "p99 latency")
LATEST_REQUEST_DURATION = Gauge(
    "payment_api_latest_request_duration_seconds",
    "Latest API request duration")
TOTAL_LATENCY = Gauge("payment_api_total_latency", "Total sum of request durations (seconds)")
AVERAGE_LATENCY = Gauge("payment_api_avg_latency", "Average latency of requests (seconds)")

# Function to reset metrics
def reset_metrics():
    """Reset all custom metrics to their initial state."""
    REQUEST_DURATION._metrics = {}
    REQUEST_COUNT._metrics.clear()
    SUCCESS_RATE.set(0)
    P50_LATENCY.set(0)
    P90_LATENCY.set(0)
    P99_LATENCY.set(0)
    LATEST_REQUEST_DURATION.set(0)
    TOTAL_LATENCY.set(0)
    AVERAGE_LATENCY.set(0)

# Helper functions
def generate_unique_invoice():
    return str(next(invoice_counter))[:10]  # Ensure 10 digits

async def send_payment_request(client, unique_invoice, callback_url, amount, invoice_date):
    payload = {
        "token": PROVIDER_TOKEN,
        "invoiceNumber": unique_invoice,
        "invoiceDate": invoice_date,
        "amount": amount,
        "callback": callback_url,
        "IpAddressNotAllowed": ""
    }
    start_time = time.time()
    try:
        with REQUEST_DURATION.time():
            response = await client.post(API_GET_TOKEN, json=payload)
    except httpx.RequestError as e:
        duration = time.time() - start_time
        LATEST_REQUEST_DURATION.set(duration)
        REQUEST_COUNT.labels(status="failure").inc()
        return {"success": False, "latency": duration, "error": str(e)}

    duration = time.time() - start_time
    LATEST_REQUEST_DURATION.set(duration)
    if response.status_code != 200:
        REQUEST_COUNT.labels(status="failure").inc()
        return {"success": False, "latency": duration}

    REQUEST_COUNT.labels(status="success").inc()
    return {"success": True, "latency": duration}

async def run_load_test():
    global metrics_data, last_test_run_time
    
    # Reset all metrics before starting the test
    reset_metrics()

    successful_requests = 0
    latencies = []
    total_requests = DEFAULT_REQUESTS_PER_MINUTE
    duration_seconds = DEFAULT_DURATION_SECONDS
    start_time = time.time()

    async with httpx.AsyncClient() as client:
        for _ in range(total_requests):
            unique_invoice = generate_unique_invoice()
            result = await send_payment_request(
                client, unique_invoice, DEFAULT_CALLBACK_URL, DEFAULT_AMOUNT, DEFAULT_INVOICE_DATE
            )
            if result["success"]:
                successful_requests += 1
                latencies.append(result["latency"])
            if time.time() - start_time >= duration_seconds:
                break
            await asyncio.sleep(duration_seconds / total_requests)

    # Calculate success rate and latency percentiles
    success_rate = (successful_requests / total_requests) * 100 if total_requests else 0
    total_latency = sum(latencies)
    avg_latency = total_latency / len(latencies) if latencies else 0
    
    # Sort latencies for percentile calculations
    if latencies:
        sorted_latencies = sorted(latencies)
        latency_p50 = sorted_latencies[int(len(sorted_latencies) * 0.5)]
        latency_p90 = sorted_latencies[int(len(sorted_latencies) * 0.9)]
        latency_p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]
    else:
        latency_p50 = latency_p90 = latency_p99 = 0

    # Update Prometheus metrics
    SUCCESS_RATE.set(success_rate)
    P50_LATENCY.set(latency_p50)
    P90_LATENCY.set(latency_p90)
    P99_LATENCY.set(latency_p99)
    TOTAL_LATENCY.set(total_latency)
    AVERAGE_LATENCY.set(avg_latency)

    # Generate Prometheus metrics in text format
    metrics_data = generate_latest().decode("utf-8")
    last_test_run_time = time.time()
    
    print(f"Load test completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Success rate: {success_rate:.2f}%, Avg latency: {avg_latency:.2f}s")

async def scheduled_task():
    """Task that runs the load test every hour."""
    while True:
        try:
            await run_load_test()
            # Wait for 1 hour (3600 seconds)
            await asyncio.sleep(3600)
            # await asyncio.sleep(300)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Error in scheduled task: {e}")
            await asyncio.sleep(60)  # Wait a minute before retrying

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the hourly task when the app starts
    global hourly_task
    hourly_task = asyncio.create_task(scheduled_task())
    print("Hourly metrics collection task started")
    
    yield
    
    # Cancel the task when the app is shutting down
    if hourly_task:
        hourly_task.cancel()
        try:
            await hourly_task
        except asyncio.CancelledError:
            print("Hourly metrics collection task cancelled")

# Create FastAPI app with lifespan manager
app = FastAPI(title="Payment Gateway API Service with Metrics", lifespan=lifespan)

@app.get("/metrics")
async def get_metrics():
    """Return the most recent metrics without running a new test."""
    global metrics_data, last_test_run_time
    
    # If no test has been run yet or it's been more than an hour, run a new test
    current_time = time.time()
    if last_test_run_time == 0 or (current_time - last_test_run_time) > 3600:
        print("time:",current_time)
        await run_load_test()
    
    return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)

@app.get("/force_test")
async def force_test(background_tasks: BackgroundTasks):
    """Force a new load test to run."""
    background_tasks.add_task(run_load_test)
    return {"message": "Load test started in the background"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9090)
