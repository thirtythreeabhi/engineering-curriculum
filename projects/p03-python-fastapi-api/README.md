# Project 03: Modular FastAPI Microservice with Pydantic v2 & JWT Auth

Production-grade asynchronous microservice built using FastAPI and Pydantic v2, featuring lifespan handlers, request-tracing middleware, OAuth2 JWT authentication with fine-grained security scopes, and automated OpenAPI documentation.

## Architectural Features

1. **Pydantic v2 Validation**:
   - Strict typing and custom validators (`@field_validator`, `@model_validator`) for user input sanitation.
   - Distinct request (`ItemCreate`, `ItemUpdate`) and response (`ItemResponse`, `UserResponse`) DTO schemas.

2. **Lifespan Context Management**:
   - Asynchronous `@asynccontextmanager async def lifespan(app: FastAPI)` for clean initialization and shutdown of connection pools.

3. **Request Tracing Middleware**:
   - Intercepts requests, propagates or assigns UUID4 `X-Request-ID`, calculates execution latency, and injects `X-Response-Time-Ms` into the response headers.

4. **JWT Authentication with Fine-Grained Scopes**:
   - OAuth2 Password Bearer flow.
   - Enforces scopes (`read:items`, `write:items`, `admin`) via `Security(get_current_user, scopes=[...])`.
   - Returns HTTP 401 for invalid credentials and HTTP 403 Forbidden for missing scopes.

5. **Self-Documenting OpenAPI**:
   - Interactive Swagger UI at `/docs` and ReDoc at `/redoc`, exporting `/openapi.json`.

## Directory Structure

```
p03-python-fastapi-api/
├── app/
│   ├── auth.py
│   ├── main.py
│   ├── middleware.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── health.py
│   │   └── items.py
│   └── schemas.py
├── README.md
├── requirements.txt
└── tests/
    └── test_api.py
```

## Running the Application

Start the development server with Uvicorn:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Running the Test Suite

```bash
pytest tests/ -v
```
