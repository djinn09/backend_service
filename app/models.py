from sqlalchemy import Column, String, Float, Date, ForeignKey, DateTime, Text, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid # For generating UUIDs if needed for default, though Supabase provides them
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    # Using String to store Supabase User ID (which is a UUID)
    # Alternatively, use sqlalchemy.dialects.postgresql.UUID
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    # hashed_password is removed as Supabase handles authentication

    sips = relationship("SIP", back_populates="owner")

class SIP(Base):
    __tablename__ = "sips"

    id = Column(Integer, primary_key=True, index=True) # Keep internal integer PK for SIPs
    scheme_name = Column(String, index=True, nullable=False)
    monthly_amount = Column(Float, nullable=False)
    start_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # user_id now refers to User.id, which is a String (Supabase UUID)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="sips")

# Note: If using sqlalchemy.dialects.postgresql.UUID for User.id,
# you might need to ensure the ForeignKey in SIP.user_id matches that type,
# or that string representation is handled correctly by SQLAlchemy.
# Using String for User.id is generally safe for UUIDs.
