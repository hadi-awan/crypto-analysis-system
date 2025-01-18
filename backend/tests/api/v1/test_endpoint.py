import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.shared.database import test_engine, SessionLocal, override_get_db, get_db
from app.shared.database import Base
import websockets

# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def test_client():
    """Create test client"""
    client = TestClient(app)
    Base.metadata.create_all(bind=test_engine)  # Create test database
    yield client
    Base.metadata.drop_all(bind=test_engine)  # Drop test database

@pytest.fixture(scope="function")
def db_session():
    """Get DB session"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

def test_health_check():
    """Test the /health endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_read_crypto_pairs(test_client):
    """Test getting available crypto pairs"""
    response = test_client.get("/api/v1/crypto/pairs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["pairs"], list)
    assert "BTC/USDT" in data["pairs"]

def test_get_crypto_price():
    """Test getting crypto price"""
    response = client.get("/api/v1/crypto/price/BTC-USDT")
    assert response.status_code == 200
    data = response.json()
    # Check that we get price data in the expected format
    assert "price" in data
    assert isinstance(data["price"], float)
    assert "timestamp" in data

def test_read_invalid_pair(test_client):
    """Test getting price for invalid crypto pair"""
    response = test_client.get("/api/v1/crypto/price/INVALID-PAIR")
    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_websocket_connection():
    """Test WebSocket connection"""
    uri = "ws://localhost:8000/api/v1/crypto/ws/BTC-USDT"

    try:
        async with websockets.connect(uri) as websocket:
            # Wait for data to arrive from the WebSocket server
            response = await websocket.recv()
            assert response is not None
            assert isinstance(response, str)  # You can modify this based on the response you expect
    except Exception as e:
        pytest.fail(f"WebSocket connection failed: {e}")

def test_historical_data(test_client):
    """Test getting historical data"""
    response = test_client.get(
        "/api/v1/crypto/historical/BTC-USDT",
        params={"timeframe": "1h", "limit": 100}
    )

    # Check if the response status is successful
    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"

    # Check if the response is JSON
    assert "application/json" in response.headers["Content-Type"], \
        f"Expected 'application/json', but got {response.headers['Content-Type']}"

    # Print the raw response text to see what you're getting back
    print(response.text)  # This will help you inspect the returned content

    # Try parsing the JSON response
    try:
        data = response.json()  # Attempt to parse the response as JSON
    except ValueError:
        pytest.fail(f"Response content is not valid JSON: {response.text}")

    # Ensure that the 'data' field is a list (or adjust based on your expected response structure)
    assert isinstance(data.get('data', []), list), f"Expected list, got {type(data)}"

    # Ensure each entry in 'data' is a dictionary (the previous test expected string which caused the error)
    for entry in data.get('data', []):
        assert isinstance(entry, dict), f"Expected dictionary, got {type(entry)}"
        # Add checks for expected keys in each dictionary (like timestamp, open, close, etc.)
        assert 'timestamp' in entry, f"Missing 'timestamp' in entry: {entry}"
        assert 'open' in entry, f"Missing 'open' in entry: {entry}"
        assert 'close' in entry, f"Missing 'close' in entry: {entry}"
        assert 'high' in entry, f"Missing 'high' in entry: {entry}"
        assert 'low' in entry, f"Missing 'low' in entry: {entry}"
        assert 'volume' in entry, f"Missing 'volume' in entry: {entry}"

