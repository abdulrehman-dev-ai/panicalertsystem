# Panic Alert System - Testing Strategy

## Testing Overview

This document outlines the comprehensive testing strategy for the Panic Alert System, covering all aspects from unit testing to end-to-end testing, performance testing, and security testing.

## Testing Principles

### Core Principles
- **Test-Driven Development (TDD)**: Write tests before implementation
- **Continuous Testing**: Automated testing in CI/CD pipeline
- **Risk-Based Testing**: Focus on critical emergency response features
- **Real-World Scenarios**: Test with realistic emergency situations
- **Performance First**: Ensure sub-second response times
- **Security Focus**: Comprehensive security testing

### Testing Pyramid
```
        ┌─────────────────┐
        │   E2E Tests     │  ← Few, High-Level, Slow
        │   (10-20%)      │
        └─────────────────┘
      ┌───────────────────────┐
      │  Integration Tests    │  ← Some, Mid-Level, Medium
      │     (20-30%)          │
      └───────────────────────┘
    ┌─────────────────────────────┐
    │      Unit Tests             │  ← Many, Low-Level, Fast
    │      (50-70%)               │
    └─────────────────────────────┘
```

## Test Categories

### 1. Unit Testing

#### Backend Unit Tests (Python/FastAPI)

**Test Framework**: pytest, pytest-asyncio

**Coverage Areas**:
- Model validation and business logic
- Service layer functions
- Utility functions
- Data transformations
- Authentication logic

**Example Test Structure**:
```python
# tests/unit/auth_service/test_models.py
import pytest
from auth_service.models import User, TokenManager

class TestUser:
    def test_password_hashing(self):
        user = User(email="test@example.com")
        user.set_password("SecurePass123!")
        assert user.verify_password("SecurePass123!")
        assert not user.verify_password("WrongPassword")
    
    def test_full_name_property(self):
        user = User(first_name="John", last_name="Doe")
        assert user.full_name == "John Doe"
    
    @pytest.mark.asyncio
    async def test_user_creation_validation(self):
        # Test user creation with invalid data
        with pytest.raises(ValidationError):
            User(email="invalid-email")

class TestTokenManager:
    def test_create_access_token(self):
        token_manager = TokenManager()
        token = token_manager.create_access_token(
            data={"sub": "user123", "type": "user"}
        )
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token(self):
        token_manager = TokenManager()
        token = token_manager.create_access_token(
            data={"sub": "user123", "type": "user"}
        )
        payload = token_manager.verify_token(token)
        assert payload["sub"] == "user123"
        assert payload["type"] == "user"
```

**Test Configuration**:
```python
# tests/conftest.py
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from shared.database import Base
from shared.config import settings

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=True
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def test_session(test_engine):
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()
```

#### Frontend Unit Tests (React/TypeScript)

**Test Framework**: Jest, React Testing Library

**Coverage Areas**:
- Component rendering
- User interactions
- State management
- Utility functions
- Custom hooks

**Example Test**:
```typescript
// src/components/__tests__/PanicButton.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { PanicButton } from '../PanicButton';
import { AlertProvider } from '../../contexts/AlertContext';

describe('PanicButton', () => {
  const mockCreateAlert = jest.fn();
  
  beforeEach(() => {
    mockCreateAlert.mockClear();
  });
  
  it('renders panic button correctly', () => {
    render(
      <AlertProvider value={{ createAlert: mockCreateAlert }}>
        <PanicButton />
      </AlertProvider>
    );
    
    expect(screen.getByRole('button', { name: /panic/i })).toBeInTheDocument();
  });
  
  it('triggers alert creation on button press', async () => {
    render(
      <AlertProvider value={{ createAlert: mockCreateAlert }}>
        <PanicButton />
      </AlertProvider>
    );
    
    const panicButton = screen.getByRole('button', { name: /panic/i });
    fireEvent.click(panicButton);
    
    await waitFor(() => {
      expect(mockCreateAlert).toHaveBeenCalledTimes(1);
    });
  });
  
  it('shows loading state during alert creation', async () => {
    mockCreateAlert.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    
    render(
      <AlertProvider value={{ createAlert: mockCreateAlert }}>
        <PanicButton />
      </AlertProvider>
    );
    
    const panicButton = screen.getByRole('button', { name: /panic/i });
    fireEvent.click(panicButton);
    
    expect(screen.getByText(/creating alert/i)).toBeInTheDocument();
  });
});
```

