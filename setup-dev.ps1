# Development Setup Script for Panic Alert System
# This script sets up the development environment on Windows

Write-Host "Setting up Panic Alert System Development Environment..." -ForegroundColor Green

# Check if Docker is installed and running
Write-Host "Checking Docker installation..." -ForegroundColor Yellow
try {
    docker --version
    docker-compose --version
    Write-Host "Docker is installed and accessible" -ForegroundColor Green
} catch {
    Write-Host "Error: Docker is not installed or not accessible" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from https://www.docker.com/products/docker-desktop" -ForegroundColor Red
    exit 1
}

# Check if Python is installed
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python is installed: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python is not installed or not accessible" -ForegroundColor Red
    Write-Host "Please install Python 3.12+ from https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env file. Please update it with your configuration." -ForegroundColor Green
} else {
    Write-Host ".env file already exists" -ForegroundColor Green
}

# Create media directory
Write-Host "Creating media directory..." -ForegroundColor Yellow
if (-not (Test-Path "media")) {
    New-Item -ItemType Directory -Path "media"
    Write-Host "Created media directory" -ForegroundColor Green
} else {
    Write-Host "Media directory already exists" -ForegroundColor Green
}

# Start Docker services
Write-Host "Starting Docker services..." -ForegroundColor Yellow
Set-Location "infrastructure/docker"
try {
    docker-compose up -d
    Write-Host "Docker services started successfully" -ForegroundColor Green
} catch {
    Write-Host "Error starting Docker services" -ForegroundColor Red
    Set-Location "../.."
    exit 1
}
Set-Location "../.."

# Wait for services to be ready
Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check if services are running
Write-Host "Checking service status..." -ForegroundColor Yellow
$services = @("postgres", "mongodb", "redis", "kafka", "zookeeper")
foreach ($service in $services) {
    $status = docker ps --filter "name=$service" --format "table {{.Names}}\t{{.Status}}"
    if ($status -match $service) {
        Write-Host "✓ $service is running" -ForegroundColor Green
    } else {
        Write-Host "✗ $service is not running" -ForegroundColor Red
    }
}

# Create Kafka topics
Write-Host "Creating Kafka topics..." -ForegroundColor Yellow
try {
    Set-Location "infrastructure/kafka"
    # Make the script executable and run it
    if (Test-Path "topics.sh") {
        # Convert shell script to PowerShell commands
        Write-Host "Creating Kafka topics..." -ForegroundColor Yellow
        
        $topics = @(
            "panic-alerts",
            "alert-responses", 
            "alert-status-updates",
            "user-events",
            "agent-events",
            "location-updates",
            "geofence-events",
            "media-uploads",
            "media-processing",
            "push-notifications",
            "sms-notifications",
            "email-notifications",
            "system-events",
            "audit-logs"
        )
        
        foreach ($topic in $topics) {
            docker exec kafka kafka-topics --create --topic $topic --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists
        }
        
        Write-Host "Kafka topics created successfully" -ForegroundColor Green
    }
    Set-Location "../.."
} catch {
    Write-Host "Error creating Kafka topics" -ForegroundColor Red
    Set-Location "../.."
}

# Install Python dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
Set-Location "backend"
try {
    # Create virtual environment if it doesn't exist
    if (-not (Test-Path "venv")) {
        python -m venv venv
        Write-Host "Created Python virtual environment" -ForegroundColor Green
    }
    
    # Activate virtual environment and install dependencies
    & ".\venv\Scripts\Activate.ps1"
    pip install --upgrade pip
    pip install -r requirements.txt
    Write-Host "Python dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "Error installing Python dependencies" -ForegroundColor Red
}
Set-Location ".."

# Display service URLs
Write-Host "`nDevelopment Environment Setup Complete!" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Green
Write-Host "Service URLs:" -ForegroundColor Yellow
Write-Host "• Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "• API Documentation: http://localhost:8000/docs" -ForegroundColor White
Write-Host "• Kafka UI: http://localhost:8080" -ForegroundColor White
Write-Host "• PostgreSQL: localhost:5432" -ForegroundColor White
Write-Host "• MongoDB: localhost:27017" -ForegroundColor White
Write-Host "• Redis: localhost:6379" -ForegroundColor White
Write-Host "• Kafka: localhost:9092" -ForegroundColor White
Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "1. Update .env file with your configuration" -ForegroundColor White
Write-Host "2. Run 'cd backend && .\venv\Scripts\Activate.ps1 && python main.py' to start the backend" -ForegroundColor White
Write-Host "3. Access API documentation at http://localhost:8000/docs" -ForegroundColor White
Write-Host "`nTo stop services: docker-compose -f infrastructure/docker/docker-compose.yml down" -ForegroundColor Cyan