# Country Currency & Exchange API

## Overview

This project is a Python-based backend API built with FastAPI, designed to fetch, store, and serve comprehensive data on countries, their currencies, and estimated GDPs. It integrates with external APIs to refresh data and utilizes SQLAlchemy for robust data persistence in a MySQL database.

## Features

- **FastAPI**: Provides a modern, high-performance web framework for building the API endpoints.
- **SQLAlchemy**: Facilitates Object-Relational Mapping (ORM) for efficient and structured database interactions with MySQL.
- **`httpx`**: Enables asynchronous HTTP requests for reliably fetching country and exchange rate data from external APIs.
- **Pillow (PIL)**: Used for dynamic generation of graphical summary reports showcasing key country statistics.
- **`python-dotenv`**: Manages environment variables for secure and flexible configuration.
- **Pydantic**: Ensures strict data validation and serialization for API requests and responses.
- **Uvicorn**: Serves as the high-performance ASGI server for running the FastAPI application.

## Getting Started

### Installation

To set up and run this project locally, follow these steps:

1.  **Clone the Repository**:

    ```bash
    git clone https://github.com/yourusername/country_currency_api.git
    cd country_currency_api
    ```

    (Replace `https://github.com/yourusername/country_currency_api.git` with the actual repository URL.)

2.  **Set up Python Environment**:
    This project is configured for Python 3.13. It is recommended to use a virtual environment.

    ```bash
    python3.13 -m venv venv
    source venv/bin/activate # On Windows use `venv\Scripts\activate`
    ```

3.  **Install Dependencies**:
    The project's dependencies are listed in `pyproject.toml`.

    ```bash
    pip install "asyncio>=4.0.0" "cryptography>=46.0.3" "dotenv>=0.9.9" "fastapi>=0.120.0" "httpx>=0.28.1" "pillow>=12.0.0" "pydantic>=2.12.3" "pymysql>=1.1.2" "sqlalchemy>=2.0.44" "uvicorn>=0.38.0"
    ```

    Alternatively, if you have `poetry` installed, you can use:

    ```bash
    poetry install
    ```

4.  **Database Setup**:
    Ensure you have a MySQL database server running and accessible. The application will create the necessary tables on startup.

5.  **Run the Application**:
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ```
    The API will then be accessible at the specified port, typically `http://localhost:8000`.

## API Documentation

### Base URL

`http://localhost:8000`

### Endpoints

#### POST /countries/refresh

Refreshes the database with the latest country data and exchange rates from external sources, and recalculates estimated GDPs. It also generates an updated summary image.

**Request**:

```
No payload required.
```

**Response**:

```json
{
  "message": "Countries refreshed successfully",
  "total": 250
}
```

**Errors**:

- `503 Service Unavailable`: Occurs if there's an issue fetching data from external APIs.

#### GET /countries

Retrieves a list of all stored countries, with optional filtering and sorting.

**Query Parameters**:

- `region` (string, optional): Filter countries by region (e.g., `Africa`).
- `currency` (string, optional): Filter countries by currency code (e.g., `USD`).
- `sort` (string, optional): Sort the results. Currently supports `gdp_desc` for descending estimated GDP.

**Request**:

```
GET /countries?region=Africa&sort=gdp_desc
```

**Response**:

```json
[
  {
    "name": "Nigeria",
    "capital": "Abuja",
    "region": "Africa",
    "population": 210000000,
    "currency_code": "NGN",
    "id": 1,
    "exchange_rate": 1200.5,
    "estimated_gdp": 250000000000.0,
    "flag_url": "https://restcountries.com/data/nga.svg",
    "last_refreshed_at": "2024-07-20T10:30:00Z"
  }
]
```

**Errors**:

- `422 Unprocessable Entity`: For invalid query parameter types (FastAPI default).

#### GET /countries/image

Retrieves a dynamically generated PNG image summarizing country statistics, including top countries by estimated GDP.

**Request**:

```
No payload required.
```

**Response**:
`image/png` (binary image data)

**Errors**:

- `404 Not Found`: If the summary image has not been generated yet or is missing.

#### GET /countries/{name}

Retrieves detailed information for a specific country by its name.

**Path Parameters**:

- `name` (string, required): The exact name of the country.

**Request**:

```
GET /countries/Nigeria
```

**Response**:

```json
{
  "name": "Nigeria",
  "capital": "Abuja",
  "region": "Africa",
  "population": 210000000,
  "currency_code": "NGN",
  "id": 1,
  "exchange_rate": 1200.5,
  "estimated_gdp": 250000000000.0,
  "flag_url": "https://restcountries.com/data/nga.svg",
  "last_refreshed_at": "2024-07-20T10:30:00Z"
}
```

**Errors**:

- `404 Not Found`: If a country with the specified name is not found in the database.

#### DELETE /countries/{name}

Deletes a country record from the database by its name.

**Path Parameters**:

- `name` (string, required): The exact name of the country to delete.

**Request**:

```
DELETE /countries/Canada
```

**Response**:

```json
{
  "message": "Canada deleted successfully"
}
```

**Errors**:

- `404 Not Found`: If a country with the specified name is not found in the database.

#### GET /status

Retrieves a health check status for the API, including the total number of countries in the database and the timestamp of the last data refresh.

**Request**:

```
No payload required.
```

**Response**:

```json
{
  "total_countries": 100,
  "last_refreshed_at": "2024-07-20T10:30:00Z"
}
```

**Errors**:

- None specific to this endpoint.

## Technologies Used

- **Python 3.13**: The primary programming language.
- **FastAPI**: High-performance, easy-to-use web framework for API development.
- **SQLAlchemy**: Robust SQL toolkit and Object-Relational Mapper (ORM) for database interactions.
- **PyMySQL**: MySQL database connector for SQLAlchemy.
- **`httpx`**: A fully featured asynchronous HTTP client for Python.
- **Pillow (PIL)**: The Python Imaging Library, used for image manipulation and generation.
- **Pydantic**: Data validation and settings management using Python type annotations.
- **`python-dotenv`**: Manages environment variables for configuration.
- **Uvicorn**: An ASGI web server for running asynchronous Python applications.