#### Mobile Unit Tests (Flutter/Dart)

**Test Framework**: flutter_test

**Coverage Areas**:
- Widget testing
- Model validation
- Service layer testing
- State management

**Example Test**:
```dart
// test/widgets/panic_button_test.dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:provider/provider.dart';

import 'package:panic_alert_app/widgets/panic_button.dart';
import 'package:panic_alert_app/providers/alert_provider.dart';

class MockAlertProvider extends Mock implements AlertProvider {}

void main() {
  group('PanicButton Widget Tests', () {
    late MockAlertProvider mockAlertProvider;
    
    setUp(() {
      mockAlertProvider = MockAlertProvider();
    });
    
    testWidgets('renders panic button correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AlertProvider>(
            create: (_) => mockAlertProvider,
            child: const PanicButton(),
          ),
        ),
      );
      
      expect(find.byType(ElevatedButton), findsOneWidget);
      expect(find.text('PANIC'), findsOneWidget);
    });
    
    testWidgets('triggers alert creation on tap', (WidgetTester tester) async {
      when(mockAlertProvider.createAlert()).thenAnswer((_) async => true);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AlertProvider>(
            create: (_) => mockAlertProvider,
            child: const PanicButton(),
          ),
        ),
      );
      
      await tester.tap(find.byType(ElevatedButton));
      await tester.pump();
      
      verify(mockAlertProvider.createAlert()).called(1);
    });
  });
}
```

### 2. Integration Testing

#### API Integration Tests

**Test Framework**: pytest with TestClient

**Coverage Areas**:
- API endpoint functionality
- Database interactions
- Authentication flows
- Error handling
- Data validation

**Example Test**:
```python
# tests/integration/test_alert_flow.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestAlertFlow:
    @pytest.fixture
    def authenticated_user(self):
        # Register and login user
        registration_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "first_name": "Test",
            "last_name": "User",
            "phone_number": "+1234567890"
        }
        
        response = client.post("/auth/register/user", json=registration_data)
        assert response.status_code == 201
        
        login_data = {
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
        
        response = client.post("/auth/login/user", json=login_data)
        assert response.status_code == 200
        
        return response.json()["data"]["access_token"]
    
    def test_create_panic_alert(self, authenticated_user):
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        
        alert_data = {
            "type": "panic",
            "location": {
                "latitude": 40.7128,
                "longitude": -74.0060
            },
            "description": "Emergency situation"
        }
        
        response = client.post("/alerts", json=alert_data, headers=headers)
        assert response.status_code == 201
        
        alert = response.json()["data"]
        assert alert["type"] == "panic"
        assert alert["status"] == "active"
        assert "id" in alert
    
    def test_alert_status_update(self, authenticated_user):
        # Create alert first
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        
        alert_data = {
            "type": "panic",
            "location": {"latitude": 40.7128, "longitude": -74.0060}
        }
        
        response = client.post("/alerts", json=alert_data, headers=headers)
        alert_id = response.json()["data"]["id"]
        
        # Update alert status
        status_data = {"status": "responded"}
        response = client.put(
            f"/alerts/{alert_id}/status", 
            json=status_data, 
            headers=headers
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "responded"
```

#### Database Integration Tests

**Coverage Areas**:
- Database schema validation
- Data integrity constraints
- Transaction handling
- Migration testing

**Example Test**:
```python
# tests/integration/test_database.py
import pytest
from sqlalchemy.exc import IntegrityError
from auth_service.models import User, Agent
from alert_service.models import Alert

class TestDatabaseIntegration:
    @pytest.mark.asyncio
    async def test_user_creation_with_constraints(self, test_session):
        # Test unique email constraint
        user1 = User(
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        test_session.add(user1)
        await test_session.commit()
        
        # Try to create another user with same email
        user2 = User(
            email="test@example.com",
            first_name="Another",
            last_name="User"
        )
        test_session.add(user2)
        
        with pytest.raises(IntegrityError):
            await test_session.commit()
    
    @pytest.mark.asyncio
    async def test_alert_user_relationship(self, test_session):
        # Create user
        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        test_session.add(user)
        await test_session.flush()  # Get user ID
        
        # Create alert for user
        alert = Alert(
            user_id=user.id,
            type="panic",
            status="active",
            location_lat=40.7128,
            location_lng=-74.0060
        )
        test_session.add(alert)
        await test_session.commit()
        
        # Verify relationship
        assert alert.user_id == user.id
        assert len(user.alerts) == 1
        assert user.alerts[0].id == alert.id
```

