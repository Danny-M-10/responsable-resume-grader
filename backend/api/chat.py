"""
Chat API endpoints for AI-powered candidate selection discussions
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from backend.middleware.auth import get_current_user_id
from backend.services.chat_service import get_chat_service

router = APIRouter()


class ChatMessageRequest(BaseModel):
    """Request model for chat messages"""
    message: str


class ChatMessageResponse(BaseModel):
    """Response model for chat messages"""
    response: str


@router.post("/{analysis_id}/message", response_model=ChatMessageResponse)
async def send_chat_message(
    analysis_id: str,
    request: ChatMessageRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Send a chat message about candidate selection rationale

    Args:
        analysis_id: Analysis ID to discuss
        request: Chat message request
        user_id: Current user ID

    Returns:
        AI response to the user's question
    """
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty"
        )

    try:
        chat_service = get_chat_service()
        response = await chat_service.generate_chat_response(
            analysis_id=analysis_id,
            user_message=request.message.strip(),
            user_id=user_id
        )
        return ChatMessageResponse(response=response)
    except ValueError as e:
        # AI provider not configured
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI chat service is not available. Set GEMINI_API_KEY or OPENAI_API_KEY."
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate chat response: {str(e)}"
        )
