from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

# Import the schemas we need
from backend.api.v1.schemas.web_auth import WebAccountCreate, Token, SetPasswordRequest
from core.services.database import Database

# Import the services we built
from backend.services import web_auth_service, user_service

router = APIRouter()

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user_data: WebAccountCreate, db: Database = Depends(web_auth_service.get_db)):
    """
    Register a new user account.
    This only creates the account with email and password.
    Further biodata should be collected after the first login.
    """
    # The business logic is now handled in user_service
    new_user = user_service.create_user(db, user=user_data)
    if not new_user:
        # This case is handled by exceptions in the service, but as a fallback
        raise HTTPException(status_code=500, detail="Could not create user.")
    return new_user


@router.post("/login", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Database = Depends(web_auth_service.get_db)
):
    """
    Login user and return an access token.
    Uses the authenticate_user service function.
    """
    # The authentication logic is now neatly handled in the service
    user = web_auth_service.authenticate_user(db, email=form_data.username, password=form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.get("error") == "password_not_set":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password not set. Please set a password first.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create the access token
    access_token_expires = timedelta(minutes=web_auth_service.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = web_auth_service.create_access_token(
        data={"sub": user['email'], "user_id": user['id']}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/set-password", status_code=status.HTTP_200_OK)
def set_password(
    request: SetPasswordRequest,
    db: Database = Depends(web_auth_service.get_db)
):
    """
    Endpoint for users registered via Telegram to set their password for the first time.
    """
    success = web_auth_service.set_user_password(db, email=request.email, password=request.password)
    if not success:
        raise HTTPException(status_code=400, detail="Could not set password. User may not exist or password already set.")
    
    return {"message": "Password has been set successfully. You can now log in."}