#### Kafka Integration Tests

**Coverage Areas**:
- Message publishing
- Message consumption
- Topic management
- Error handling

**Example Test**:
```python
# tests/integration/test_kafka.py
import pytest
import asyncio
from shared.kafka_client import KafkaClient, KafkaMessage

class TestKafkaIntegration:
    @pytest.mark.asyncio
    async def test_publish_and_consume_alert(self):
        kafka_client = KafkaClient()
        await kafka_client.initialize()
        
        # Test message
        test_message = KafkaMessage(
            event_type="panic_alert_created",
            data={
                "alert_id": "test-alert-123",
                "user_id": "test-user-456",
                "location": {"lat": 40.7128, "lng": -74.0060}
            }
        )
        
        # Publish message
        await kafka_client.publish_alert_event(test_message)
        
        # Set up consumer
        messages_received = []
        
        async def message_handler(message):
            messages_received.append(message)
        
        await kafka_client.setup_alert_consumer(message_handler)
        
        # Wait for message to be consumed
        await asyncio.sleep(2)
        
        # Verify message was received
        assert len(messages_received) == 1
        received_message = messages_received[0]
        assert received_message.event_type == "panic_alert_created"
        assert received_message.data["alert_id"] == "test-alert-123"
        
        await kafka_client.close()
```

### 3. End-to-End Testing

#### Web E2E Tests (Playwright)

**Test Framework**: Playwright

**Coverage Areas**:
- Complete user workflows
- Cross-browser compatibility
- Real user scenarios
- UI interactions

**Example Test**:
```typescript
// tests/e2e/alert-workflow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Alert Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Login as user
    await page.goto('/login');
    await page.fill('[data-testid="email"]', 'test@example.com');
    await page.fill('[data-testid="password"]', 'SecurePass123!');
    await page.click('[data-testid="login-button"]');
    await expect(page).toHaveURL('/dashboard');
  });
  
  test('user can create panic alert', async ({ page }) => {
    // Navigate to panic button
    await page.click('[data-testid="panic-button"]');
    
    // Confirm alert creation
    await page.click('[data-testid="confirm-panic"]');
    
    // Verify alert was created
    await expect(page.locator('[data-testid="alert-status"]'))
      .toContainText('Alert Active');
    
    // Verify alert appears in history
    await page.click('[data-testid="alert-history"]');
    await expect(page.locator('[data-testid="alert-item"]').first())
      .toBeVisible();
  });
  
  test('agent can respond to alert', async ({ page, context }) => {
    // Create alert as user (previous test setup)
    await page.click('[data-testid="panic-button"]');
    await page.click('[data-testid="confirm-panic"]');
    
    // Open new tab as agent
    const agentPage = await context.newPage();
    await agentPage.goto('/agent/login');
    await agentPage.fill('[data-testid="email"]', 'agent@example.com');
    await agentPage.fill('[data-testid="password"]', 'AgentPass123!');
    await agentPage.click('[data-testid="login-button"]');
    
    // Agent sees new alert
    await expect(agentPage.locator('[data-testid="new-alert"]'))
      .toBeVisible();
    
    // Agent responds to alert
    await agentPage.click('[data-testid="respond-button"]');
    await agentPage.fill('[data-testid="response-message"]', 'On my way');
    await agentPage.click('[data-testid="send-response"]');
    
    // Verify user sees agent response
    await expect(page.locator('[data-testid="agent-response"]'))
      .toContainText('On my way');
  });
});
```

#### Mobile E2E Tests (Flutter Integration Tests)

**Test Framework**: flutter_driver

**Coverage Areas**:
- Complete app workflows
- Device-specific features
- Real device testing
- Performance testing

