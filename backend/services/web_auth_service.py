from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import jwt, JWTError

import os
from datetime import timedelta, datetime
from typing import Optional

# Database imports
from core.services.database import Database
from common.config.db_config import DBConfig
from common.config.settings import settings

# --- Database Dependency ---
def get_db():
    """FastAPI dependency to create and clean up a database session."""
    db = Database()
    try:
        yield db
    finally:
        pass # Koneksi dikelola secara internal oleh kelas Database

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/web-auth/login")

# Impor fungsi yang sudah dipindahkan
from core.services.profiling_service import verify_password, get_password_hash

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user_email(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return email

async def get_current_active_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Decodes the JWT token to get the current user's data.
    This is the dependency used to protect authenticated routes.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("id") # Diperbarui agar konsisten
        role: str = payload.get("role")
        if email is None or user_id is None or role is None:
            raise credentials_exception
        
        # Return a dictionary that matches the User schema and other expectations
        return {"email": email, "id": user_id, "role": role}

    except JWTError:
        raise credentials_exception

async def get_current_admin_user(current_user: dict = Depends(get_current_active_user)) -> dict:
    """
    Dependency to ensure the current user is an admin.
    Raises a 403 Forbidden error if the user is not an admin.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have the required permissions",
        )
    return current_user

# --- Core Authentication Logic ---
def authenticate_user(db: Database, email: str, password:str) -> Optional[dict]:
    """
    Authenticates a user by email and password.

    :param email: User's email.
    :param password: User's plain text password.
    :return: User object as a dict if authentication is successful, otherwise None.
    """
    user = db.get_user(email=email)
    if not user:
        return None
    # New check: if user registered via Telegram, they won't have a password yet.
    if user["hashed_password"] is None:
        return {"error": "password_not_set"}
    if not verify_password(password, user["hashed_password"]):
        return None
    return user

def get_user_full_profile_by_id(db: Database, user_id: int) -> dict:
    """
    Retrieves a user's full profile, including biodata and profiling results, by their ID.
    This is used after a successful login to populate the bot's context. It joins data
    from `users`, `profiles`, and `health_results`.
    """
    user_account = db.get_user_by_id(user_id)
    if not user_account:
        return {}

    # Fetch profile (biodata) and the latest health result
    profile_data = db.get_profile_by_user_id(user_id)
    health_results = db.get_all_health_results(user_id) # Mengambil semua riwayat

    # Add user's email to the biodata profile for frontend display
    if profile_data:
        # SOLUSI: Konversi DictRow (atau tipe data serupa) menjadi dictionary standar.
        # Ini memastikan Pydantic dapat memetakannya dengan benar.
        profile_data = dict(profile_data)
        profile_data['email'] = user_account.get('email')

    # Construct the profile dictionary
    response = {
        "biodata": profile_data,
        "health_results": health_results
    }
    
    return response

def find_user_by_email(db: Database, email: str) -> Optional[dict]:
    """
    Finds a user by email without password verification.
    Used for Telegram bot login.

    :param email: User's email.
    :return: User object as a dict if found, otherwise None.
    """
    return db.get_user(email=email)

def set_user_password(db: Database, email: str, password: str) -> bool:
    """
    Sets the password for a user who registered without one (e.g., via Telegram).
    """
    user = db.get_user(email=email)
    if not user or user.get("hashed_password") is not None:
        return False # User not found or password already set
    
    hashed_password = get_password_hash(password)
    return db.update_user_password(user['id'], hashed_password)


def internal_token_dependency(x_internal_token: str = Header(...)):
    """
    Dependency to protect internal endpoints.
    It checks for a secret token in the X-Internal-Token header.
    """
    if x_internal_token != settings.INTERNAL_BOT_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal token",
        )
    return True