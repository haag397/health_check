# health_check

# Payment Gateway API Service

This project is a FastAPI application that performs a load test on a payment gateway API. It sends payment requests to the gateway and checks the responses.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Configuration](#configuration)
- [License](#license)

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/your-username/payment-gateway-api-service.git
    cd payment-gateway-api-service
    ```

2. Create and activate a virtual environment:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Start the FastAPI application:
    ```sh
    uvicorn main:app --host 0.0.0.0 --port 8000
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