**Example Test**:
```dart
// test_driver/alert_workflow_test.dart
import 'package:flutter_driver/flutter_driver.dart';
import 'package:test/test.dart';

void main() {
  group('Alert Workflow E2E Tests', () {
    late FlutterDriver driver;
    
    setUpAll(() async {
      driver = await FlutterDriver.connect();
    });
    
    tearDownAll(() async {
      await driver.close();
    });
    
    test('user can create and track panic alert', () async {
      // Login
      await driver.tap(find.byValueKey('email_field'));
      await driver.enterText('test@example.com');
      await driver.tap(find.byValueKey('password_field'));
      await driver.enterText('SecurePass123!');
      await driver.tap(find.byValueKey('login_button'));
      
      // Wait for dashboard
      await driver.waitFor(find.byValueKey('dashboard'));
      
      // Trigger panic alert
      await driver.tap(find.byValueKey('panic_button'));
      await driver.tap(find.byValueKey('confirm_panic'));
      
      // Verify alert status
      await driver.waitFor(find.text('Alert Active'));
      
      // Check alert in history
      await driver.tap(find.byValueKey('alert_history_tab'));
      await driver.waitFor(find.byValueKey('alert_item'));
      
      // Verify alert details
      await driver.tap(find.byValueKey('alert_item'));
      await driver.waitFor(find.text('Panic Alert'));
      await driver.waitFor(find.byValueKey('alert_location'));
    });
    
    test('silent alert mode works correctly', () async {
      // Enable silent mode
      await driver.tap(find.byValueKey('settings_tab'));
      await driver.tap(find.byValueKey('silent_mode_toggle'));
      
      // Trigger silent alert
      await driver.tap(find.byValueKey('home_tab'));
      await driver.tap(find.byValueKey('panic_button'));
      
      // Verify no visible confirmation (silent mode)
      await driver.waitForAbsent(find.text('Confirm Panic'));
      
      // Verify alert was still created
      await driver.tap(find.byValueKey('alert_history_tab'));
      await driver.waitFor(find.byValueKey('alert_item'));
    });
  });
}
```

### 4. Performance Testing

#### Load Testing (Locust)

**Coverage Areas**:
- API response times under load
- Database performance
- Kafka throughput
- Concurrent user handling

**Example Test**:
```python
# tests/performance/load_test.py
from locust import HttpUser, task, between
import json
import random

class PanicAlertUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login and get token
        response = self.client.post("/auth/login/user", json={
            "email": f"user{random.randint(1, 1000)}@example.com",
            "password": "SecurePass123!"
        })
        
        if response.status_code == 200:
            self.token = response.json()["data"]["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}
    
    @task(3)
    def view_dashboard(self):
        self.client.get("/users/profile", headers=self.headers)
    
    @task(1)
    def create_panic_alert(self):
        alert_data = {
            "type": "panic",
            "location": {
                "latitude": random.uniform(40.0, 41.0),
                "longitude": random.uniform(-75.0, -73.0)
            },
            "description": "Load test alert"
        }
        
        with self.client.post(
            "/alerts", 
            json=alert_data, 
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Failed to create alert: {response.status_code}")
    
    @task(2)
    def view_alerts(self):
        self.client.get("/alerts", headers=self.headers)
    
    @task(1)
    def update_location(self):
        location_data = {
            "latitude": random.uniform(40.0, 41.0),
            "longitude": random.uniform(-75.0, -73.0),
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        self.client.post(
            "/geofencing/location", 
            json=location_data, 
            headers=self.headers
        )

class AgentUser(HttpUser):
    wait_time = between(2, 5)
    
    def on_start(self):
        # Login as agent
        response = self.client.post("/auth/login/agent", json={
            "email": f"agent{random.randint(1, 100)}@example.com",
            "password": "AgentPass123!"
        })
        
        if response.status_code == 200:
            self.token = response.json()["data"]["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}
    
    @task(5)
    def view_alerts(self):
        self.client.get("/alerts?status=active", headers=self.headers)
    
    @task(2)
    def respond_to_alert(self):
        # Get active alerts
        response = self.client.get("/alerts?status=active", headers=self.headers)
        
        if response.status_code == 200:
            alerts = response.json()["data"]
            if alerts:
                alert_id = alerts[0]["id"]
                
                # Respond to alert
                self.client.put(
                    f"/alerts/{alert_id}/status",
                    json={"status": "responded"},
                    headers=self.headers
                )
```

