# Authentication Patterns in FastAPI

## Overview

FastAPI provides built-in support for OAuth2, JWT tokens, API keys, and other authentication methods through security utilities and dependency injection.

## OAuth2 with Password Flow (JWT Tokens)

### Installation

```bash
pip install python-jose[cryptography] passlib[bcrypt] python-multipart
```

### Setup

```python
from datetime import datetime, timedelta
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Configuration
SECRET_KEY = "your-secret-key-here"  # Use environment variable in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

app = FastAPI()
```

### User Model and Schemas

```python
class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None
```

### Password Hashing

```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

### Token Creation and Validation

```python
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
```

### Login Endpoint

```python
@app.post("/auth/token", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user
```

### Protected Routes

```python
@app.get("/users/me", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user

@app.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return [{"item_id": "Foo", "owner": current_user.username}]
```

## API Key Authentication

### Simple API Key

```python
from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader

API_KEY = "your-api-key-here"
API_KEY_NAME = "X-API-Key"

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate API key"
    )

@app.get("/secure-data")
async def get_secure_data(api_key: str = Depends(get_api_key)):
    return {"data": "secret"}
```

### Database-Backed API Keys

```python
from sqlmodel import Session, select

def get_api_key_from_db(api_key: str, session: Session) -> APIKey | None:
    statement = select(APIKey).where(APIKey.key == api_key, APIKey.is_active == True)
    return session.exec(statement).first()

async def validate_api_key(
    api_key: str = Security(api_key_header),
    session: Session = Depends(get_session)
):
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key required"
        )

    db_key = get_api_key_from_db(api_key, session)
    if not db_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )

    return db_key

@app.get("/protected")
async def protected_route(api_key: APIKey = Depends(validate_api_key)):
    return {"message": "Authorized", "key_owner": api_key.owner_id}
```

## Role-Based Access Control (RBAC)

```python
from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class User(BaseModel):
    username: str
    role: Role

def require_role(required_role: Role):
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)]
    ):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role.value} role"
            )
        return current_user
    return role_checker

@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin_user: User = Depends(require_role(Role.ADMIN))
):
    return {"message": f"User {user_id} deleted by {admin_user.username}"}
```

## Permission-Based Access Control

```python
from typing import Callable

class Permission(str, Enum):
    READ_USERS = "read:users"
    WRITE_USERS = "write:users"
    DELETE_USERS = "delete:users"

class User(BaseModel):
    username: str
    permissions: list[Permission]

def require_permission(permission: Permission) -> Callable:
    async def permission_checker(
        current_user: Annotated[User, Depends(get_current_active_user)]
    ):
        if permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission.value}"
            )
        return current_user
    return permission_checker

@app.get("/users/")
async def list_users(
    user: User = Depends(require_permission(Permission.READ_USERS))
):
    return {"users": [...]}

@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    user: User = Depends(require_permission(Permission.DELETE_USERS))
):
    return {"message": "User deleted"}
```

## Refresh Tokens

```python
class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/auth/token", response_model=TokenPair)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials"
        )

    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@app.post("/auth/refresh", response_model=Token)
async def refresh_access_token(refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        username: str = payload.get("sub")
        access_token = create_access_token(data={"sub": username})
        return {"access_token": access_token, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
```

## HTTP Basic Authentication

```python
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

security = HTTPBasic()

def verify_credentials(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, "password")

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/admin/")
def admin_area(username: str = Depends(verify_credentials)):
    return {"message": f"Hello {username}"}
```

## OAuth2 with Social Providers (Google, GitHub)

```python
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()

oauth.register(
    name='google',
    client_id='YOUR_GOOGLE_CLIENT_ID',
    client_secret='YOUR_GOOGLE_CLIENT_SECRET',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@app.get("/auth/google")
async def login_google(request: Request):
    redirect_uri = request.url_for('auth_google_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/google/callback")
async def auth_google_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user = await oauth.google.parse_id_token(request, token)
    # Create session or JWT for user
    return {"email": user.email}
```

## Best Practices

1. **Never store plain passwords**: Always hash with bcrypt or similar
2. **Use environment variables**: Store secrets in .env files, not in code
3. **HTTPS only**: Never send tokens over unencrypted connections
4. **Short token expiry**: Use refresh tokens for long-lived sessions
5. **Validate on every request**: Don't trust client-side validation
6. **Rate limiting**: Prevent brute-force attacks on login endpoints
7. **Secure token storage**: HttpOnly cookies or secure local storage
8. **Logout mechanism**: Invalidate tokens (requires database tracking)
9. **Password requirements**: Enforce minimum length and complexity
10. **Monitor auth failures**: Log and alert on suspicious activity

## Summary

| Method | Use Case | Complexity |
|--------|----------|------------|
| **JWT + OAuth2** | User-facing applications | Medium |
| **API Keys** | Service-to-service, public APIs | Low |
| **HTTP Basic** | Simple internal tools | Very Low |
| **RBAC** | Multi-tenant applications | Medium |
| **Permissions** | Fine-grained access control | High |
| **Social OAuth** | Consumer applications | High |
