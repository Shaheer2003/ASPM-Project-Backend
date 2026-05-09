from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.models import User, PasswordReset, UserStatus
from app.schemas import LoginRequest, LoginResponse, ForgotPasswordRequest, ForgotPasswordResponse, ResetPasswordRequest, ResetPasswordResponse
from app.auth.utils import hash_password, verify_password, create_access_token, generate_reset_token
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/api/auth", tags=["auth"])


def send_email(*args, **kwargs):
    """Compatibility hook for tests that patch email delivery."""
    return True


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    # Find user by username
    user = db.query(User).filter(
        User.username == request.username.lower().strip()
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not verify_password(request.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Check if user is inactive or archived
    if user.status not in {UserStatus.ACTIVE, "Active"}:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account is inactive."
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    return LoginResponse(
        ok=True,
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "role": getattr(user.role, "name", str(user.role)).upper(),
            "email": user.email
        }
    )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Request password reset token."""
    normalized_email = request.email.lower().strip()
    
    # Find user by email
    user = db.query(User).filter(
        User.email == normalized_email
    ).first()
    
    if not user:
        return ForgotPasswordResponse(
            ok=True,
            token=None,
            message="Reset link generated. Use the token to reset your password."
        )
    
    # Clear old reset tokens for this user
    db.query(PasswordReset).filter(
        PasswordReset.user_id == user.id,
        PasswordReset.is_used == False
    ).delete()
    
    # Generate new reset token
    token = generate_reset_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    password_reset = PasswordReset(
        user_id=user.id,
        email=user.email,
        token=token,
        expires_at=expires_at
    )
    
    db.add(password_reset)
    db.commit()

    send_email(user.email, "password-reset", token)
    
    return ForgotPasswordResponse(
        ok=True,
        token=token,
        message="Reset link generated. Use the token to reset your password."
    )


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset user password with reset token."""
    token = request.token.strip()
    new_password = getattr(request, "new_password", None) or getattr(request, "newPassword", None)
    
    # Find reset token
    reset_request = db.query(PasswordReset).filter(
        PasswordReset.token == token,
        PasswordReset.is_used == False,
        PasswordReset.expires_at > datetime.now(timezone.utc)
    ).first()
    
    if not reset_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token."
        )
    
    # Validate password length
    if len(new_password.strip()) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters."
        )
    
    # Update user password
    user = db.query(User).filter(User.id == reset_request.user_id).first()
    if not user:
        user = db.query(User).filter(User.email == reset_request.email).first()
    if user:
        user.password = hash_password(new_password.strip())
        db.add(user)
    
    # Mark reset token as used
    reset_request.is_used = True
    db.add(reset_request)
    db.commit()
    
    return ResetPasswordResponse(
        ok=True,
        message="Password reset successfully."
    )