#### Database Performance Testing

**Coverage Areas**:
- Query performance under load
- Connection pool efficiency
- Index effectiveness
- Transaction throughput

**Example Test**:
```python
# tests/performance/database_performance.py
import asyncio
import time
import pytest
from sqlalchemy import text
from shared.database import get_db_session

class TestDatabasePerformance:
    @pytest.mark.asyncio
    async def test_user_query_performance(self):
        """Test user query performance with large dataset"""
        async with get_db_session() as session:
            # Create test data
            for i in range(10000):
                await session.execute(
                    text("""
                    INSERT INTO users (id, email, first_name, last_name, created_at)
                    VALUES (gen_random_uuid(), :email, :first_name, :last_name, NOW())
                    """),
                    {
                        "email": f"user{i}@example.com",
                        "first_name": f"User{i}",
                        "last_name": "Test"
                    }
                )
            await session.commit()
            
            # Test query performance
            start_time = time.time()
            
            result = await session.execute(
                text("SELECT * FROM users WHERE email LIKE :pattern LIMIT 100"),
                {"pattern": "user1%"}
            )
            users = result.fetchall()
            
            end_time = time.time()
            query_time = end_time - start_time
            
            # Assert performance requirements
            assert query_time < 0.1  # Query should complete in < 100ms
            assert len(users) > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_alert_creation(self):
        """Test concurrent alert creation performance"""
        async def create_alert(session, user_id, alert_num):
            await session.execute(
                text("""
                INSERT INTO alerts (id, user_id, type, status, location_lat, location_lng, created_at)
                VALUES (gen_random_uuid(), :user_id, 'panic', 'active', :lat, :lng, NOW())
                """),
                {
                    "user_id": user_id,
                    "lat": 40.7128 + (alert_num * 0.001),
                    "lng": -74.0060 + (alert_num * 0.001)
                }
            )
        
        # Create test user
        async with get_db_session() as session:
            result = await session.execute(
                text("""
                INSERT INTO users (id, email, first_name, last_name, created_at)
                VALUES (gen_random_uuid(), 'testuser@example.com', 'Test', 'User', NOW())
                RETURNING id
                """)
            )
            user_id = result.fetchone()[0]
            await session.commit()
        
        # Test concurrent alert creation
        start_time = time.time()
        
        tasks = []
        for i in range(100):
            async with get_db_session() as session:
                task = create_alert(session, user_id, i)
                tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Assert performance requirements
        assert total_time < 5.0  # 100 concurrent inserts should complete in < 5 seconds
        throughput = 100 / total_time
        assert throughput > 20  # Should handle > 20 alerts per second
```

### 5. Security Testing

#### Authentication Security Tests

**Coverage Areas**:
- JWT token security
- Password hashing
- Session management
- Authorization checks

