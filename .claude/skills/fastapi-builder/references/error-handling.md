# Error Handling in FastAPI

## Overview

FastAPI provides robust error handling mechanisms with automatic validation errors and custom exception handling.

## HTTP Status Codes for Errors

### 4xx Client Errors

**400 Bad Request**
- Use for: Malformed requests, invalid parameters, business logic violations
- Example: Invalid date format, out-of-range values, missing required headers

**401 Unauthorized**
- Use for: Missing or invalid authentication credentials
- Example: No auth token, expired token, invalid API key

**403 Forbidden**
- Use for: Authenticated user lacks permissions
- Example: User trying to access admin endpoint, insufficient role

**404 Not Found**
- Use for: Resource doesn't exist
- Example: User ID not in database, file not found

**409 Conflict**
- Use for: Request conflicts with current state
- Example: Duplicate email registration, updating deleted resource

**422 Unprocessable Entity** (Default for Pydantic validation)
- Use for: Request is well-formed but fails validation
- Example: Type mismatches, failed Pydantic validators, constraint violations
- **FastAPI automatically returns 422 for Pydantic validation errors**

**429 Too Many Requests**
- Use for: Rate limiting
- Example: Exceeded API rate limit

## 400 vs 422: When to Use Each

| Status | Use When | Example |
|--------|----------|---------|
| **422** | Pydantic validation fails (type errors, constraints) | `{"age": "not a number"}` |
| **400** | Business logic validation fails | `{"age": -5}` after Pydantic validated it's an int |
| **400** | Custom validation errors | Invalid enum value your code checks |
| **400** | Malformed request structure | Invalid JSON, missing required headers |

**Rule of thumb**: Let FastAPI return 422 for Pydantic validation. Use 400 for custom business logic validation.

## HTTPException - Basic Pattern

```python
from fastapi import HTTPException, status

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    item = get_item_from_db(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return item
```

**Key points:**
- Always `raise` HTTPException (never `return`)
- Use `status` module constants for readability
- `detail` accepts any JSON-serializable value

## Structured Error Responses

### Simple String Detail

```python
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Item not found"
)
```

Response:
```json
{
  "detail": "Item not found"
}
```

### Structured Detail (Recommended for Production)

```python
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail={
        "error": "INVALID_DATE_RANGE",
        "message": "Start date must be before end date",
        "params": {
            "start_date": "2024-12-31",
            "end_date": "2024-01-01"
        }
    }
)
```

Response:
```json
{
  "detail": {
    "error": "INVALID_DATE_RANGE",
    "message": "Start date must be before end date",
    "params": {
      "start_date": "2024-12-31",
      "end_date": "2024-01-01"
    }
  }
}
```

## Custom Exception Handlers

### Define Custom Exception

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

class BusinessLogicError(Exception):
    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code

app = FastAPI()

@app.exception_handler(BusinessLogicError)
async def business_logic_exception_handler(
    request: Request,
    exc: BusinessLogicError
):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "path": str(request.url)
        },
    )
```

### Override Validation Error Handler (422)

Convert 422 to 400 with custom formatting:

```python
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"][1:]),
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "errors": errors
        },
    )
```

### Global Error Handler

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the error for debugging
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred"
        },
    )
```

## Error Response Patterns

### Standardized Error Schema

```python
from pydantic import BaseModel

class ErrorDetail(BaseModel):
    field: str
    message: str
    type: str

class ErrorResponse(BaseModel):
    error: str
    message: str
    errors: list[ErrorDetail] | None = None

# Use in responses parameter
@app.post(
    "/items/",
    responses={
        400: {"model": ErrorResponse},
        422: {"model": ErrorResponse}
    }
)
async def create_item(item: ItemCreate):
    ...
```

### Multiple Error Responses

```python
@app.get(
    "/items/{item_id}",
    response_model=Item,
    responses={
        404: {
            "description": "Item not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Item not found"}
                }
            }
        },
        403: {
            "description": "Not enough permissions",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User lacks permission to view this item"
                    }
                }
            }
        }
    }
)
async def read_item(item_id: int):
    ...
```

## Custom Headers in Errors

```python
raise HTTPException(
    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    detail="Rate limit exceeded",
    headers={
        "X-RateLimit-Limit": "100",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": "1640000000"
    }
)
```

## Best Practices

1. **Use status constants**: `status.HTTP_404_NOT_FOUND` instead of `404`
2. **Structured errors**: Return JSON objects with error codes for client error handling
3. **Consistent format**: Define a standard error response schema across your API
4. **Don't leak secrets**: Never expose sensitive data (passwords, tokens) in error messages
5. **Log server errors**: Always log 5xx errors with full context
6. **Document errors**: Use `responses` parameter to document possible errors in OpenAPI
7. **Security consideration**: Use 404 instead of 403 when you want to hide resource existence
8. **Validation separation**: Let Pydantic handle 422, use 400 for business logic validation

## Example: Production-Ready Error Handling

```python
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

app = FastAPI()

# Error response models
class ErrorDetail(BaseModel):
    field: str
    message: str

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: list[ErrorDetail] | None = None

# Custom exceptions
class ItemNotFoundError(Exception):
    pass

class InsufficientPermissionsError(Exception):
    pass

# Exception handlers
@app.exception_handler(ItemNotFoundError)
async def item_not_found_handler(request: Request, exc: ItemNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorResponse(
            error_code="ITEM_NOT_FOUND",
            message="The requested item does not exist"
        ).model_dump()
    )

@app.exception_handler(InsufficientPermissionsError)
async def permissions_handler(request: Request, exc: InsufficientPermissionsError):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=ErrorResponse(
            error_code="INSUFFICIENT_PERMISSIONS",
            message="You don't have permission to perform this action"
        ).model_dump()
    )

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    errors = [
        ErrorDetail(
            field=".".join(str(x) for x in error["loc"][1:]),
            message=error["msg"]
        )
        for error in exc.errors()
    ]

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            details=errors
        ).model_dump()
    )

@app.exception_handler(Exception)
async def global_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred"
        ).model_dump()
    )
```
