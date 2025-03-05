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