**Example Test**:
```python
# tests/security/test_authentication.py
import pytest
import jwt
from fastapi.testclient import TestClient
from main import app
from shared.config import settings

client = TestClient(app)

class TestAuthenticationSecurity:
    def test_password_hashing_security(self):
        """Test password hashing is secure"""
        from auth_service.models import User
        
        user = User(email="test@example.com")
        password = "SecurePass123!"
        user.set_password(password)
        
        # Password should be hashed
        assert user.password_hash != password
        assert len(user.password_hash) > 50  # Argon2 hash length
        assert user.verify_password(password)
        assert not user.verify_password("WrongPassword")
    
    def test_jwt_token_security(self):
        """Test JWT token security"""
        # Register and login
        registration_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "first_name": "Test",
            "last_name": "User",
            "phone_number": "+1234567890"
        }
        
        response = client.post("/auth/register/user", json=registration_data)
        assert response.status_code == 201
        
        login_data = {"email": "test@example.com", "password": "SecurePass123!"}
        response = client.post("/auth/login/user", json=login_data)
        
        token = response.json()["data"]["access_token"]
        
        # Verify token structure
        decoded = jwt.decode(token, options={"verify_signature": False})
        assert "sub" in decoded
        assert "exp" in decoded
        assert "type" in decoded
        
        # Test token expiration
        import time
        time.sleep(1)
        
        # Token should still be valid (not expired yet)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 200
    
    def test_unauthorized_access_prevention(self):
        """Test unauthorized access is prevented"""
        # Try to access protected endpoint without token
        response = client.get("/auth/me")
        assert response.status_code == 401
        
        # Try with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401
        
        # Try with malformed header
        headers = {"Authorization": "InvalidFormat"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401
    
    def test_role_based_access_control(self):
        """Test RBAC is enforced"""
        # Create user and agent
        user_data = {
            "email": "user@example.com",
            "password": "SecurePass123!",
            "first_name": "Test",
            "last_name": "User",
            "phone_number": "+1234567890"
        }
        
        agent_data = {
            "email": "agent@example.com",
            "password": "AgentPass123!",
            "first_name": "Test",
            "last_name": "Agent",
            "badge_number": "AGENT001",
            "department": "Emergency Response"
        }
        
        # Register both
        client.post("/auth/register/user", json=user_data)
        client.post("/auth/register/agent", json=agent_data)
        
        # Login as user
        user_login = client.post("/auth/login/user", json={
            "email": "user@example.com",
            "password": "SecurePass123!"
        })
        user_token = user_login.json()["data"]["access_token"]
        
        # Login as agent
        agent_login = client.post("/auth/login/agent", json={
            "email": "agent@example.com",
            "password": "AgentPass123!"
        })
        agent_token = agent_login.json()["data"]["access_token"]
        
        # User should not access agent-only endpoints
        user_headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get("/agents/dashboard", headers=user_headers)
        assert response.status_code == 403
        
        # Agent should access agent endpoints
        agent_headers = {"Authorization": f"Bearer {agent_token}"}
        response = client.get("/agents/dashboard", headers=agent_headers)
        assert response.status_code == 200
```

#### Input Validation Security Tests

**Coverage Areas**:
- SQL injection prevention
- XSS prevention
- Input sanitization
- File upload security

**Example Test**:
```python
# tests/security/test_input_validation.py
class TestInputValidationSecurity:
    def test_sql_injection_prevention(self):
        """Test SQL injection attacks are prevented"""
        # Try SQL injection in login
        malicious_data = {
            "email": "admin@example.com'; DROP TABLE users; --",
            "password": "password"
        }
        
        response = client.post("/auth/login/user", json=malicious_data)
        # Should return validation error, not execute SQL
        assert response.status_code in [400, 422]
        
        # Verify users table still exists by trying to register
        valid_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "first_name": "Test",
            "last_name": "User",
            "phone_number": "+1234567890"
        }
        
        response = client.post("/auth/register/user", json=valid_data)
        assert response.status_code == 201
    
    def test_xss_prevention(self):
        """Test XSS attacks are prevented"""
        # Register user first
        registration_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "first_name": "<script>alert('xss')</script>",
            "last_name": "User",
            "phone_number": "+1234567890"
        }
        
        response = client.post("/auth/register/user", json=registration_data)
        
        if response.status_code == 201:
            # Login and get profile
            login_data = {"email": "test@example.com", "password": "SecurePass123!"}
            login_response = client.post("/auth/login/user", json=login_data)
            token = login_response.json()["data"]["access_token"]
            
            headers = {"Authorization": f"Bearer {token}"}
            profile_response = client.get("/auth/me", headers=headers)
            
            # Script tags should be escaped or rejected
            profile_data = profile_response.json()["data"]
            assert "<script>" not in profile_data["first_name"]
    
    def test_file_upload_security(self):
        """Test file upload security"""
        # Register and login user
        registration_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "first_name": "Test",
            "last_name": "User",
            "phone_number": "+1234567890"
        }
        
        client.post("/auth/register/user", json=registration_data)
        
        login_data = {"email": "test@example.com", "password": "SecurePass123!"}
        login_response = client.post("/auth/login/user", json=login_data)
        token = login_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to upload malicious file
        malicious_content = b"<?php system($_GET['cmd']); ?>"
        files = {"file": ("malicious.php", malicious_content, "application/x-php")}
        
        response = client.post("/media/upload", files=files, headers=headers)
        
        # Should reject PHP files
        assert response.status_code in [400, 422]
        
        # Try oversized file
        large_content = b"x" * (50 * 1024 * 1024 + 1)  # > 50MB
        files = {"file": ("large.jpg", large_content, "image/jpeg")}
        
        response = client.post("/media/upload", files=files, headers=headers)
        
        # Should reject oversized files
        assert response.status_code in [400, 413, 422]
```

