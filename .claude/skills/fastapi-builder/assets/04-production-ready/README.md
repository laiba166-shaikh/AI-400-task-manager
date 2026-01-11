# Production-Ready FastAPI Structure

This template provides a production-ready FastAPI application structure with best practices for scalability, maintainability, and deployment.

## Project Structure

```
app/
├── core/
│   ├── config.py          # Application settings and configuration
│   ├── database.py        # Database engine and session management
│   ├── security.py        # Authentication and password hashing
│   └── exceptions.py      # Custom exceptions and handlers
├── models/
│   ├── user.py            # User database model
│   └── item.py            # Item database model
├── schemas/
│   ├── user.py            # User Pydantic schemas (request/response)
│   └── item.py            # Item Pydantic schemas
├── crud/
│   ├── user.py            # User CRUD operations
│   └── item.py            # Item CRUD operations
├── routers/
│   ├── auth.py            # Authentication endpoints
│   ├── users.py           # User management endpoints
│   └── items.py           # Item management endpoints
├── services/
│   └── email.py           # Email service (example)
├── dependencies.py        # Shared dependencies
└── main.py                # FastAPI application entry point

tests/
├── conftest.py            # Pytest configuration and fixtures
├── test_users.py          # User endpoint tests
└── test_items.py          # Item endpoint tests

alembic/                   # Database migrations
scripts/                   # Utility scripts
.env.example               # Example environment variables
requirements.txt           # Python dependencies
```

## Key Features

- **Environment-based configuration** using Pydantic Settings
- **Database session management** with dependency injection
- **JWT authentication** with OAuth2 password flow
- **Structured error handling** with custom exceptions
- **CRUD layer separation** for business logic
- **Role-based access control** (RBAC)
- **Comprehensive testing** setup
- **Database migrations** with Alembic
- **CORS middleware** configuration

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   ```

3. Initialize database:
   ```bash
   python scripts/init_db.py
   ```

4. Run migrations (optional):
   ```bash
   alembic upgrade head
   ```

5. Start the development server:
   ```bash
   fastapi dev app/main.py
   ```

## Usage

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Authentication**: POST to `/auth/token` with username/password

## Testing

```bash
pytest
```

## Production Deployment

See deployment documentation for Docker, AWS, GCP, or other platforms.
