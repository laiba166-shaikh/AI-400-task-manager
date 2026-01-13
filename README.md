# Task Manager API

A production-ready REST API for task management built with FastAPI, SQLModel, and PostgreSQL. This project demonstrates modern Python web development practices with async support, type safety, and clean architecture.

## Features

- **Full CRUD Operations**: Create, read, update, and delete tasks
- **SQLModel Integration**: Unified ORM and validation with type safety
- **Async/Await Support**: Fully asynchronous database operations using asyncpg
- **PostgreSQL Database**: Production database with Neon DB support
- **Automatic API Documentation**: Interactive Swagger UI and ReDoc
- **Repository Pattern**: Clean separation of concerns with CRUD repository
- **Environment Configuration**: Secure configuration management with .env files
- **Health Checks**: Built-in health check endpoint for monitoring

## Tech Stack

- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern, fast web framework for building APIs
- **[SQLModel](https://sqlmodel.tiangolo.com/)** - SQL databases in Python with type safety
- **[PostgreSQL](https://www.postgresql.org/)** - Robust, production-ready database
- **[asyncpg](https://github.com/MagicStack/asyncpg)** - Fast PostgreSQL driver for async operations
- **[Uvicorn](https://www.uvicorn.org/)** - Lightning-fast ASGI server
- **[Pydantic](https://docs.pydantic.dev/)** - Data validation using Python type annotations

## Project Structure

```
tasks_manager/
├── app/
│   ├── routers/
│   │   └── tasks.py          # Task API endpoints
│   ├── crud.py               # CRUD repository for tasks
│   ├── database.py           # Database configuration and session management
│   └── models.py             # SQLModel models (Task, TaskCreate, TaskRead, TaskUpdate)
├── tests/                    # Test suite (pytest)
├── .claude/
│   └── skills/               # Custom Claude Code skills
│       ├── fastapi-builder/  # FastAPI project scaffolding skill
│       ├── pytest-test-suite/# Test generation skill
│       ├── skill-creator/    # Skill development helper
│       └── sql-model-builder/# SQLModel & database patterns skill
├── main.py                   # FastAPI application entry point
├── pyproject.toml           # Project dependencies and metadata
├── .env.example             # Environment variables template
└── README.md                # This file
```

## Custom Claude Code Skills

This project includes custom skills for Claude Code that enhance development workflow:

### 1. **fastapi-builder**
Scaffolds FastAPI projects from hello world to production-ready applications. Handles project structure, API design, best practices, dependency management, testing, and deployment configuration.

### 2. **sql-model-builder**
Builds production-ready SQL data models using SQLModel (SQLAlchemy + Pydantic unified). Provides patterns for database models, session management, CRUD operations, repository patterns, FastAPI integration, migrations (Alembic), and performance optimization.

### 3. **pytest-test-suite**
Generates comprehensive pytest test suites for Python projects. Supports unit, integration, and API testing with fixtures, parametrization, mocking, and coverage reporting.

### 4. **skill-creator**
Helper skill for creating and updating Claude Code skills with best practices and proper structure.

## Prerequisites

- Python 3.12 or higher
- PostgreSQL database (or [Neon](https://neon.tech/) serverless PostgreSQL)
- pip or uv package manager

## Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/laiba166-shaikh/AI-400-task-manager.git
   cd tasks_manager
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv

   # On Windows
   .venv\Scripts\activate

   # On macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   # Using pip
   pip install -e .

   # Or using uv (faster)
   uv pip install -e .

   # For development dependencies
   pip install -e ".[dev]"
   ```

4. **Configure environment variables**

   Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your database connection string:
   ```env
   DATABASE_URL=postgresql+asyncpg://user:password@host:port/database?sslmode=require
   APP_ENV=development
   DEBUG=true
   ```

   **For Neon DB:**
   - Sign up at [neon.tech](https://neon.tech/)
   - Create a new project
   - Copy the connection string from the dashboard
   - Paste it into your `.env` file

## How to Run the Server

### Development Mode

Start the server with auto-reload:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

Start the server without auto-reload:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Access the API

Once the server is running:

- **API Root**: http://localhost:8000/
- **Interactive API Docs (Swagger UI)**: http://localhost:8000/docs
- **Alternative API Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Root
- `GET /` - API welcome message and version info

### Health
- `GET /health` - Health check endpoint

### Tasks
- `POST /tasks/` - Create a new task
- `GET /tasks/` - List all tasks (with pagination)
- `GET /tasks/{task_id}` - Get a specific task by ID
- `PATCH /tasks/{task_id}` - Update a task (partial update)
- `DELETE /tasks/{task_id}` - Delete a task

### Example API Usage

**Create a task:**
```bash
curl -X POST "http://localhost:8000/tasks/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Buy groceries",
    "description": "Milk, eggs, bread",
    "completed": false
  }'
```

**Get all tasks:**
```bash
curl "http://localhost:8000/tasks/"
```

**Update a task:**
```bash
curl -X PATCH "http://localhost:8000/tasks/1" \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'
```

**Delete a task:**
```bash
curl -X DELETE "http://localhost:8000/tasks/1"
```

## Development

### Code Quality

The project uses Ruff for linting and formatting:

```bash
# Check code quality
ruff check .

# Format code
ruff format .
```

### Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_tasks.py -v
```

### Database Migrations

For production deployments, consider using Alembic for database migrations:

```bash
# Initialize Alembic
alembic init alembic

# Create a migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `APP_ENV` | Environment (development/production) | development |
| `DEBUG` | Enable debug mode | true |
| `SQL_ECHO` | Log SQL queries | false |
| `DB_POOL_SIZE` | Database connection pool size | 5 |
| `DB_MAX_OVERFLOW` | Max overflow connections | 10 |

## Architecture Highlights

### SQLModel Pattern
The project uses SQLModel's unified model approach:
- **TaskBase**: Shared fields across all variants
- **Task**: Database table model (with `table=True`)
- **TaskCreate**: API input schema for creation
- **TaskRead**: API output schema for responses
- **TaskUpdate**: API input schema for partial updates

### Repository Pattern
CRUD operations are encapsulated in `TaskRepository` class, providing:
- Clean separation of concerns
- Reusable database operations
- Consistent error handling
- Type-safe queries

### Async/Await
Full async support throughout the stack:
- Async database sessions with asyncpg
- Async FastAPI endpoints
- Non-blocking I/O operations

## Deployment

### Docker Deployment (Coming Soon)

```dockerfile
# Dockerfile example
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -e .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Platform Recommendations

- **[Render](https://render.com/)** - Easy deployment with free tier
- **[Railway](https://railway.app/)** - Simple deployment with PostgreSQL included
- **[Fly.io](https://fly.io/)** - Global edge deployment
- **[Heroku](https://heroku.com/)** - Classic PaaS with PostgreSQL add-on

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Video Tutorial

Watch the complete project walkthrough and demonstration:

[Task Manager API - Project Overview & Demo](https://www.loom.com/share/c6b934e6b3eb4be18a70fc6e40d28e24)

## Resources

### Claude Code Skills Library

Automate repetitive tasks from your daily development workflow with custom Claude Code skills:

[Skills Library Repository](https://github.com/laiba166-shaikh/skills-library)

This repository contains a collection of reusable skills of my repetitive resuable tasks.

---

**Built with ❤️ using FastAPI and SQLModel**