## Test Data Management

### Test Data Strategy

#### Test Data Categories
1. **Static Test Data**: Predefined data for consistent testing
2. **Generated Test Data**: Dynamically generated realistic data
3. **Anonymized Production Data**: Sanitized production data for testing
4. **Synthetic Data**: AI-generated realistic test data

#### Test Data Setup
```python
# tests/fixtures/test_data.py
import pytest
from faker import Faker
import uuid
from datetime import datetime, timedelta

fake = Faker()

@pytest.fixture
def sample_users():
    return [
        {
            "id": str(uuid.uuid4()),
            "email": "john.doe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+1234567890",
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "email": "jane.smith@example.com",
            "first_name": "Jane",
            "last_name": "Smith",
            "phone_number": "+1987654321",
            "created_at": datetime.utcnow()
        }
    ]

@pytest.fixture
def sample_alerts():
    return [
        {
            "id": str(uuid.uuid4()),
            "type": "panic",
            "status": "active",
            "location_lat": 40.7128,
            "location_lng": -74.0060,
            "description": "Emergency situation",
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "type": "medical",
            "status": "responded",
            "location_lat": 40.7589,
            "location_lng": -73.9851,
            "description": "Medical emergency",
            "created_at": datetime.utcnow() - timedelta(hours=1)
        }
    ]

def generate_realistic_user():
    return {
        "id": str(uuid.uuid4()),
        "email": fake.email(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "phone_number": fake.phone_number(),
        "created_at": fake.date_time_between(start_date="-1y", end_date="now")
    }

def generate_realistic_alert(user_id):
    return {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": fake.random_element(["panic", "medical", "fire", "theft"]),
        "status": fake.random_element(["active", "responded", "resolved", "false_alarm"]),
        "location_lat": float(fake.latitude()),
        "location_lng": float(fake.longitude()),
        "description": fake.text(max_nb_chars=200),
        "created_at": fake.date_time_between(start_date="-30d", end_date="now")
    }
```

## Test Environment Management

### Environment Configuration

#### Test Environment Setup
```yaml
# docker-compose.test.yml
version: '3.8'
services:
  test-postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: panic_alert_test
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
    ports:
      - "5433:5432"
    volumes:
      - test_postgres_data:/var/lib/postgresql/data
  
  test-mongodb:
    image: mongo:7
    environment:
      MONGO_INITDB_ROOT_USERNAME: test_admin
      MONGO_INITDB_ROOT_PASSWORD: test_password
      MONGO_INITDB_DATABASE: panic_alert_test
    ports:
      - "27018:27017"
    volumes:
      - test_mongodb_data:/data/db
  
  test-redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"
    command: redis-server --requirepass test_password
  
  test-kafka:
    image: confluentinc/cp-kafka:latest
    environment:
      KAFKA_ZOOKEEPER_CONNECT: test-zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9093
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    ports:
      - "9093:9092"
    depends_on:
      - test-zookeeper
  
  test-zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - "2182:2181"

volumes:
  test_postgres_data:
  test_mongodb_data:
```

