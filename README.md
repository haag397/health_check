# health_check

# Payment Gateway API Service

This project is a FastAPI application that performs a load test on a payment gateway API. It sends payment requests to the gateway and checks the responses.
Send request one time per minutes and save failed log in failed_requests.log.
## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/haag397/health_check.git
    cd health_check
    ```
2. Buid docker image:
    ```sh
    docker compose build --no-cache
    ```

## Usage
1. up project:
    ```sh
    docker compose up
    ```
## API Endpoints

### Load Test Endpoint

**URL:** `/metrics`
        curl -X GET "http://localhost:9090/metrics?validation_token=token"

**Method:** `GET`

**Query Parameters:**
- `validation_token` (required): A validation token for API access.

**Response:**
- **Success (200 OK):**
  ```text
    # HELP python_gc_objects_collected_total Objects collected during gc
    # TYPE python_gc_objects_collected_total counter
    python_gc_objects_collected_total{generation="0"} 123179.0
    python_gc_objects_collected_total{generation="1"} 18351.0
    python_gc_objects_collected_total{generation="2"} 0.0
    # HELP python_gc_objects_uncollectable_total Uncollectable objects found during GC
    # TYPE python_gc_objects_uncollectable_total counter
    python_gc_objects_uncollectable_total{generation="0"} 0.0
    python_gc_objects_uncollectable_total{generation="1"} 0.0
    python_gc_objects_uncollectable_total{generation="2"} 0.0
    # HELP python_gc_collections_total Number of times this generation was collected
    # TYPE python_gc_collections_total counter
    python_gc_collections_total{generation="0"} 264.0
    python_gc_collections_total{generation="1"} 24.0
    python_gc_collections_total{generation="2"} 1.0
    # HELP python_info Python platform information
    # TYPE python_info gauge
    python_info{implementation="CPython",major="3",minor="12",patchlevel="9",version="3.12.9"} 1.0
    # HELP process_virtual_memory_bytes Virtual memory size in bytes.
    # TYPE process_virtual_memory_bytes gauge
    process_virtual_memory_bytes 8.026112e+07
    # HELP process_resident_memory_bytes Resident memory size in bytes.
    # TYPE process_resident_memory_bytes gauge
    process_resident_memory_bytes 5.955584e+07
    # HELP process_start_time_seconds Start time of the process since unix epoch in seconds.
    # TYPE process_start_time_seconds gauge
    process_start_time_seconds 1.74152832599e+09
    # HELP process_cpu_seconds_total Total user and system CPU time spent in seconds.
    # TYPE process_cpu_seconds_total counter
    process_cpu_seconds_total 231.36
    # HELP process_open_fds Number of open file descriptors.
    # TYPE process_open_fds gauge
    process_open_fds 9.0
    # HELP process_max_fds Maximum number of open file descriptors.
    # TYPE process_max_fds gauge
    process_max_fds 1.048576e+06
    # HELP payment_api_requests_total Total API requests
    # TYPE payment_api_requests_total counter
    payment_api_requests_total{endpoint="getToken",status="failure"} 49.0
    payment_api_requests_total{endpoint="getToken",status="success"} 956.0
    payment_api_requests_total{endpoint="redirect",status="success"} 956.0
    # HELP payment_api_requests_created Total API requests
    # TYPE payment_api_requests_created gauge
    payment_api_requests_created{endpoint="getToken",status="failure"} 1.74152833238046e+09
    payment_api_requests_created{endpoint="getToken",status="success"} 1.7415283824017098e+09
    payment_api_requests_created{endpoint="redirect",status="success"} 1.7415283824274855e+09
    # HELP payment_api_request_duration_seconds API request duration
    # TYPE payment_api_request_duration_seconds histogram
    payment_api_request_duration_seconds_bucket{endpoint="getToken",le="0.05"} 0.0
    payment_api_request_duration_seconds_bucket{endpoint="getToken",le="0.1"} 0.0
    payment_api_request_duration_seconds_bucket{endpoint="getToken",le="0.25"} 16.0
    payment_api_request_duration_seconds_bucket{endpoint="getToken",le="0.5"} 302.0
    payment_api_request_duration_seconds_bucket{endpoint="getToken",le="1.0"} 518.0
    payment_api_request_duration_seconds_bucket{endpoint="getToken",le="2.5"} 930.0
    payment_api_request_duration_seconds_bucket{endpoint="getToken",le="5.0"} 954.0
    payment_api_request_duration_seconds_bucket{endpoint="getToken",le="10.0"} 1005.0
    payment_api_request_duration_seconds_bucket{endpoint="getToken",le="+Inf"} 1005.0
    payment_api_request_duration_seconds_count{endpoint="getToken"} 1005.0
    payment_api_request_duration_seconds_sum{endpoint="getToken"} 1383.6321134330738
    payment_api_request_duration_seconds_bucket{endpoint="redirect",le="0.05"} 953.0
    payment_api_request_duration_seconds_bucket{endpoint="redirect",le="0.1"} 956.0
    payment_api_request_duration_seconds_bucket{endpoint="redirect",le="0.25"} 956.0
    payment_api_request_duration_seconds_bucket{endpoint="redirect",le="0.5"} 956.0
    payment_api_request_duration_seconds_bucket{endpoint="redirect",le="1.0"} 956.0
    payment_api_request_duration_seconds_bucket{endpoint="redirect",le="2.5"} 956.0
    payment_api_request_duration_seconds_bucket{endpoint="redirect",le="5.0"} 956.0
    payment_api_request_duration_seconds_bucket{endpoint="redirect",le="10.0"} 956.0
    payment_api_request_duration_seconds_bucket{endpoint="redirect",le="+Inf"} 956.0
    payment_api_request_duration_seconds_count{endpoint="redirect"} 956.0
    payment_api_request_duration_seconds_sum{endpoint="redirect"} 22.53184400993814
    # HELP payment_api_request_duration_seconds_created API request duration
    # TYPE payment_api_request_duration_seconds_created gauge
    payment_api_request_duration_seconds_created{endpoint="getToken"} 1.7415283273521945e+09
    payment_api_request_duration_seconds_created{endpoint="redirect"} 1.7415283824020362e+09
    # HELP payment_api_success_rate API success rate (%)
    # TYPE payment_api_success_rate gauge
    payment_api_success_rate{endpoint="getToken"} 100.0
    payment_api_success_rate{endpoint="redirect"} 100.0
    # HELP payment_api_latest_request_duration_seconds Latest API request duration
    # TYPE payment_api_latest_request_duration_seconds gauge
    payment_api_latest_request_duration_seconds{endpoint="getToken"} 1.9152696132659912
    payment_api_latest_request_duration_seconds{endpoint="redirect"} 0.02369976043701172
    # HELP payment_api_failed_requests_total Total failed API requests
    # TYPE payment_api_failed_requests_total counter
    payment_api_failed_requests_total{endpoint="getToken"} 49.0
    payment_api_failed_requests_total{endpoint="redirect"} 49.0
    # HELP payment_api_failed_requests_created Total failed API requests
    # TYPE payment_api_failed_requests_created gauge
    payment_api_failed_requests_created{endpoint="getToken"} 1.741528332380472e+09
    payment_api_failed_requests_created{endpoint="redirect"} 1.7415283323807209e+09
    # HELP payment_api_last_test_timestamp Timestamp of the last API call
    # TYPE payment_api_last_test_timestamp gauge
    payment_api_last_test_timestamp 1.7415885620544076e+09

