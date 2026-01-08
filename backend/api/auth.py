"""
Authentication API endpoints
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.schemas import UserCreate, UserLogin, Token, UserResponse
from backend.database.connection import get_db
from backend.services.auth_service import (
    create_user_async,
    authenticate_async,
    get_user_by_id_async
)
from backend.middleware.auth import get_current_user_id

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user
    
    Args:
        user_data: User registration data (email, password)
        db: Database session
        
    Returns:
        JWT access token
        
    Raises:
        HTTPException: If registration fails
    """
    try:
        user_id = await create_user_async(
            email=user_data.email,
            password=user_data.password,
            db=db
        )
        
        # Create JWT token
        from backend.middleware.auth import create_access_token
        access_token = create_access_token(data={"sub": user_id})
        
        return Token(access_token=access_token, token_type="bearer")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login user
    
    Args:
        user_data: User login data (email, password)
        db: Database session
        
    Returns:
        JWT access token
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        access_token, user_id = await authenticate_async(
            email=user_data.email,
            password=user_data.password,
            db=db
        )
        
        return Token(access_token=access_token, token_type="bearer")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current authenticated user
    
    Args:
        user_id: Current user ID from JWT token
        db: Database session
        
    Returns:
        User information
        
    Raises:
        HTTPException: If user not found
    """
    user = await get_user_by_id_async(user_id, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Parse datetime string
    created_at_str = user["created_at"]
    if created_at_str.endswith("Z"):
        created_at_str = created_at_str[:-1] + "+00:00"
    created_at = datetime.fromisoformat(created_at_str)
    
    return UserResponse(
        id=user["id"],
        email=user["email"],
        created_at=created_at
    )


@router.post("/logout")
async def logout(
    user_id: str = Depends(get_current_user_id)
):
    """
    Logout user (client should discard token)
    
    Args:
        user_id: Current user ID from JWT token
        
    Returns:
        Success message
    """
    # In JWT-based auth, logout is handled client-side by discarding the token
    # Optionally, we could maintain a token blacklist in Redis
    return {"message": "Logged out successfully"}
