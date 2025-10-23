
from fastapi import HTTPException

# Database imports
from core.services.database import Database
from common.config.db_config import DBConfig

# Service imports
from core.services.profiling_service import get_password_hash
from backend.api.v1.schemas.web_auth import WebAccountCreate

# --- Database Setup ---
db = Database(
    host=DBConfig.HOST,
    user=DBConfig.USER,
    password=DBConfig.PASSWORD,
    database=DBConfig.NAME
)
# --------------------

def create_user(user: WebAccountCreate):
    """
    Handles the business logic for creating a new user.
    """
    db_user = db.get_user(email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    
    # Create user account with only email and password
    user_id = db.create_user_account(email=user.email, hashed_password=hashed_password)
    
    # Return the basic user info
    return {"id": user_id, "email": user.email}

def create_user_from_telegram(email: str):
    """
    Handles the business logic for creating a new user from Telegram.
    The initial password will be set to the user's email.
    """
    db_user = db.get_user(email=email)
    if db_user:
        # If user exists, just return their data. This handles re-registration attempts.
        return {"id": db_user['id'], "email": db_user['email']}
    
    # Hash the email to use it as the initial password.
    hashed_password = get_password_hash(email)
    
    user_id = db.create_user_account(email=email, hashed_password=hashed_password)
    
    return {"id": user_id, "email": email}

def check_user_profile_status(user_id: int) -> dict:
    """
    Checks if a user has completed their identity profile.
    """
    profile = db.get_profile_by_user_id(user_id)
    return {
        "has_identity": profile is not None
    }
