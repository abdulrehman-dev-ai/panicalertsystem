# Panic Alert System - Development Guide

## Getting Started

### Prerequisites

#### Required Software
- **Python 3.12+** - Backend development
- **Node.js 18+** - Frontend tooling and React development
- **Flutter SDK 3.16+** - Mobile app development
- **Docker Desktop** - Containerization and local services
- **Git** - Version control
- **VS Code** or **PyCharm** - Recommended IDEs

#### Optional Tools
- **Postman** or **Insomnia** - API testing
- **MongoDB Compass** - MongoDB GUI
- **pgAdmin** - PostgreSQL GUI
- **Kafka Tool** - Kafka cluster management
- **Redis Commander** - Redis GUI

### Environment Setup

#### 1. Clone Repository
```bash
git clone <repository-url>
cd kafka
```

#### 2. Run Setup Script
```powershell
# Windows PowerShell
.\setup-dev.ps1
```

#### 3. Manual Setup (if script fails)
```bash
# Copy environment file
cp .env.example .env

# Create media directory
mkdir -p media/{uploads,processed,temp}

# Start infrastructure services
docker-compose -f infrastructure/docker/docker-compose.yml up -d

# Wait for services to start (30 seconds)
sleep 30

# Create Kafka topics
bash infrastructure/kafka/topics.sh

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install Python dependencies
pip install -r backend/requirements.txt
```

## Development Workflow

### Backend Development

#### Starting the Backend
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Start FastAPI server
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

#### Running Tests
```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# All tests with coverage
pytest --cov=. --cov-report=html
```

#### Code Quality
```bash
# Format code
black .
isort .

# Lint code
flake8 .
mypy .

# Security scan
bandit -r .
```

### Frontend Development

#### Web Portal (React)
```bash
cd web-portal

# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test

# Lint code
npm run lint
```

#### Mobile Apps (Flutter)
```bash
cd mobile/user-app  # or mobile/agent-app

# Get dependencies
flutter pub get

# Run on emulator/device
flutter run

# Build APK
flutter build apk

# Build iOS (Mac only)
flutter build ios

# Run tests
flutter test

# Analyze code
flutter analyze
```

## Project Structure

### Backend Structure
```
backend/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── shared/                 # Shared utilities and configurations
│   ├── config.py          # Application configuration
│   ├── database.py        # Database connections
│   └── kafka_client.py    # Kafka client utilities
├── auth_service/          # Authentication microservice
│   ├── __init__.py
│   ├── models.py          # SQLAlchemy models
│   ├── router.py          # API endpoints
│   └── schemas.py         # Pydantic schemas
├── user_service/          # User management microservice
├── alert_service/         # Alert management microservice
├── geofencing_service/    # Geofencing microservice
├── media_service/         # Media handling microservice
└── tests/                 # Test files
    ├── unit/
    ├── integration/
    └── conftest.py
```

### Frontend Structure
```
web-portal/
├── public/
├── src/
│   ├── components/        # Reusable UI components
│   ├── pages/            # Page components
│   ├── hooks/            # Custom React hooks
│   ├── services/         # API service functions
│   ├── store/            # State management
│   ├── utils/            # Utility functions
│   └── types/            # TypeScript type definitions
├── package.json
└── tsconfig.json
```

### Mobile Structure
```
mobile/user-app/
├── lib/
│   ├── main.dart         # App entry point
│   ├── models/           # Data models
│   ├── screens/          # UI screens
│   ├── widgets/          # Reusable widgets
│   ├── services/         # API and local services
│   ├── providers/        # State management
│   └── utils/            # Utility functions
├── pubspec.yaml          # Flutter dependencies
└── test/                 # Test files
```

## API Development Guidelines

### Endpoint Naming Conventions
- Use RESTful conventions
- Use plural nouns for resources: `/users`, `/alerts`
- Use hyphens for multi-word resources: `/emergency-contacts`
- Use clear, descriptive names

### Request/Response Format
```python
# Standard success response
{
    "success": true,
    "data": {...},
    "message": "Operation completed successfully"
}

# Standard error response
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input data",
        "details": {...}
    }
}

# Paginated response
{
    "success": true,
    "data": [...],
    "pagination": {
        "page": 1,
        "per_page": 20,
        "total": 100,
        "pages": 5
    }
}
```

### Error Handling
```python
# Custom exception classes
class PanicAlertException(Exception):
    def __init__(self, message: str, code: str = "GENERIC_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class ValidationError(PanicAlertException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "VALIDATION_ERROR")
        self.details = details

class AuthenticationError(PanicAlertException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR")
```

### Authentication
```python
# Protected endpoint example
from fastapi import Depends
from auth_service.models import get_current_user, User

@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    return {"success": True, "data": current_user.to_dict()}
```

## Database Guidelines

### Migration Management
```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Check current version
alembic current
```

