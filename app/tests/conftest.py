import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool # For SQLite in-memory
import os

from app.main import app # Main FastAPI app
from app.database import Base, get_db # Base for creating tables, get_db to override
from app.auth import get_current_user_data # To override auth
from app import models, schemas # For creating mock user data

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}, # Needed for SQLite
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables in the in-memory database before tests run
Base.metadata.create_all(bind=engine)

def override_get_db():
    """Dependency override for database session."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

MOCK_USER_ID = "test-user-uuid-123"
MOCK_USER_EMAIL = "testuser@example.com"

async def override_get_current_user_data():
    """Dependency override for authentication. Returns a mock user."""
    # This mock user should exist in the test DB for FK constraints if SIPs are added.
    # We can add it here or ensure tests that need it handle its creation.
    # For simplicity, this returns a models.User object directly.
    # In a real scenario, ensure this user is in the test DB if your logic needs it.
    return models.User(id=MOCK_USER_ID, email=MOCK_USER_EMAIL)

@pytest.fixture(scope="function")
def db_session():
    """Fixture to provide a test database session per test function."""
    # Create tables for each test function if they were dropped, or clean up data.
    # For SQLite in-memory with StaticPool, the DB is fresh per engine instance.
    # If sharing engine, then Base.metadata.create_all(bind=engine) might be needed here
    # or Base.metadata.drop_all/create_all for true isolation if not using transactions.
    # For this setup, tables are created once. Data needs cleanup or transactional tests.

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        # Clean up data after test. This is a simple way.
        # For more complex scenarios, consider database transaction strategies.
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
        db.close()

@pytest.fixture(scope="function")
def client(db_session): # Pass db_session to ensure it runs and cleans up
    """Fixture to provide a TestClient with overridden dependencies."""
    app.dependency_overrides[get_db] = lambda: db_session # Use the session from db_session fixture
    app.dependency_overrides[get_current_user_data] = override_get_current_user_data

    # Pre-populate the mock user in the database for this client session
    # This ensures the user identified by override_get_current_user_data exists in the DB.
    user = db_session.query(models.User).filter_by(id=MOCK_USER_ID).first()
    if not user:
        db_user = models.User(id=MOCK_USER_ID, email=MOCK_USER_EMAIL)
        db_session.add(db_user)
        db_session.commit()

    with TestClient(app) as c:
        yield c

    # Clear overrides after test to not affect other tests if TestClient is created differently
    app.dependency_overrides.clear()
