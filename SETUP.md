# Emergency Response System - Setup Guide

## Prerequisites

Before setting up the Emergency Response System, ensure you have the following installed:

### Required Software

1. **Python 3.9+**
   - Download from [python.org](https://www.python.org/downloads/)
   - Make sure to add Python to PATH during installation
   - Verify installation: `python --version` or `py --version`

2. **PostgreSQL 13+**
   - Download from [postgresql.org](https://www.postgresql.org/download/)
   - Create a database named `emergency_response_db`
   - Default credentials: username `postgres`, password `password`

3. **Apache Kafka**
   - Download from [kafka.apache.org](https://kafka.apache.org/downloads)
   - Or use Docker Compose (recommended for development)

4. **Redis** (Optional, for caching)
   - Download from [redis.io](https://redis.io/download)
   - Or use Docker

## Quick Setup with Docker

### 1. Start Infrastructure Services

```bash
# Navigate to the infrastructure directory
cd infrastructure/docker

# Start all services (Kafka, Zookeeper, PostgreSQL, Redis)
docker-compose up -d
```

### 2. Setup Python Environment

```bash
# Navigate back to project root
cd ../..

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
# The default values should work with Docker setup
```

### 4. Initialize Database

```bash
# Run database migrations
alembic upgrade head
```

### 5. Start the Application

```bash
# Start the FastAPI server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Manual Setup (Without Docker)

### 1. Install and Configure PostgreSQL

```sql
-- Connect to PostgreSQL as superuser
CREATE DATABASE emergency_response_db;
CREATE USER emergency_user WITH PASSWORD 'emergency_password';
GRANT ALL PRIVILEGES ON DATABASE emergency_response_db TO emergency_user;
```

### 2. Install and Configure Kafka

```bash
# Start Zookeeper
bin/zookeeper-server-start.sh config/zookeeper.properties

# Start Kafka Server
bin/kafka-server-start.sh config/server.properties

# Create required topics
sh infrastructure/kafka/topics.sh
```

### 3. Install Redis (Optional)

```bash
# Start Redis server
redis-server
```

### 4. Update Environment Configuration

Edit `.env` file with your database and service URLs:

```env
DATABASE_URL=postgresql://emergency_user:emergency_password@localhost:5432/emergency_response_db
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
REDIS_URL=redis://localhost:6379/0
```

## Project Structure

```
kafka/
├── backend/                    # FastAPI backend application
│   ├── agent_service/         # Agent management service
│   ├── alert_service/         # Emergency alert service
│   ├── auth_service/          # Authentication service
│   ├── geofencing_service/    # Geofencing service
│   ├── media_service/         # Media file service
│   ├── user_service/          # User management service
│   ├── config.py              # Application configuration
│   ├── database.py            # Database setup
│   ├── kafka_config.py        # Kafka configuration
│   └── main.py                # FastAPI application entry point
├── alembic/                   # Database migrations
├── infrastructure/            # Infrastructure setup
│   ├── docker/               # Docker configurations
│   └── kafka/                # Kafka topic scripts
├── requirements.txt           # Python dependencies
└── .env.example              # Environment template
```

## API Services

The system includes the following microservices:

### 1. Authentication Service (`/api/v1/auth`)
- User registration and login
- JWT token management
- Password reset functionality

### 2. User Service (`/api/v1/users`)
- User profile management
- Contact and emergency contact management
- User preferences and settings

### 3. Alert Service (`/api/v1/alerts`)
- Emergency alert creation and management
- Alert escalation and notifications
- Alert timeline and metrics

### 4. Geofencing Service (`/api/v1/geofences`)
- Geofence creation and management
- Location-based event triggers
- Geofence analytics and reporting

### 5. Media Service (`/api/v1/media`)
- File upload and management
- Media processing and optimization
- Access control and sharing

### 6. Agent Service (`/api/v1/agents`)
- Emergency responder management
- Incident assignment and tracking
- Agent performance metrics

## Database Schema

The system uses PostgreSQL with the following main entities:

- **Users**: User accounts and profiles
- **Alerts**: Emergency alerts and incidents
- **Geofences**: Geographic boundaries and rules
- **Media**: File attachments and media content
- **Agents**: Emergency responders and authorities
- **Departments**: Organizational units for agents

## Kafka Topics

The system uses the following Kafka topics for real-time messaging:

- `emergency_alerts`: Emergency alert notifications
- `location_updates`: Real-time location updates
- `geofence_events`: Geofence entry/exit events
- `agent_updates`: Agent status and location updates
- `notifications`: Push notifications and messages
- `media_processing`: Media file processing events

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=backend
```

### Code Quality

```bash
# Format code
black backend/

# Sort imports
isort backend/

# Lint code
flake8 backend/

# Type checking
mypy backend/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Production Deployment

### Environment Variables

For production deployment, ensure the following environment variables are properly configured:

```env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-production-secret-key-at-least-32-characters
DATABASE_URL=postgresql://user:password@host:port/database
KAFKA_BOOTSTRAP_SERVERS=kafka1:9092,kafka2:9092,kafka3:9092
REDIS_URL=redis://redis-host:6379/0
```

### Security Considerations

1. Use strong, unique secret keys
2. Enable HTTPS/TLS for all communications
3. Configure proper CORS origins
4. Set up proper database access controls
5. Use environment-specific configurations
6. Enable logging and monitoring

### Scaling

- Use multiple FastAPI workers with Gunicorn
- Scale Kafka partitions based on load
- Implement database read replicas
- Use Redis for session management and caching
- Consider container orchestration (Kubernetes)

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify PostgreSQL is running
   - Check database credentials in `.env`
   - Ensure database exists

2. **Kafka Connection Error**
   - Verify Kafka and Zookeeper are running
   - Check Kafka bootstrap servers configuration
   - Ensure topics are created

3. **Import Errors**
   - Verify virtual environment is activated
   - Check all dependencies are installed
   - Ensure Python path is correct

### Logs

Application logs are written to:
- Console output (development)
- `app.log` file (configurable)

### Health Checks

Monitor system health using:
- `/health` endpoint for overall system status
- Database connection status
- Kafka connection status

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Verify configuration settings
4. Check service dependencies

## License

This project is licensed under the MIT License.