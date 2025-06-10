from sqlalchemy.orm import Session
from . import models, schemas

def get_user(db: Session, user_id: str) -> models.User | None:
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user_id: str, email: str) -> models.User:
    db_user = models.User(id=user_id, email=email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_or_create_user(db: Session, user_id: str, email: str) -> models.User:
    db_user = get_user(db, user_id=user_id)
    if db_user:
        # Optionally update email if it can change in Supabase and needs sync
        # if db_user.email != email:
        #     db_user.email = email
        #     db.commit()
        #     db.refresh(db_user)
        return db_user
    return create_user(db=db, user_id=user_id, email=email)

def create_sip(db: Session, sip: schemas.SIPCreate, user_id: str) -> models.SIP:
    db_sip = models.SIP(**sip.dict(), user_id=user_id)
    db.add(db_sip)
    db.commit()
    db.refresh(db_sip)
    return db_sip

def get_sips_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100) -> list[models.SIP]:
    return db.query(models.SIP).filter(models.SIP.user_id == user_id).offset(skip).limit(limit).all()
