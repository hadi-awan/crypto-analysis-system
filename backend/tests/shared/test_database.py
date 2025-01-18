
import pytest
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from sqlalchemy.exc import IntegrityError
import os
from app.shared.database import test_engine, SessionLocal
from app.shared.database import Base

# Test model for database verification
from sqlalchemy import Column, Integer, String, CheckConstraint
class TestModel(Base):
    __tablename__ = "test_model"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)  # Make name required
    
    # Add constraint that name can't be empty
    __table_args__ = (
        CheckConstraint('length(name) > 0', name='name_length_check'),
    )

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create the test database"""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists("test.db"):
        os.remove("test.db")

@pytest.fixture(scope="function")
def db_session():
    """Get DB session with transaction rollback"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

def test_database_connection(db_session):
    """Test database connection"""
    assert isinstance(db_session, Session)
    
    # Try to execute a simple query
    result = db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1

def test_model_crud(db_session):
    """Test CRUD operations"""
    # Create
    test_item = TestModel(name="test")
    db_session.add(test_item)
    db_session.flush()
    
    # Read
    db_item = db_session.query(TestModel).filter_by(name="test").first()
    assert db_item is not None
    assert db_item.name == "test"
    
    # Update
    db_item.name = "updated"
    db_session.flush()
    updated_item = db_session.query(TestModel).filter_by(id=db_item.id).first()
    assert updated_item.name == "updated"
    
    # Delete
    db_session.delete(db_item)
    db_session.flush()
    deleted_item = db_session.query(TestModel).filter_by(id=db_item.id).first()
    assert deleted_item is None

def test_session_rollback(db_session):
    """Test transaction rollback"""
    # Create initial record
    test_item = TestModel(name="rollback_test")
    db_session.add(test_item)
    db_session.flush()
    item_id = test_item.id
    
    # Try to update with invalid data (empty name) - should trigger constraint
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            test_item.name = ""  # This should fail due to check constraint
            db_session.flush()
    
    # Verify original data is preserved
    db_item = db_session.query(TestModel).get(item_id)
    assert db_item is not None
    assert db_item.name == "rollback_test"  # Original name should be preserved

def test_rollback_on_invalid_insert(db_session):
    """Test rollback when inserting invalid data"""
    # Try to create item with invalid data
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            invalid_item = TestModel(name="")  # Empty name violates constraint
            db_session.add(invalid_item)
            db_session.flush()
    
    # Verify no data was persisted
    items = db_session.query(TestModel).all()
    assert len(items) == 0
