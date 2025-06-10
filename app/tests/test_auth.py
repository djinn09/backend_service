import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from app.auth import get_current_user_data, supabase # Assuming supabase client is accessible for patching
from app.database import SessionLocal # To create a db session for the test
from app.crud import get_user # Changed from get_user to get_or_create_user based on auth logic
from app.models import User as UserModel

# This test is more involved due to async nature and DB interaction within auth.py
# For simplicity, this example focuses on mocking Supabase and checking DB side effects.
# Note: Running async code in pytest requires pytest-asyncio usually.
# However, get_current_user_data is an async function called by FastAPI, not directly by test.

@pytest.mark.asyncio # If testing async functions directly
async def test_get_current_user_data_new_user(db_session): # Use db_session fixture
    mock_supabase_user = MagicMock()
    mock_supabase_user.id = "new-user-uuid"
    mock_supabase_user.email = "new@example.com"

    mock_user_response = MagicMock()
    mock_user_response.user = mock_supabase_user

    with patch("app.auth.supabase.auth.get_user") as mock_get_user_supabase: # Renamed to avoid conflict
        mock_get_user_supabase.return_value = mock_user_response

        # Simulate FastAPI calling the dependency
        # This requires a bit of setup to mimic FastAPI's dependency injection
        # For a direct test, you might call it with mock token and db_session
        token = "fake-jwt-token"

        # Ensure the user does not exist before the call
        assert get_user(db_session, user_id=mock_supabase_user.id) is None

        # Call the function being tested
        auth_user_model = await get_current_user_data(token=token, db=db_session)

        assert auth_user_model is not None
        assert auth_user_model.id == mock_supabase_user.id
        assert auth_user_model.email == mock_supabase_user.email

        # Verify user was created in DB
        db_user_after_call = get_user(db_session, user_id=mock_supabase_user.id) # Renamed to avoid conflict
        assert db_user_after_call is not None
        assert db_user_after_call.email == mock_supabase_user.email
        mock_get_user_supabase.assert_called_once_with(token)

@pytest.mark.asyncio
async def test_get_current_user_data_existing_user(db_session):
    existing_user_id = "existing-user-uuid"
    existing_user_email = "existing@example.com"
    # Pre-populate user in DB
    db_session.add(UserModel(id=existing_user_id, email=existing_user_email))
    db_session.commit()

    mock_supabase_user = MagicMock()
    mock_supabase_user.id = existing_user_id
    mock_supabase_user.email = existing_user_email # Email can be updated if logic allows
    mock_user_response = MagicMock()
    mock_user_response.user = mock_supabase_user

    with patch("app.auth.supabase.auth.get_user") as mock_get_user_supabase: # Renamed
        mock_get_user_supabase.return_value = mock_user_response
        token = "fake-jwt-token"
        auth_user_model = await get_current_user_data(token=token, db=db_session)

        assert auth_user_model.id == existing_user_id
        # Add more assertions if email update logic was in place

@pytest.mark.asyncio
async def test_get_current_user_data_supabase_error(db_session):
    with patch("app.auth.supabase.auth.get_user") as mock_get_user_supabase: # Renamed
        mock_get_user_supabase.side_effect = Exception("Supabase boom!") # Simulate any Supabase client error
        token = "fake-jwt-token"
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_data(token=token, db=db_session)
        assert exc_info.value.status_code == 401
