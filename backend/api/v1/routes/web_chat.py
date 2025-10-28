from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.services.web_auth_service import get_current_active_user, get_user_full_profile_by_id, get_db
from backend.api.v1.schemas.user import User
from core.services.openrouter_service import openrouter_service
from core.services.database import Database

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@router.post("/", response_model=ChatResponse)
async def handle_web_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    Handles chat messages from the web interface. Requires JWT authentication.
    The user is identified via the token, not the request body.
    """
    user_profile = get_user_full_profile_by_id(db, current_user.id)
    if not user_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")

    answer = await openrouter_service.get_Psiko_answer(request.message, profile=user_profile)
    return ChatResponse(response=answer)