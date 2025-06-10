from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt # JWTError might not be directly used if relying on supabase.auth.get_user
from pydantic import BaseModel
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from typing import Optional

from sqlalchemy.orm import Session
from .database import get_db # Import get_db
from . import crud, models # Import crud and models

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    # In a real app, log this or handle more gracefully
    raise Exception("Supabase URL and Key must be set in environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # Placeholder tokenUrl

class TokenData(BaseModel):
    user_id: Optional[str] = None
    # email: Optional[str] = None # Could add email if needed downstream

async def get_current_user_data(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_response = supabase.auth.get_user(token)

        if user_response.user is None:
            raise credentials_exception

        supabase_user_id = str(user_response.user.id)
        supabase_user_email = user_response.user.email

        if supabase_user_id is None or supabase_user_email is None:
            raise credentials_exception

        # Get or create user in local database
        # This ensures our DB has a record for the authenticated user
        db_user = crud.get_or_create_user(db, user_id=supabase_user_id, email=supabase_user_email)
        if db_user is None:
            # This case should ideally not be reached if crud.get_or_create_user is robust
            raise HTTPException(status_code=500, detail="Could not get or create local user record.")

        return db_user # Return the full User model from local DB

    except JWTError: # Should not be hit if using supabase.auth.get_user primarily
        raise credentials_exception
    except HTTPException as e: # Re-raise HTTPExceptions
        raise e
    except Exception as e:
        # Log the exception e for debugging
        print(f"Error in get_current_user_data: {e}")
        raise credentials_exception

# Dependency to get user_id as a string from the local user model
async def get_current_user_id(current_db_user: models.User = Depends(get_current_user_data)) -> str:
    if current_db_user.id is None: # Should always be there if current_db_user is valid
        raise HTTPException(status_code=400, detail="User ID not found after authentication")
    return current_db_user.id
