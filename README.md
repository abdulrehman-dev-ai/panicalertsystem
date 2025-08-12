# Emergency Response System

A comprehensive real-time emergency response and safety monitoring system built with modern cloud-native technologies.

## Overview

The Emergency Response System is designed to provide immediate emergency response capabilities through:
- Real-time location tracking and geofencing
- Instant alert broadcasting to emergency contacts and authorities
- Multi-platform support (Mobile apps, Web portal)
- Scalable microservices architecture
- Real-time data processing with Apache Kafka

## Architecture

### Technology Stack
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Message Broker**: Apache Kafka
- **Cache**: Redis
- **Mobile**: Flutter (iOS/Android)
- **Web Portal**: React.js
- **Infrastructure**: Docker, Kubernetes

### System Components

1. **User Mobile Application**
   - Emergency panic button
   - Real-time location sharing
   - Contact management
   - Alert history

2. **Agent Mobile Application**
   - Emergency response interface
   - Real-time incident tracking
   - Communication tools
   - Route optimization

3. **Web Administration Portal**
   - System monitoring and analytics
   - User and agent management
   - Geofence configuration
   - Report generation

4. **Backend Services**
   - Authentication & Authorization
   - User Management
   - Alert Processing
   - Geofencing
   - Media Handling
   - Agent Management
   - Real-time Notifications

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.9+
- Node.js 16+ (for web portal)
- Flutter SDK (for mobile apps)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd emergency-response-system
   ```

2. **Start infrastructure services**
   ```bash
   cd infrastructure/docker
   docker-compose up -d
   ```

3. **Setup backend**
   ```bash
   cd ../../
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the backend server**
   ```bash
   uvicorn backend.main:app --reload
   ```

The API will be available at `http://localhost:8000`

## Project Structure

```
emergency-response-system/
├── backend/                    # FastAPI backend services
│   ├── auth_service/          # Authentication service
│   ├── user_service/          # User management
│   ├── alert_service/         # Alert processing
│   ├── geofencing_service/    # Geofencing logic
│   ├── media_service/         # File handling
│   ├── agent_service/         # Agent management
│   ├── config.py              # Application configuration
│   ├── database.py            # Database setup
│   ├── kafka_config.py        # Kafka configuration
│   └── main.py                # FastAPI application
├── mobile/
│   ├── user-app/              # User mobile application
│   └── agent-app/             # Agent mobile application
├── web-portal/                # React admin portal
├── infrastructure/            # Infrastructure setup
│   ├── docker/               # Docker configurations
│   ├── kafka/                # Kafka setup
│   └── databases/            # Database configurations
├── alembic/                   # Database migrations
├── docs/                      # Documentation
├── requirements.txt           # Python dependencies
├── SETUP.md                   # Detailed setup guide
└── README.md                  # This file
```

## Features

### Core Features
- **Emergency Alerts**: One-touch panic button with automatic location sharing
- **Real-time Tracking**: Continuous location monitoring and geofencing
- **Multi-channel Notifications**: SMS, Email, Push notifications, and in-app alerts
- **Contact Management**: Emergency contacts with priority levels
- **Incident Management**: Complete incident lifecycle tracking
- **Agent Dispatch**: Automatic assignment of nearby emergency responders
- **Media Attachments**: Photo, video, and audio evidence collection

### Advanced Features
- **Geofencing**: Custom safe zones and restricted areas with smart triggers
- **Escalation Rules**: Automatic escalation based on response time and severity
- **Analytics Dashboard**: Real-time monitoring and historical reports
- **Multi-tenant Support**: Organization-level isolation and management
- **API Integration**: RESTful APIs for third-party integrations
- **Performance Metrics**: Agent and system performance tracking
- **Template System**: Predefined alert and geofence templates

## API Documentation

Once the backend is running, access the interactive API documentation at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/health`

### Main API Endpoints

#### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User authentication
- `POST /api/v1/auth/refresh` - Refresh access token

#### Emergency Alerts
- `POST /api/v1/alerts/emergency` - Trigger emergency alert
- `GET /api/v1/alerts` - List user alerts
- `PUT /api/v1/alerts/{id}/status` - Update alert status

#### User Management
- `GET /api/v1/users/profile` - Get user profile
- `PUT /api/v1/users/profile` - Update user profile
- `POST /api/v1/users/contacts` - Add emergency contact

#### Geofencing
- `POST /api/v1/geofences` - Create geofence
- `GET /api/v1/geofences` - List user geofences
- `PUT /api/v1/geofences/{id}` - Update geofence

#### Agent Management
- `GET /api/v1/agents/nearby` - Find nearby agents
- `POST /api/v1/agents/incidents` - Assign incident to agent
- `PUT /api/v1/agents/status` - Update agent status

#### Media
- `POST /api/v1/media/upload` - Upload media file
- `GET /api/v1/media/{id}` - Get media file
- `DELETE /api/v1/media/{id}` - Delete media file

## Development

### Backend Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Code formatting
black backend/
isort backend/

# Linting
flake8 backend/

# Type checking
mypy backend/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Check current revision
alembic current
```

