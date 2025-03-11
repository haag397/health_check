import asyncio
import httpx
import time
import logging
import json
import os
from contextlib import asynccontextmanager
from itertools import count
from fastapi import FastAPI, Response, Query, HTTPException
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST, REGISTRY

# *Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# *Set up file logging for failed requests
os.makedirs("logs", exist_ok=True)
failed_logger = logging.getLogger("failed_requests")
failed_handler = logging.FileHandler("logs/failed_requests.log")
failed_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
failed_logger.addHandler(failed_handler)
failed_logger.setLevel(logging.ERROR)

# *Global variables for task management
minute_task = None
metrics_data = ""
last_test_run_time = 0
is_test_running = False  # Flag to prevent concurrent test runs
log_list = []  # To store logs of recent requests
# *Track request counts manually for easier access in status endpoint
request_counts = {
    "getToken": {"success": 0, "failure": 0},
    "redirect": {"success": 0, "failure": 0}
}

# *Constants
API_GET_TOKEN = "https://ipg.gardeshpay.ir/v1/provider/payment/getToken"
API_REDIRECT = "https://ipg.gardeshpay.ir/v1/provider/payment/redirect"
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN", "") 
VALIDATION_TOKEN = os.getenv("VALIDATION_TOKEN", "") 
DEFAULT_CALLBACK_URL = "https://www.google.com"
DEFAULT_AMOUNT = 10000
DEFAULT_INVOICE_DATE = "1403-11-30"
# *Set interval to one minute (60 seconds)
MINUTE_INTERVAL = 60
# *Limit log list size
MAX_LOG_ENTRIES = 1000

invoice_counter = count(start=int(time.time()))

