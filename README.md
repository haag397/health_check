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

2. Create and activate a virtual environment:
    ```sh
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Start the FastAPI application:
    ```sh
    uvicorn service_check:app --host 0.0.0.0 --port 8000
    or only run python3 service_check.py
    ```

## API Endpoints

### Load Test Endpoint

**URL:** `/api/load-test`
        http://127.0.0.1:8002/api/load-test?validation_token=valid_token_123
**Method:** `GET`

**Query Parameters:**
- `validation_token` (required): A validation token for API access.
    sample set token in code ["valid_token_123", "test_token_456"]

**Response:**
- **Success (200 OK):**
  ```json
  {
    "message": "All API calls completed successfully",
    "total_successful_requests": 600,
    "start_time": "2023-04-01T12:00:00",
    "last_request_time": "2023-04-01T12:01:00"
  }

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
