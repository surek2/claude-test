"""
Authentication module for AICOM community service.
Handles all auth-related functionality including signup, login, JWT handling, and CSRF protection.
"""

import os
from jose import jwt
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
from functools import wraps

from fastapi import APIRouter, HTTPException, Request, Response, Depends, status, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr, Field, field_validator
from supabase import Client

from .config import settings
from .database import db

# ==================== Models ====================

class UserSignup(BaseModel):
    """User signup request model"""
    email: EmailStr
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=6)
    password_confirm: str
    
    @field_validator('password_confirm')
    def passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @field_validator('username')
    def username_valid(cls, v):
        # Allow alphanumeric, Korean, underscore, hyphen
        # No validation for now - accept all characters
        return v.strip()

class UserLogin(BaseModel):
    """User login request model"""
    email: EmailStr
    password: str = Field(..., min_length=1)

class EmailCheckRequest(BaseModel):
    """Email availability check request"""
    email: EmailStr

class UsernameCheckRequest(BaseModel):
    """Username availability check request"""
    username: str = Field(..., min_length=1, max_length=50)

class AuthResponse(BaseModel):
    """Authentication response model"""
    message: str
    user: Optional[Dict[str, Any]] = None

class AvailabilityResponse(BaseModel):
    """Availability check response"""
    available: bool

# ==================== JWT Handling ====================

