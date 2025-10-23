from fastapi import APIRouter, Depends, HTTPException
from backend.api.v1.schemas.chat import ChatMessage
from core.services.openrouter_service import openrouter_service
from core.services.database import Database
from backend.services import web_auth_service

router = APIRouter()

def get_db():
    db = Database()
    try:
        yield db
    finally:
        pass

@router.post("/")
async def chat_with_bot(chat_message: ChatMessage, db: Database = Depends(get_db)):
    user_id = chat_message.user_id

    # 1. Get user profile using the consistent service
    # This now returns a dictionary with 'biodata' and 'health_results' keys
    full_profile = web_auth_service.get_user_full_profile_by_id(user_id)
    
    user_profile = full_profile # The service expects the full structure
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    # 2. Get bot response
    bot_response = await openrouter_service.get_Psiko_answer(chat_message.message, profile=user_profile)

    return {"response": bot_response}