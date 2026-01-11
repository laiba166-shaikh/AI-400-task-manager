# HTTP Status Codes Reference for FastAPI

## Quick Reference Table

| Code | Constant | Use When | Common Operations |
|------|----------|----------|-------------------|
| **200** | `HTTP_200_OK` | Successful GET, PUT, or general success | GET, PUT |
| **201** | `HTTP_201_CREATED` | Resource successfully created | POST |
| **204** | `HTTP_204_NO_CONTENT` | Success with no response body | DELETE, PUT |
| **400** | `HTTP_400_BAD_REQUEST` | Invalid request, business logic failure | Any |
| **401** | `HTTP_401_UNAUTHORIZED` | Missing/invalid authentication | Any |
| **403** | `HTTP_403_FORBIDDEN` | User lacks permissions | Any |
| **404** | `HTTP_404_NOT_FOUND` | Resource doesn't exist | GET, PUT, PATCH, DELETE |
| **409** | `HTTP_409_CONFLICT` | Request conflicts with state | POST, PUT |
| **422** | `HTTP_422_UNPROCESSABLE_ENTITY` | Validation error | POST, PUT, PATCH |
| **429** | `HTTP_429_TOO_MANY_REQUESTS` | Rate limit exceeded | Any |
| **500** | `HTTP_500_INTERNAL_SERVER_ERROR` | Server error | Any |
| **503** | `HTTP_503_SERVICE_UNAVAILABLE` | Service temporarily down | Any |

## Import Statement

```python
from fastapi import status
```

## Success Codes (2xx)

### 200 OK

**Use for**: Standard successful response with body

```python
@app.get("/items/{item_id}", status_code=status.HTTP_200_OK)
async def read_item(item_id: int):
    return {"id": item_id, "name": "Item"}
```

**Common operations**: GET, PUT (when updating and returning data)

### 201 Created

**Use for**: Resource successfully created

```python
@app.post("/items/", status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemCreate):
    db_item = create_item_in_db(item)
    return db_item
```

**Common operations**: POST (creating resources)

**Best practice**: Include `Location` header with URL of created resource

```python
from fastapi import Response

@app.post("/items/", status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemCreate, response: Response):
    db_item = create_item_in_db(item)
    response.headers["Location"] = f"/items/{db_item.id}"
    return db_item
```

### 204 No Content

**Use for**: Successful operation with no response body

```python
@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int):
    delete_item_from_db(item_id)
    return None
```

**Common operations**: DELETE, PUT (when updating without returning data)

## Client Error Codes (4xx)

### 400 Bad Request

**Use for**:
- Malformed requests
- Invalid parameters after type validation
- Business logic validation failures
- Custom validation errors

```python
@app.post("/orders/")
async def create_order(order: OrderCreate):
    if order.quantity > available_stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INSUFFICIENT_STOCK",
                "message": f"Only {available_stock} items available",
                "requested": order.quantity,
                "available": available_stock
            }
        )
    return create_order_in_db(order)
```

### 401 Unauthorized

**Use for**: Missing or invalid authentication

```python
from fastapi import Depends, HTTPException

async def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return verify_token(token)
```

**Important**: Include `WWW-Authenticate` header

### 403 Forbidden

**Use for**: Authenticated user lacks permissions

```python
async def get_current_admin(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return user

@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(get_current_admin)
):
    delete_user_from_db(user_id)
    return {"message": "User deleted"}
```

**401 vs 403**:
- 401: "Who are you?" (authentication)
- 403: "I know who you are, but you can't do that" (authorization)

### 404 Not Found

**Use for**: Resource doesn't exist

```python
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    item = get_item_from_db(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found"
        )
    return item
```

**Security tip**: Use 404 instead of 403 when you want to hide resource existence

### 409 Conflict

**Use for**: Request conflicts with current resource state

```python
@app.post("/users/")
async def create_user(user: UserCreate):
    existing = get_user_by_email(user.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "EMAIL_EXISTS",
                "message": "User with this email already exists"
            }
        )
    return create_user_in_db(user)
```

**Common scenarios**:
- Duplicate unique field (email, username)
- Concurrent modification conflicts
- State transition errors (e.g., canceling shipped order)

### 422 Unprocessable Entity

**Use for**: Pydantic validation errors (automatic)

FastAPI automatically returns 422 when Pydantic validation fails:

```python
class ItemCreate(BaseModel):
    name: str
    price: float = Field(gt=0)

@app.post("/items/")  # Automatically returns 422 on validation error
async def create_item(item: ItemCreate):
    return item
```

**Request with invalid data**:
```json
{"name": "Widget", "price": -10}
```

**Response (422)**:
```json
{
  "detail": [
    {
      "loc": ["body", "price"],
      "msg": "Input should be greater than 0",
      "type": "greater_than"
    }
  ]
}
```

**Note**: See error-handling.md for converting 422 to 400

### 429 Too Many Requests

**Use for**: Rate limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/data")
@limiter.limit("5/minute")
async def get_data(request: Request):
    return {"data": "value"}
```

**Best practice**: Include rate limit headers

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

## Server Error Codes (5xx)

### 500 Internal Server Error

**Use for**: Unexpected server errors

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )
```

### 503 Service Unavailable

**Use for**: Service temporarily unavailable (maintenance, overload)

```python
@app.get("/health")
async def health_check():
    if not is_database_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
            headers={"Retry-After": "60"}
        )
    return {"status": "healthy"}
```

## CRUD Operation Status Codes

### Standard CRUD Mapping