def decode_jwt(token: str) -> Dict[str, Any]:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False}
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Extract current user from JWT in cookies"""
    access_token = request.cookies.get("access_token")
    if not access_token:
        return None
    
    try:
        payload = decode_jwt(access_token)
        
        # Get user profile from database to include is_admin field
        user_id = payload.get("sub")  # Supabase stores user ID in 'sub' field
        if user_id:
            profile = db.select("users", filters={"id": user_id})
            if profile:
                # Merge JWT payload with profile data
                user_data = {
                    **payload,
                    "id": user_id,
                    "email": profile[0].get("email"),
                    "username": profile[0].get("username"),
                    "is_admin": profile[0].get("is_admin", False)
                }
                return user_data
        
        return payload
    except HTTPException:
        return None

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        request = kwargs.get('request')
        if not request:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Request object not found"
            )
        
        user = get_current_user(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        kwargs['current_user'] = user
        return await f(*args, **kwargs)
    
    return decorated_function

# ==================== CSRF Protection ====================

def generate_csrf_token() -> str:
    """Generate a new CSRF token"""
    return secrets.token_urlsafe(32)

def verify_csrf_token(request: Request, token: str) -> bool:
    """Verify CSRF token from request"""
    stored_token = request.session.get("csrf_token") if hasattr(request, "session") else None
    return stored_token == token if stored_token else True  # Allow if no session (testing)

async def csrf_protect(request: Request):
    """CSRF protection dependency"""
    # For POST/PUT/DELETE requests, check CSRF token
    if request.method in ["POST", "PUT", "DELETE"]:
        # Try to get CSRF token from multiple sources
        token = None
        
        # 1. Check X-CSRF-Token header (for AJAX/HTMX requests)
        token = request.headers.get("X-CSRF-Token")
        
        # 2. Check form data (for regular form submissions)
        if not token and request.method == "POST":
            # Check if content-type is form data
            content_type = request.headers.get("content-type", "")
            if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
                form_data = await request.form()
                token = form_data.get("csrf_token")
        
        # 3. Check JSON body (for JSON API requests)
        if not token and request.method in ["POST", "PUT", "DELETE"]:
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    body = await request.json()
                    token = body.get("csrf_token")
                except:
                    pass
        
        # Verify token
        if not token or not verify_csrf_token(request, token):
            # For HTMX requests, return a user-friendly error
            if request.headers.get("HX-Request"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="세션이 만료되었습니다. 페이지를 새로고침해주세요."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF token validation failed"
                )

# ==================== Services ====================

def create_user_profile(user_id: str, email: str, username: str, is_admin: bool = False) -> None:
    """Create user profile in users table"""
    try:
        result = db.insert("users", {
            "id": user_id,
            "email": email,
            "username": username,
            "is_admin": is_admin
        })
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user profile"
            )
    except Exception as e:
        # Check if it's a unique constraint violation
        if "duplicate key" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email or username already exists"
            )
        raise

def check_email_exists(email: str) -> bool:
    """Check if email already exists in users table"""
    result = db.select("users", filters={"email": email})
    return len(result) > 0 if result else False

def check_username_exists(username: str) -> bool:
    """Check if username already exists in users table"""
    result = db.select("users", filters={"username": username})
    return len(result) > 0 if result else False

def set_auth_cookies(response: Response, session: Dict[str, Any]) -> None:
    """Set authentication cookies"""
    access_token = session.get("access_token")
    refresh_token = session.get("refresh_token")
    
    if access_token:
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
            max_age=3600  # 1 hour
        )
    
    if refresh_token:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
            max_age=604800  # 7 days
        )

def clear_auth_cookies(response: Response) -> None:
    """Clear authentication cookies"""
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")

# ==================== API Routes ====================

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/signup", response_model=AuthResponse, dependencies=[Depends(csrf_protect)])
async def signup(
    request: Request,
    response: Response,
    email: EmailStr = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...)
):
    """User signup endpoint"""
    try:
        # Validate passwords match
        if password != password_confirm:
            # Check if request is from HTMX
            if request.headers.get("HX-Request"):
                return JSONResponse(
                    content={"error": "비밀번호가 일치하지 않습니다"},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )
        
        # Validate password length
        if len(password) < 6:
            if request.headers.get("HX-Request"):
                return JSONResponse(
                    content={"error": "비밀번호는 최소 6자 이상이어야 합니다"},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters"
            )
        
        # Check if email or username already exists
        if check_email_exists(email):
            if request.headers.get("HX-Request"):
                return JSONResponse(
                    content={"error": "이미 등록된 이메일입니다"},
                    status_code=status.HTTP_409_CONFLICT
                )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        if check_username_exists(username):
            if request.headers.get("HX-Request"):
                return JSONResponse(
                    content={"error": "이미 사용 중인 사용자명입니다"},
                    status_code=status.HTTP_409_CONFLICT
                )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken"
            )
        
        # Sign up user with Supabase Auth
        auth_response = db.sign_up(
            email=email,
            password=password,
            metadata={"username": username}
        )
        
        if not auth_response or not auth_response.user:
            if request.headers.get("HX-Request"):
                return JSONResponse(
                    content={"error": "계정 생성에 실패했습니다"},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create account"
            )
        
        # Create user profile
        try:
            create_user_profile(
                user_id=auth_response.user.id,
                email=email,
                username=username
            )
        except HTTPException:
            # If profile creation fails, we need to handle it properly
            # The auth user was created but profile wasn't
            raise
        except Exception as e:
            # Log the actual error for debugging
            print(f"Profile creation error: {e}")
            if request.headers.get("HX-Request"):
                return JSONResponse(
                    content={"error": "프로필 설정 중 오류가 발생했습니다"},
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Account created but profile setup failed: {str(e)}"
            )
        
        # Set auth cookies
        if auth_response.session:
            set_auth_cookies(response, auth_response.session.__dict__)
        
        # Return success response for HTMX
        if request.headers.get("HX-Request"):
            response.headers["HX-Redirect"] = "/"
            return {"message": "회원가입이 완료되었습니다", "redirect": "/"}
        
        return AuthResponse(
            message="Signup successful",
            user={
                "id": auth_response.user.id,
                "email": auth_response.user.email,
                "username": username,
                "is_admin": False  # New users are not admin by default
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        if request.headers.get("HX-Request"):
            return JSONResponse(
                content={"error": "회원가입 중 오류가 발생했습니다"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup failed: {str(e)}"
        )

@router.post("/login", response_model=AuthResponse, dependencies=[Depends(csrf_protect)])
async def login(
    request: Request,
    response: Response,
    email: EmailStr = Form(...),
    password: str = Form(...)
):
    """User login endpoint"""
    try:
        # Sign in with Supabase Auth
        auth_response = db.sign_in(
            email=email,
            password=password
        )
        
        if not auth_response or not auth_response.user:
            if request.headers.get("HX-Request"):
                return JSONResponse(
                    content={"error": "이메일 또는 비밀번호가 올바르지 않습니다"},
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Get user profile
        profile = db.select(
            "users",
            filters={"id": auth_response.user.id}
        )
        
        if not profile:
            if request.headers.get("HX-Request"):
                return JSONResponse(
                    content={"error": "사용자 프로필을 찾을 수 없습니다"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        # Set auth cookies
        if auth_response.session:
            set_auth_cookies(response, auth_response.session.__dict__)
        
        # Return success response for HTMX
        if request.headers.get("HX-Request"):
            response.headers["HX-Redirect"] = "/"
            return {"message": "로그인 성공", "redirect": "/"}
        
        return AuthResponse(
            message="Login successful",
            user={
                "id": auth_response.user.id,
                "email": auth_response.user.email,
                "username": profile[0].get("username") if profile else None,
                "is_admin": profile[0].get("is_admin", False) if profile else False
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        if request.headers.get("HX-Request"):
            return JSONResponse(
                content={"error": "이메일 또는 비밀번호가 올바르지 않습니다"},
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

@router.post("/logout")
async def logout(request: Request, response: Response):
    """User logout endpoint"""
    try:
        # Get current user (optional - logout should work even if not logged in)
        access_token = request.cookies.get("access_token")
        if access_token:
            # Sign out from Supabase
            db.sign_out(access_token)
        
        # Clear auth cookies
        clear_auth_cookies(response)
        
        # Handle HTMX request - redirect to home
        if request.headers.get("HX-Request"):
            response.headers["HX-Redirect"] = "/"
            return {"message": "로그아웃되었습니다"}
        
        return AuthResponse(message="Logout successful")
        
    except Exception as e:
        # Still clear cookies even if Supabase signout fails
        clear_auth_cookies(response)
        
        if request.headers.get("HX-Request"):
            response.headers["HX-Redirect"] = "/"
            return {"message": "로그아웃되었습니다"}
            
        return AuthResponse(message="Logout successful")

@router.post("/check-email")
async def check_email(
    request: Request,
    email: EmailStr = Form(...)
):
    """Check if email is available"""
    exists = check_email_exists(email)
    
    # For HTMX requests, return HTML snippet
    if request.headers.get("HX-Request"):
        if exists:
            return HTMLResponse('<span class="text-destructive">이미 사용 중인 이메일입니다</span>')
        else:
            return HTMLResponse('<span class="text-green-600">사용 가능한 이메일입니다</span>')
    
    return AvailabilityResponse(available=not exists)

@router.post("/check-username")
async def check_username(
    request: Request,
    username: str = Form(...)
):
    """Check if username is available"""
    exists = check_username_exists(username)
    
    # For HTMX requests, return HTML snippet
    if request.headers.get("HX-Request"):
        if exists:
            return HTMLResponse('<span class="text-destructive">이미 사용 중인 사용자명입니다</span>')
        else:
            return HTMLResponse('<span class="text-green-600">사용 가능한 사용자명입니다</span>')
    
    return AvailabilityResponse(available=not exists)

@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(request: Request, response: Response):
    """Refresh access token using refresh token"""
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )
    
    try:
        # Refresh session with Supabase
        auth_response = db.refresh_token(refresh_token)
        
        if not auth_response or not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Set new auth cookies
        if auth_response.session:
            set_auth_cookies(response, auth_response.session.__dict__)
        
        return AuthResponse(
            message="Token refreshed successfully",
            user={
                "id": auth_response.user.id,
                "email": auth_response.user.email
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to refresh token"
        )

# ==================== Middleware ====================

async def jwt_middleware(request: Request, call_next):
    """JWT authentication middleware"""
    # Public paths that don't require authentication
    public_paths = ["/", "/login", "/signup", "/api/auth", "/static", "/favicon.ico", "/health"]
    
    # Always try to get user from token if available
    access_token = request.cookies.get("access_token")
    
    if access_token:
        try:
            # Verify token
            payload = decode_jwt(access_token)
            request.state.user = payload
        except HTTPException:
            # Try to refresh token
            refresh_token = request.cookies.get("refresh_token")
            if refresh_token:
                try:
                    auth_response = db.refresh_token(refresh_token)
                    if auth_response and auth_response.session:
                        # Set new tokens in response
                        response = await call_next(request)
                        set_auth_cookies(response, auth_response.session.__dict__)
                        return response
                except:
                    pass
            
            # If refresh fails, clear user
            request.state.user = None
    else:
        request.state.user = None
    
    # Check if path requires authentication
    is_public_path = any(request.url.path.startswith(path) for path in public_paths)
    
    if not is_public_path and not request.state.user:
        # Protected path requires authentication
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Authentication required"}
        )
    
    return await call_next(request)

# ==================== Dependencies ====================

async def require_admin(request: Request) -> dict:
    """Require admin user for protected endpoints"""
    user = getattr(request.state, "user", None)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Get user profile to check admin status
    profiles = db.select("users", filters={"id": user.get("sub")})
    
    if not profiles or not profiles[0].get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Add user info to the user dict
    user["email"] = profiles[0].get("email")
    user["username"] = profiles[0].get("username")
    user["is_admin"] = profiles[0].get("is_admin")
    
    return user

# ==================== Admin Account Setup ====================

def create_initial_admin():
    """Create initial admin account if it doesn't exist"""
    admin_email = "admin@example.com"
    admin_password = "admin123"
    admin_username = "admin"
    
    try:
        # Check if admin already exists
        existing = check_email_exists(admin_email)
        if existing:
            print("Admin account already exists")
            return
        
        # Create admin account
        auth_response = db.sign_up(
            email=admin_email,
            password=admin_password,
            metadata={"username": admin_username}
        )
        
        if auth_response and auth_response.user:
            # Create user profile with admin privileges
            create_user_profile(
                user_id=auth_response.user.id,
                email=admin_email,
                username=admin_username,
                is_admin=True  # Set as admin
            )
            
            print(f"Initial admin account created: {admin_email}")
    except HTTPException:
        # Re-raise HTTP exceptions (from create_user_profile)
        raise
    except Exception as e:
        print(f"Failed to create initial admin: {e}")
        # Don't raise - allow app to start even if admin creation fails