### Model Conventions
```python
class BaseModel:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
```

### Query Optimization
- Use indexes for frequently queried columns
- Implement pagination for large datasets
- Use select_related/joinedload for related data
- Monitor query performance with EXPLAIN

## Testing Guidelines

### Unit Testing
```python
# Test example
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_user_registration():
    response = client.post("/auth/register/user", json={
        "email": "test@example.com",
        "password": "SecurePass123!",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "+1234567890"
    })
    assert response.status_code == 201
    assert response.json()["success"] is True
```

### Integration Testing
```python
# Database integration test
@pytest.mark.asyncio
async def test_user_creation_database():
    async with get_db_session() as session:
        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        session.add(user)
        await session.commit()
        
        result = await session.get(User, user.id)
        assert result.email == "test@example.com"
```

### Test Data Management
```python
# Fixtures for test data
@pytest.fixture
async def test_user():
    async with get_db_session() as session:
        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        session.add(user)
        await session.commit()
        yield user
        await session.delete(user)
        await session.commit()
```

## Security Guidelines

### Input Validation
- Use Pydantic schemas for all input validation
- Sanitize all user inputs
- Validate file uploads (type, size, content)
- Implement rate limiting on all endpoints

### Authentication & Authorization
- Use JWT tokens with short expiration times
- Implement refresh token rotation
- Store sensitive data in environment variables
- Use HTTPS in production

### Data Protection
- Hash passwords with Argon2
- Encrypt sensitive data at rest
- Use parameterized queries to prevent SQL injection
- Implement proper CORS policies

## Performance Guidelines

### Database Optimization
- Use connection pooling
- Implement query caching
- Use database indexes effectively
- Monitor slow queries

### API Optimization
- Implement response caching
- Use compression for large responses
- Optimize serialization
- Monitor response times

### Kafka Optimization
- Use appropriate partition counts
- Implement proper consumer groups
- Monitor consumer lag
- Use batch processing where appropriate

## Deployment Guidelines

### Docker Best Practices
```dockerfile
# Multi-stage build example
FROM python:3.12-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Configuration
- Use environment-specific configuration files
- Never commit secrets to version control
- Use Docker secrets or external secret management
- Implement health checks for all services

### Monitoring & Logging
- Implement structured logging
- Use correlation IDs for request tracing
- Monitor key business metrics
- Set up alerting for critical issues

## Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check database logs
docker logs kafka-postgres-1

# Test connection
psql -h localhost -p 5432 -U panic_user -d panic_alert_db
```

#### Kafka Issues
```bash
# Check Kafka status
docker ps | grep kafka

# List topics
docker exec kafka-kafka-1 kafka-topics --list --bootstrap-server localhost:9092

# Check consumer groups
docker exec kafka-kafka-1 kafka-consumer-groups --bootstrap-server localhost:9092 --list
```

#### API Issues
```bash
# Check API logs
docker logs backend-container

# Test API health
curl http://localhost:8000/health

# Check API documentation
open http://localhost:8000/docs
```

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# FastAPI debug mode
app = FastAPI(debug=True)
```

## Code Style Guidelines

### Python (Backend)
- Follow PEP 8 style guide
- Use Black for code formatting
- Use isort for import sorting
- Use type hints for all functions
- Maximum line length: 88 characters

### TypeScript (Frontend)
- Use Prettier for code formatting
- Use ESLint for linting
- Use strict TypeScript configuration
- Follow React best practices

### Flutter (Mobile)
- Follow Dart style guide
- Use dart format for formatting
- Use dart analyze for linting
- Follow Flutter best practices

## Git Workflow

### Branch Naming
- `feature/feature-name` - New features
- `bugfix/bug-description` - Bug fixes
- `hotfix/critical-fix` - Critical production fixes
- `refactor/component-name` - Code refactoring

### Commit Messages
```
type(scope): description

Types: feat, fix, docs, style, refactor, test, chore
Scope: auth, user, alert, media, geo, etc.

Examples:
feat(auth): add JWT token refresh endpoint
fix(alert): resolve duplicate alert creation issue
docs(api): update authentication documentation
```

### Pull Request Process
1. Create feature branch from `develop`
2. Implement changes with tests
3. Update documentation if needed
4. Create pull request to `develop`
5. Code review and approval
6. Merge to `develop`
7. Deploy to staging for testing
8. Merge to `main` for production

## Resources

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Flutter Documentation](https://flutter.dev/docs)
- [React Documentation](https://reactjs.org/docs)
- [Kafka Documentation](https://kafka.apache.org/documentation/)

### Tools
- [Postman Collection](./postman/panic-alert-system.json)
- [Database Schema](./database/schema.sql)
- [API Specification](./api/openapi.yaml)

### Support
- **Technical Issues**: Create GitHub issue
- **Questions**: Use team chat or email
- **Documentation**: Update this guide as needed