### Kafka Topics

The system uses the following Kafka topics:
- `emergency_alerts` - Emergency alert events
- `location_updates` - Real-time location data
- `geofence_events` - Geofence entry/exit events
- `agent_updates` - Agent status and location updates
- `notifications` - Notification delivery events
- `media_processing` - Media file processing events

## Database Schema

The system uses PostgreSQL with the following main entities:

### Core Tables
- **users** - User accounts and profiles
- **alerts** - Emergency alerts and incidents
- **geofences** - Geographic boundaries and rules
- **media_files** - File attachments and media content
- **agents** - Emergency responders and authorities
- **departments** - Organizational units for agents

### Supporting Tables
- **alert_timeline_events** - Alert progression tracking
- **geofence_events** - Geofence trigger events
- **agent_incidents** - Agent-incident assignments
- **media_collections** - Organized media groups
- **performance_metrics** - System and agent metrics

## Deployment

### Production Deployment

1. **Environment Configuration**
   ```bash
   # Set production environment variables
   export ENVIRONMENT=production
   export DATABASE_URL=postgresql://...
   export KAFKA_BOOTSTRAP_SERVERS=...
   export SECRET_KEY=your-production-secret-key
   ```

2. **Database Setup**
   ```bash
   # Run migrations
   alembic upgrade head
   ```

3. **Start Services**
   ```bash
   # Using Docker Compose
   docker-compose -f docker-compose.prod.yml up -d
   
   # Or using Gunicorn
   gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

### Monitoring

- **Health Checks**: `GET /health`
- **Metrics**: Application metrics and monitoring
- **Logs**: Structured logging with correlation IDs
- **Performance**: Response time and throughput monitoring

## Security

- **Authentication**: JWT-based authentication with refresh tokens
- **Authorization**: Role-based access control (RBAC)
- **Data Encryption**: TLS in transit, secure password hashing
- **Input Validation**: Comprehensive request validation with Pydantic
- **Rate Limiting**: API rate limiting and abuse protection
- **CORS**: Configurable cross-origin resource sharing
- **File Security**: Secure file upload and validation

## Testing

### Running Tests

```bash
# Backend tests
pytest tests/ -v --cov=backend

# Integration tests
pytest tests/integration/ -v

# Specific test file
pytest tests/test_alerts.py -v
```

### Test Coverage

- Unit tests for all business logic
- Integration tests for API endpoints
- End-to-end tests for critical workflows
- Database transaction testing
- Kafka message testing

## Performance

### Optimization Features
- Database connection pooling
- Redis caching for frequently accessed data
- Kafka for asynchronous processing
- Efficient database queries with proper indexing
- File compression and optimization
- Background task processing

### Scalability
- Horizontal scaling with multiple FastAPI workers
- Database read replicas for read-heavy operations
- Kafka partitioning for high-throughput messaging
- Microservices architecture for independent scaling
- Container orchestration support

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Write comprehensive tests for new features
- Update documentation for API changes
- Use conventional commit messages
- Ensure all CI checks pass
- Add type hints for better code quality

## Documentation

- **Setup Guide**: [SETUP.md](SETUP.md) - Detailed installation and configuration
- **API Documentation**: Available at `/docs` when running the server
- **Architecture**: [docs/architecture.md](docs/architecture.md)
- **Development Guide**: [docs/development-guide.md](docs/development-guide.md)
- **Testing Strategy**: [docs/testing-strategy.md](docs/testing-strategy.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the [SETUP.md](SETUP.md) for detailed setup instructions
- Review the API documentation at `/docs`
- Check the troubleshooting section in SETUP.md

## Roadmap

### Phase 1 (Current)
- [x] Core backend API development
- [x] Database schema and migrations
- [x] Kafka integration
- [x] Authentication and authorization
- [x] Basic CRUD operations for all services

### Phase 2 (Next)
- [ ] Mobile application development (Flutter)
- [ ] Web portal implementation (React)
- [ ] Real-time WebSocket connections
- [ ] Push notification integration
- [ ] Advanced geofencing features

### Phase 3 (Future)
- [ ] Advanced analytics and reporting
- [ ] Machine learning for predictive alerts
- [ ] Integration with external emergency services
- [ ] Multi-language support
- [ ] Offline-first mobile capabilities
- [ ] Advanced monitoring and observability