#### Test Configuration
```python
# tests/config.py
import os
from shared.config import Settings

class TestSettings(Settings):
    # Override database URLs for testing
    postgres_url: str = "postgresql+asyncpg://test_user:test_password@localhost:5433/panic_alert_test"
    mongodb_url: str = "mongodb://test_admin:test_password@localhost:27018/panic_alert_test"
    redis_url: str = "redis://:test_password@localhost:6380/0"
    
    # Override Kafka settings
    kafka_bootstrap_servers: str = "localhost:9093"
    
    # Test-specific settings
    testing: bool = True
    log_level: str = "DEBUG"
    
    # Disable external services in tests
    enable_sms: bool = False
    enable_email: bool = False
    enable_push_notifications: bool = False

test_settings = TestSettings()
```

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: panic_alert_test
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      mongodb:
        image: mongo:7
        env:
          MONGO_INITDB_ROOT_USERNAME: test_admin
          MONGO_INITDB_ROOT_PASSWORD: test_password
        ports:
          - 27017:27017
      
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r backend/requirements.txt
        pip install pytest-cov pytest-xdist
    
    - name: Set up Kafka
      run: |
        docker run -d --name zookeeper -p 2181:2181 confluentinc/cp-zookeeper:latest
        docker run -d --name kafka -p 9092:9092 --link zookeeper confluentinc/cp-kafka:latest
        sleep 30  # Wait for Kafka to start
    
    - name: Run unit tests
      run: |
        cd backend
        pytest tests/unit/ -v --cov=. --cov-report=xml --cov-report=html
    
    - name: Run integration tests
      run: |
        cd backend
        pytest tests/integration/ -v
    
    - name: Run security tests
      run: |
        cd backend
        pytest tests/security/ -v
        bandit -r . -f json -o bandit-report.json
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
        flags: backend
        name: backend-coverage
    
    - name: Run performance tests
      run: |
        cd backend
        pytest tests/performance/ -v --maxfail=1
  
  frontend-test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: web-portal/package-lock.json
    
    - name: Install dependencies
      run: |
        cd web-portal
        npm ci
    
    - name: Run tests
      run: |
        cd web-portal
        npm test -- --coverage --watchAll=false
    
    - name: Run E2E tests
      run: |
        cd web-portal
        npm run test:e2e
  
  mobile-test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Flutter
      uses: subosito/flutter-action@v2
      with:
        flutter-version: '3.16.0'
    
    - name: Install dependencies
      run: |
        cd mobile/user-app
        flutter pub get
    
    - name: Run tests
      run: |
        cd mobile/user-app
        flutter test --coverage
    
    - name: Run integration tests
      run: |
        cd mobile/user-app
        flutter drive --target=test_driver/app.dart
```

## Test Reporting

### Coverage Reporting

```python
# pytest.ini
[tool:pytest]
addopts = 
    --strict-markers
    --strict-config
    --cov=.
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml
    --cov-fail-under=80
    --junitxml=junit.xml

testpaths = tests
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
    security: Security tests
    slow: Slow running tests
```

### Test Metrics Dashboard

```python
# scripts/generate_test_report.py
import json
import xml.etree.ElementTree as ET
from datetime import datetime

def generate_test_report():
    """Generate comprehensive test report"""
    
    # Parse coverage report
    coverage_data = parse_coverage_xml('coverage.xml')
    
    # Parse test results
    test_results = parse_junit_xml('junit.xml')
    
    # Parse performance results
    performance_data = parse_performance_results('performance_results.json')
    
    # Generate HTML report
    report = {
        'timestamp': datetime.utcnow().isoformat(),
        'coverage': coverage_data,
        'test_results': test_results,
        'performance': performance_data,
        'summary': {
            'total_tests': test_results['total'],
            'passed_tests': test_results['passed'],
            'failed_tests': test_results['failed'],
            'coverage_percentage': coverage_data['line_rate'] * 100,
            'performance_score': calculate_performance_score(performance_data)
        }
    }
    
    # Save report
    with open('test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    # Generate HTML dashboard
    generate_html_dashboard(report)

if __name__ == '__main__':
    generate_test_report()
```

## Best Practices

### Test Writing Guidelines

1. **Test Naming**: Use descriptive test names that explain what is being tested
2. **Test Structure**: Follow Arrange-Act-Assert pattern
3. **Test Independence**: Each test should be independent and idempotent
4. **Test Data**: Use fixtures and factories for test data
5. **Mocking**: Mock external dependencies appropriately
6. **Assertions**: Use specific assertions with clear error messages

### Performance Testing Guidelines

1. **Baseline Metrics**: Establish performance baselines
2. **Realistic Load**: Use realistic user patterns and data volumes
3. **Environment Consistency**: Use consistent test environments
4. **Monitoring**: Monitor system resources during tests
5. **Regression Testing**: Include performance tests in CI/CD

### Security Testing Guidelines

1. **Threat Modeling**: Base tests on identified threats
2. **Input Validation**: Test all input validation thoroughly
3. **Authentication**: Test all authentication mechanisms
4. **Authorization**: Verify role-based access controls
5. **Data Protection**: Test encryption and data handling

## Conclusion

This testing strategy ensures comprehensive coverage of the Panic Alert System, focusing on reliability, performance, and security. Regular execution of these tests will maintain system quality and user safety.