| Operation | Method | Success Code | Error Codes |
|-----------|--------|--------------|-------------|
| **Create** | POST | 201 Created | 400, 409, 422 |
| **Read (One)** | GET | 200 OK | 404, 403 |
| **Read (List)** | GET | 200 OK | 400 (invalid filters) |
| **Update (Full)** | PUT | 200 OK | 400, 404, 409, 422 |
| **Update (Partial)** | PATCH | 200 OK | 400, 404, 422 |
| **Delete** | DELETE | 204 No Content | 404, 403 |

### Complete CRUD Example

```python
from fastapi import FastAPI, HTTPException, status

app = FastAPI()

@app.post("/items/", status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemCreate) -> ItemResponse:
    if item_exists(item.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Item already exists"
        )
    return create_item_in_db(item)

@app.get("/items/{item_id}", status_code=status.HTTP_200_OK)
async def read_item(item_id: int) -> ItemResponse:
    item = get_item(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return item

@app.get("/items/", status_code=status.HTTP_200_OK)
async def list_items(
    skip: int = 0,
    limit: int = 100
) -> list[ItemResponse]:
    return get_items(skip=skip, limit=limit)

@app.put("/items/{item_id}", status_code=status.HTTP_200_OK)
async def update_item(
    item_id: int,
    item: ItemUpdate
) -> ItemResponse:
    db_item = get_item(item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return update_item_in_db(item_id, item)

@app.patch("/items/{item_id}", status_code=status.HTTP_200_OK)
async def partial_update_item(
    item_id: int,
    item: ItemUpdate
) -> ItemResponse:
    db_item = get_item(item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    update_data = item.model_dump(exclude_unset=True)
    return update_item_in_db(item_id, update_data)

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int):
    db_item = get_item(item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    delete_item_from_db(item_id)
    return None
```

## Best Practices

1. **Use status constants**: Import from `fastapi.status` instead of magic numbers
2. **Document expected codes**: Use `responses` parameter in route decorators
3. **Be consistent**: Use same codes for same scenarios across your API
4. **Return appropriate codes**: Match HTTP semantics to operation outcomes
5. **Include details**: Provide clear error messages with structured details
6. **Security consideration**: Use 404 to hide resource existence when needed
7. **Follow REST conventions**: Use standard codes for CRUD operations
8. **Log 5xx errors**: Always log server errors for debugging
9. **Rate limiting**: Use 429 with appropriate headers
10. **Validation errors**: Let FastAPI handle 422, use 400 for business logic

## Complete Status Code List

All available status codes in `fastapi.status`:

```python
# 1xx Informational
HTTP_100_CONTINUE
HTTP_101_SWITCHING_PROTOCOLS
HTTP_102_PROCESSING
HTTP_103_EARLY_HINTS

# 2xx Success
HTTP_200_OK
HTTP_201_CREATED
HTTP_202_ACCEPTED
HTTP_203_NON_AUTHORITATIVE_INFORMATION
HTTP_204_NO_CONTENT
HTTP_205_RESET_CONTENT
HTTP_206_PARTIAL_CONTENT
HTTP_207_MULTI_STATUS
HTTP_208_ALREADY_REPORTED
HTTP_226_IM_USED

# 3xx Redirection
HTTP_300_MULTIPLE_CHOICES
HTTP_301_MOVED_PERMANENTLY
HTTP_302_FOUND
HTTP_303_SEE_OTHER
HTTP_304_NOT_MODIFIED
HTTP_305_USE_PROXY
HTTP_306_RESERVED
HTTP_307_TEMPORARY_REDIRECT
HTTP_308_PERMANENT_REDIRECT

# 4xx Client Errors
HTTP_400_BAD_REQUEST
HTTP_401_UNAUTHORIZED
HTTP_402_PAYMENT_REQUIRED
HTTP_403_FORBIDDEN
HTTP_404_NOT_FOUND
HTTP_405_METHOD_NOT_ALLOWED
HTTP_406_NOT_ACCEPTABLE
HTTP_407_PROXY_AUTHENTICATION_REQUIRED
HTTP_408_REQUEST_TIMEOUT
HTTP_409_CONFLICT
HTTP_410_GONE
HTTP_411_LENGTH_REQUIRED
HTTP_412_PRECONDITION_FAILED
HTTP_413_REQUEST_ENTITY_TOO_LARGE
HTTP_414_REQUEST_URI_TOO_LONG
HTTP_415_UNSUPPORTED_MEDIA_TYPE
HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE
HTTP_417_EXPECTATION_FAILED
HTTP_418_IM_A_TEAPOT
HTTP_421_MISDIRECTED_REQUEST
HTTP_422_UNPROCESSABLE_ENTITY
HTTP_423_LOCKED
HTTP_424_FAILED_DEPENDENCY
HTTP_425_TOO_EARLY
HTTP_426_UPGRADE_REQUIRED
HTTP_428_PRECONDITION_REQUIRED
HTTP_429_TOO_MANY_REQUESTS
HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE
HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS

# 5xx Server Errors
HTTP_500_INTERNAL_SERVER_ERROR
HTTP_501_NOT_IMPLEMENTED
HTTP_502_BAD_GATEWAY
HTTP_503_SERVICE_UNAVAILABLE
HTTP_504_GATEWAY_TIMEOUT
HTTP_505_HTTP_VERSION_NOT_SUPPORTED
HTTP_506_VARIANT_ALSO_NEGOTIATES
HTTP_507_INSUFFICIENT_STORAGE
HTTP_508_LOOP_DETECTED
HTTP_510_NOT_EXTENDED
HTTP_511_NETWORK_AUTHENTICATION_REQUIRED
```