# *Prometheus Metrics setup
REQUEST_COUNT = Counter("payment_api_requests_total", "Total API requests", ["endpoint", "status"])
REQUEST_DURATION = Histogram(
    "payment_api_request_duration_seconds",
    "API request duration",
    ["endpoint"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)
SUCCESS_RATE = Gauge("payment_api_success_rate", "API success rate (%)", ["endpoint"])
LATEST_REQUEST_DURATION = Gauge(
    "payment_api_latest_request_duration_seconds",
    "Latest API request duration",
    ["endpoint"]
)
FAILED_REQUESTS_TOTAL = Counter("payment_api_failed_requests_total", "Total failed API requests", ["endpoint"])
LAST_TEST_TIME = Gauge("payment_api_last_test_timestamp", "Timestamp of the last API call")

# *Function to reset metrics
def reset_metrics():
    """Reset all custom metrics to their initial state."""
    global request_counts
    for metric in [REQUEST_DURATION, REQUEST_COUNT, SUCCESS_RATE, LATEST_REQUEST_DURATION, FAILED_REQUESTS_TOTAL]:
        if hasattr(metric, '_metrics'):
            metric._metrics.clear()
    LAST_TEST_TIME.set(0)
    # *Reset manual counters
    request_counts = {
        "getToken": {"success": 0, "failure": 0},
        "redirect": {"success": 0, "failure": 0}
    }

# *Helper functions
def generate_unique_invoice():
    return str(next(invoice_counter))[:10]  # Ensure 10 digits

def save_failed_request_log(log_entry):
    """Save failed request details to log file with timestamp"""
    try:
        failed_logger.error(json.dumps(log_entry))
    except Exception as e:
        logger.error(f"Error saving failed request log: {e}")

async def send_payment_requests():
    """Send request to getToken API and then to redirect API if token is received."""
    global metrics_data, last_test_run_time, is_test_running, log_list, request_counts
    
    # *Prevent concurrent requests
    if is_test_running:
        logger.info("Request already in progress, skipping this minute")
        return False
    
    is_test_running = True
    unique_invoice = generate_unique_invoice()
    token = None
    current_time_str = time.strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        logger.info(f"Sending scheduled request with invoice {unique_invoice}...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # *STEP 1: Call getToken API
            payload = {
                "token": PROVIDER_TOKEN,
                "invoiceNumber": unique_invoice,
                "invoiceDate": DEFAULT_INVOICE_DATE,
                "amount": DEFAULT_AMOUNT,
                "callback": DEFAULT_CALLBACK_URL,
                "IpAddressNotAllowed": ""
            }
            
            # *Track getToken API call
            start_time = time.time()
            try:
                with REQUEST_DURATION.labels(endpoint="getToken").time():
                    response = await client.post(API_GET_TOKEN, json=payload)
                
                end_time = time.time()
                duration = end_time - start_time
                LATEST_REQUEST_DURATION.labels(endpoint="getToken").set(duration)
                
                # *Log the getToken response
                log_entry = {
                    "type": "getToken",
                    "invoiceNumber": unique_invoice,
                    "status_code": response.status_code,
                    "response_time": round(duration, 4),
                    "timestamp": current_time_str,
                    "success": response.status_code == 200
                }
                
                # *Try to include response body in logs
                try:
                    log_entry["response_body"] = response.text[:500]  # Limit response size
                except Exception:
                    log_entry["response_body"] = "Error extracting response text"
                
                # *Print log immediately and store in history
                logger.info(f"LOG: {json.dumps(log_entry)}")
                log_list.append(log_entry)
                
                # *Limit log list size
                if len(log_list) > MAX_LOG_ENTRIES:
                    log_list = log_list[-MAX_LOG_ENTRIES:]
                
                # *Update metrics
                if response.status_code == 200:
                    REQUEST_COUNT.labels(endpoint="getToken", status="success").inc()
                    request_counts["getToken"]["success"] += 1  # Update manual counter
                    SUCCESS_RATE.labels(endpoint="getToken").set(100)
                    
                    # *Parse token
                    try:
                        data = response.json()
                        if data.get("success") and "data" in data:
                            token = data["data"].get("token")
                            logger.info(f"Successfully obtained token: {token[:10]}...")
                        else:
                            logger.warning(f"API returned success=false: {data}")
                            save_failed_request_log({
                                **log_entry, 
                                "error": "API returned success=false",
                                "data": str(data)
                            })
                    except Exception as e:
                        logger.error(f"Error parsing getToken response: {e}")
                        save_failed_request_log({
                            **log_entry, 
                            "error": f"JSON parse error: {str(e)}"
                        })
                else:
                    REQUEST_COUNT.labels(endpoint="getToken", status="failure").inc()
                    request_counts["getToken"]["failure"] += 1  # Update manual counter
                    FAILED_REQUESTS_TOTAL.labels(endpoint="getToken").inc()
                    SUCCESS_RATE.labels(endpoint="getToken").set(0)
                    save_failed_request_log(log_entry)
                    logger.error(f"getToken request failed with status code {response.status_code}")
                
            except httpx.RequestError as e:
                duration = time.time() - start_time
                LATEST_REQUEST_DURATION.labels(endpoint="getToken").set(duration)
                REQUEST_COUNT.labels(endpoint="getToken", status="failure").inc()
                request_counts["getToken"]["failure"] += 1  # Update manual counter
                FAILED_REQUESTS_TOTAL.labels(endpoint="getToken").inc()
                SUCCESS_RATE.labels(endpoint="getToken").set(0)
                
                error_log = {
                    "type": "getToken",
                    "invoiceNumber": unique_invoice,
                    "error": str(e),
                    "response_time": round(duration, 4),
                    "timestamp": current_time_str,
                    "success": False
                }
                logger.error(f"getToken request error: {e}")
                save_failed_request_log(error_log)
                log_list.append(error_log)
            
            # *STEP 2: Call redirect API if we have a token
            if token:
                redirect_url = f"{API_REDIRECT}/{token}"
                start_time_redirect = time.time()
                
                try:
                    with REQUEST_DURATION.labels(endpoint="redirect").time():
                        redirect_response = await client.get(redirect_url)
                    
                    end_time_redirect = time.time()
                    duration_redirect = end_time_redirect - start_time_redirect
                    LATEST_REQUEST_DURATION.labels(endpoint="redirect").set(duration_redirect)
                    
                    # *Log the redirect response
                    redirect_log_entry = {
                        "type": "redirect",
                        "invoiceNumber": unique_invoice,
                        "token": token[:10] + "...",  # Only log part of the token for security
                        "status_code": redirect_response.status_code,
                        "response_time": round(duration_redirect, 4),
                        "timestamp": current_time_str,
                        "success": redirect_response.status_code == 200
                    }
                    
                    # *Try to include response header info in logs
                    try:
                        redirect_log_entry["content_type"] = redirect_response.headers.get("content-type", "unknown")
                        redirect_log_entry["content_length"] = redirect_response.headers.get("content-length", "unknown")
                    except Exception:
                        pass
                    
                    logger.info(f"LOG: {json.dumps(redirect_log_entry)}")
                    log_list.append(redirect_log_entry)
                    
                    # *Update metrics
                    if redirect_response.status_code == 200:
                        REQUEST_COUNT.labels(endpoint="redirect", status="success").inc()
                        request_counts["redirect"]["success"] += 1  # Update manual counter
                        SUCCESS_RATE.labels(endpoint="redirect").set(100)
                    else:
                        REQUEST_COUNT.labels(endpoint="redirect", status="failure").inc()
                        request_counts["redirect"]["failure"] += 1  # Update manual counter
                        FAILED_REQUESTS_TOTAL.labels(endpoint="redirect").inc()
                        SUCCESS_RATE.labels(endpoint="redirect").set(0)
                        save_failed_request_log(redirect_log_entry)
                        logger.error(f"Redirect request failed with status code {redirect_response.status_code}")
                    
                except httpx.RequestError as e:
                    duration_redirect = time.time() - start_time_redirect
                    LATEST_REQUEST_DURATION.labels(endpoint="redirect").set(duration_redirect)
                    REQUEST_COUNT.labels(endpoint="redirect", status="failure").inc()
                    request_counts["redirect"]["failure"] += 1  # Update manual counter
                    FAILED_REQUESTS_TOTAL.labels(endpoint="redirect").inc()
                    SUCCESS_RATE.labels(endpoint="redirect").set(0)
                    
                    redirect_error_log = {
                        "type": "redirect",
                        "invoiceNumber": unique_invoice,
                        "token": token[:10] + "...",
                        "error": str(e),
                        "response_time": round(duration_redirect, 4),
                        "timestamp": current_time_str,
                        "success": False
                    }
                    logger.error(f"Redirect request error: {e}")
                    save_failed_request_log(redirect_error_log)
                    log_list.append(redirect_error_log)
            else:
                logger.warning("No token received, skipping redirect API call")
                FAILED_REQUESTS_TOTAL.labels(endpoint="redirect").inc()
                request_counts["redirect"]["failure"] += 1  # Update manual counter
                no_token_log = {
                    "type": "redirect_skipped",
                    "invoiceNumber": unique_invoice,
                    "reason": "No token received from getToken API",
                    "timestamp": current_time_str,
                    "success": False
                }
                save_failed_request_log(no_token_log)
                log_list.append(no_token_log)
        
        # *Update the last request timestamp
        current_time = time.time()
        LAST_TEST_TIME.set(current_time)
        last_test_run_time = current_time

        # *Generate Prometheus metrics in text format
        metrics_data = generate_latest().decode("utf-8")
        
        logger.info(f"Request cycle completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        return True
    except Exception as e:
        logger.error(f"Unexpected error in request process: {e}")
        error_log = {
            "type": "system_error",
            "invoiceNumber": unique_invoice,
            "error": str(e),
            "timestamp": current_time_str,
            "success": False
        }
        save_failed_request_log(error_log)
        log_list.append(error_log)
        return False
    finally:
        is_test_running = False

async def scheduled_task():
    """Task that runs the request exactly once per minute."""
    while True:
        try:
            # *Send requests to both APIs
            await send_payment_requests()
            
            # *Calculate the exact time to wait until the next minute
            now = time.time()
            seconds_in_current_minute = time.localtime(now).tm_sec
            wait_time = MINUTE_INTERVAL - seconds_in_current_minute
            if wait_time <= 0:
                wait_time += MINUTE_INTERVAL
                
            logger.info(f"Next scheduled request in {wait_time:.1f} seconds")
            await asyncio.sleep(wait_time)
                
        except asyncio.CancelledError:
            logger.info("Scheduled task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in scheduled task: {e}")
            # *If there's an error, wait 10 seconds and try again
            await asyncio.sleep(10)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # *Start the minutely task when the app starts
    global minute_task
    minute_task = asyncio.create_task(scheduled_task())
    logger.info("Minutely request task started")
    
    yield
    
    # *Cancel the task when the app is shutting down
    if minute_task:
        minute_task.cancel()
        try:
            await minute_task
        except asyncio.CancelledError:
            logger.info("Minutely request task cancelled")

# *Create FastAPI app with lifespan manager
app = FastAPI(title="Payment Gateway API Service with Metrics", lifespan=lifespan)

@app.get("/metrics")
async def get_metrics(validation_token: str = Query(None, alias="validation_token")):
    """Return the most recent metrics only if the validation token matches VALIDATION_TOKEN."""
    global metrics_data, last_test_run_time
    print(PROVIDER_TOKEN)
    print(VALIDATION_TOKEN)
    # *Check if the validation token is correct
    if validation_token != VALIDATION_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid validation token")

    # *If no request has been sent yet, send one immediately
    if last_test_run_time == 0:
        logger.info("First metrics request, sending initial request")
        await send_payment_requests()

    # *Otherwise just return the cached metrics
    return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)

@app.get("/status")
async def status():
    """Return the status of the request scheduling."""
    global request_counts
    
    # Get recent failures
    recent_failures = [log for log in log_list if not log.get("success", False)][-5:]
    
    return {
        "last_request_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_test_run_time)) if last_test_run_time else "Never",
        "time_since_last_request": f"{time.time() - last_test_run_time:.1f} seconds" if last_test_run_time else "N/A",
        "next_scheduled_request": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_test_run_time + MINUTE_INTERVAL)) if last_test_run_time else "ASAP",
        "is_request_in_progress": is_test_running,
        "recent_failures": recent_failures,
        "request_count": request_counts
    }

@app.get("/logs")
async def get_logs(limit: int = 20, failed_only: bool = False):
    """Return recent logs, optionally filtered to show only failures."""
    global log_list
    
    if failed_only:
        filtered_logs = [log for log in log_list if not log.get("success", False)]
    else:
        filtered_logs = log_list
    
    # Return most recent logs first, limited by the 'limit' parameter
    return {"logs": filtered_logs[-limit:]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9090)
