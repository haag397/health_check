# health_check

# Payment Gateway API Service

This project is a FastAPI application that performs a load test on a payment gateway API. It sends payment requests to the gateway and checks the responses.

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
    docker-compose build --no-cache
    ```

## Usage
1. up project:
    ```sh
    docker-compose up
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
  python_gc_objects_collected_total{generation="0"} 33683.0
  python_gc_objects_collected_total{generation="1"} 5780.0
  python_gc_objects_collected_total{generation="2"} 617.0
  # HELP python_gc_objects_uncollectable_total Uncollectable objects found during GC
  # TYPE python_gc_objects_uncollectable_total counter
  python_gc_objects_uncollectable_total{generation="0"} 0.0
  python_gc_objects_uncollectable_total{generation="1"} 0.0
  python_gc_objects_uncollectable_total{generation="2"} 0.0
  # HELP python_gc_collections_total Number of times this generation was collected
  # TYPE python_gc_collections_total counter
  python_gc_collections_total{generation="0"} 149.0
  python_gc_collections_total{generation="1"} 13.0
  python_gc_collections_total{generation="2"} 1.0
  # HELP python_info Python platform information
  # TYPE python_info gauge
  python_info{implementation="CPython",major="3",minor="12",patchlevel="3",version="3.12.3"} 1.0
  # HELP process_virtual_memory_bytes Virtual memory size in bytes.
  # TYPE process_virtual_memory_bytes gauge
  process_virtual_memory_bytes 1.49803008e+08
  # HELP process_resident_memory_bytes Resident memory size in bytes.
  # TYPE process_resident_memory_bytes gauge
  process_resident_memory_bytes 5.750784e+07
  # HELP process_start_time_seconds Start time of the process since unix epoch in seconds.
  # TYPE process_start_time_seconds gauge
  process_start_time_seconds 1.74116822119e+09
  # HELP process_cpu_seconds_total Total user and system CPU time spent in seconds.
  # TYPE process_cpu_seconds_total counter
  process_cpu_seconds_total 3.43
  # HELP process_open_fds Number of open file descriptors.
  # TYPE process_open_fds gauge
  process_open_fds 21.0
  # HELP process_max_fds Maximum number of open file descriptors.
  # TYPE process_max_fds gauge
  process_max_fds 1.048576e+06
  # HELP payment_api_requests_total Total API requests
  # TYPE payment_api_requests_total counter
  payment_api_requests_total{status="success"} 164.0
  payment_api_requests_total{status="failure"} 2.0
  # HELP payment_api_requests_created Total API requests
  # TYPE payment_api_requests_created gauge
  payment_api_requests_created{status="success"} 1.7411684638500497e+09
  payment_api_requests_created{status="failure"} 1.7411684767535589e+09
  # HELP payment_api_request_duration_seconds API request duration
  # TYPE payment_api_request_duration_seconds histogram
  payment_api_request_duration_seconds_bucket{le="0.05"} 3.0
  payment_api_request_duration_seconds_bucket{le="0.1"} 3.0
  payment_api_request_duration_seconds_bucket{le="0.25"} 99.0
  payment_api_request_duration_seconds_bucket{le="0.5"} 659.0
  payment_api_request_duration_seconds_bucket{le="1.0"} 661.0
  payment_api_request_duration_seconds_bucket{le="2.5"} 661.0
  payment_api_request_duration_seconds_bucket{le="5.0"} 661.0
  payment_api_request_duration_seconds_bucket{le="10.0"} 661.0
  payment_api_request_duration_seconds_bucket{le="+Inf"} 661.0
  payment_api_request_duration_seconds_count 661.0
  payment_api_request_duration_seconds_sum 191.3132874564035
  # HELP payment_api_request_duration_seconds_created API request duration
  # TYPE payment_api_request_duration_seconds_created gauge
  payment_api_request_duration_seconds_created 1.74116822220035e+09
  # HELP payment_api_success_rate API success rate (%)
  # TYPE payment_api_success_rate gauge
  payment_api_success_rate 20.5
  # HELP payment_api_latency_p50 p50 latency (median)
  # TYPE payment_api_latency_p50 gauge
  payment_api_latency_p50 0.29022812843322754
  # HELP payment_api_latency_p90 p90 latency
  # TYPE payment_api_latency_p90 gauge
  payment_api_latency_p90 0.35930395126342773
  # HELP payment_api_latency_p99 p99 latency
  # TYPE payment_api_latency_p99 gauge
  payment_api_latency_p99 0.41031479835510254
  # HELP payment_api_latest_request_duration_seconds Latest API request duration
  # TYPE payment_api_latest_request_duration_seconds gauge
  payment_api_latest_request_duration_seconds 0.3146860599517822
  # HELP payment_api_total_latency Total sum of request durations (seconds)
  # TYPE payment_api_total_latency gauge
  payment_api_total_latency 47.7893967628479
  # HELP payment_api_avg_latency Average latency of requests (seconds)
  # TYPE payment_api_avg_latency gauge
  payment_api_avg_latency 0.29139876074907256


- **Error (500 Internal server error):**
  ```json
    {
    "detail": {
        "error": "GetToken API failed",
        "status_code": 503,
        "successful_requests_before_error": 62,
        "start_time": "2025-03-02T11:26:59.172321",
        "last_request_time": "2025-03-02T11:27:23.970569"
    }
    }
