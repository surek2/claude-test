"""
Main FastAPI application for AICOM community service.
"""

import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from .config import settings
from .auth import router as auth_router, jwt_middleware, create_initial_admin, generate_csrf_token
from .boards import router as boards_router, create_initial_boards
from .posts import router as posts_router
from .comments import router as comments_router
from .admin import router as admin_router
from .init_data import init_all_data

logger = logging.getLogger(__name__)

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle app startup and shutdown events"""
    # Startup
    print("Starting AICOM community service...")
    
    # Create initial admin account
    try:
        create_initial_admin()
    except Exception as e:
        print(f"Admin account creation skipped: {e}")
    
    # Create initial boards
    try:
        create_initial_boards()
    except Exception as e:
        print(f"Initial boards creation skipped: {e}")
    
    yield
    
    # Shutdown
    print("Shutting down AICOM community service...")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="AICOM Community Service API",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    same_site=settings.cookie_samesite,
    https_only=settings.cookie_secure
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure based on your domain
)

# Add JWT middleware
app.middleware("http")(jwt_middleware)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Only add HSTS in production
    if settings.cookie_secure:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Content Security Policy - allow inline styles/scripts for HTMX and Quill
    csp_directives = [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://unpkg.com https://cdn.jsdelivr.net https://cdn.tailwindcss.com",
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
        "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com data:",
        "img-src 'self' data: https:",
        "connect-src 'self'",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'"
    ]
    response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
    
    return response

# Create directories if they don't exist
static_dir = Path(__file__).parent.parent / "static"
templates_dir = Path(__file__).parent.parent / "templates"
static_dir.mkdir(exist_ok=True)
templates_dir.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Setup templates
templates = Jinja2Templates(directory=str(templates_dir))

# Add custom filters
from datetime import datetime

def format_date(value):
    """Format datetime to Korean format"""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except:
            return value
    
    now = datetime.now(value.tzinfo)
    diff = now - value
    
    if diff.days == 0:
        if diff.seconds < 60:
            return "방금 전"
        elif diff.seconds < 3600:
            return f"{diff.seconds // 60}분 전"
        else:
            return f"{diff.seconds // 3600}시간 전"
    elif diff.days == 1:
        return "어제"
    elif diff.days < 7:
        return f"{diff.days}일 전"
    else:
        return value.strftime("%Y.%m.%d")

templates.env.filters["date"] = format_date

# Include routers
app.include_router(auth_router)
app.include_router(boards_router)
app.include_router(posts_router)
app.include_router(comments_router)
app.include_router(admin_router)

# ==================== Page Routes ====================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, board: Optional[str] = None, page: int = 1):
    """Home page with optional board and page parameters"""
    csrf_token = generate_csrf_token()
    request.session["csrf_token"] = csrf_token
    
    # Get all boards ordered by display_order
    from .database import db
    # Get boards with consistent ordering - display_order, then name, then id for absolute consistency
    boards = db.client.table("boards").select("*").eq("is_active", True).order("display_order", desc=False).order("name", desc=False).order("id", desc=False).execute()
    boards = boards.data
    
    # Filter boards based on user permissions
    user = getattr(request.state, "user", None)
    visible_boards = []
    
    # Check if user is admin and get user info
    if user:
        user_profiles = db.select("users", filters={"id": user.get("sub")})
        if user_profiles:
            user_profile = user_profiles[0]
            user["is_admin"] = user_profile.get("is_admin", False)
            user["username"] = user_profile.get("username")
            user["email"] = user_profile.get("email")
    
    for board_item in boards:
        can_read = board_item.get("can_read", "all")
        if can_read == "all":
            visible_boards.append(board_item)
        elif can_read == "member" and user:
            visible_boards.append(board_item)
        elif can_read == "admin" and user and user.get("is_admin", False):
            visible_boards.append(board_item)
    
    # Determine active board slug
    # Priority: 1. URL parameter, 2. Default to gongjisahang
    active_board_slug = board  # Use URL parameter if provided
    
    # Validate the board slug exists and user has permission
    if active_board_slug:
        board_exists = any(b["slug"] == active_board_slug for b in visible_boards)
        if not board_exists:
            active_board_slug = None
    
    # If no valid board specified, default to notice
    if not active_board_slug:
        for board_item in visible_boards:
            if board_item.get("slug") == "notice":
                active_board_slug = "notice"
                break
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "csrf_token": csrf_token,
            "user": user,
            "boards": visible_boards,
            "active_board_slug": active_board_slug,
            "initial_page": page
        }
    )

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    csrf_token = generate_csrf_token()
    request.session["csrf_token"] = csrf_token
    
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "csrf_token": csrf_token
        }
    )

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Signup page"""
    csrf_token = generate_csrf_token()
    request.session["csrf_token"] = csrf_token
    
    return templates.TemplateResponse(
        "signup.html",
        {
            "request": request,
            "csrf_token": csrf_token
        }
    )

@app.get("/boards/{board_slug}/posts/new", response_class=HTMLResponse)
async def create_post_page(request: Request, board_slug: str):
    """Create new post page"""
    from .database import db
    
    # Check if user is logged in
    user = getattr(request.state, "user", None)
    if not user:
        return templates.TemplateResponse(
            "403.html",
            {"request": request, "user": user},
            status_code=403
        )
    
    # Get board
    boards = db.select("boards", filters={"slug": board_slug})
    if not boards:
        raise HTTPException(status_code=404, detail="Board not found")
    
    board = boards[0]
    
    # Check write permission
    can_write = board.get("can_write", "member")
    is_admin = False
    
    # Check if user is admin and get user info
    user_profiles = db.select("users", filters={"id": user.get("sub")})
    if user_profiles:
        user_profile = user_profiles[0]
        is_admin = user_profile.get("is_admin", False)
        user["is_admin"] = is_admin
        user["username"] = user_profile.get("username")
        user["email"] = user_profile.get("email")
    
    # Check write permission
    if can_write == "member":
        # Any logged in user can write
        pass
    elif can_write == "admin" and not is_admin:
        return templates.TemplateResponse(
            "403.html",
            {"request": request, "user": user},
            status_code=403
        )
    elif can_write == "all":
        # Anyone can write (but we already checked login)
        pass
    
    csrf_token = generate_csrf_token()
    request.session["csrf_token"] = csrf_token
    
    return templates.TemplateResponse(
        "posts/create.html",
        {
            "request": request,
            "user": user,
            "board": board,
            "csrf_token": csrf_token
        }
    )

@app.get("/boards/{board_slug}/posts/{post_id}", response_class=HTMLResponse)
async def post_detail_page(request: Request, board_slug: str, post_id: str, from_page: int = 1):
    """Post detail page"""
    from .database import db
    
    # Get board
    boards = db.select("boards", filters={"slug": board_slug})
    if not boards:
        raise HTTPException(status_code=404, detail="Board not found")
    
    board = boards[0]
    
    # Get post
    posts = db.select("posts", filters={"id": post_id, "board_id": board["id"]})
    if not posts:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post = posts[0]
    
    # Check read permission
    user = getattr(request.state, "user", None)
    can_read = board.get("can_read", "all")
    is_admin = False
    
    if user:
        user_profiles = db.select("users", filters={"id": user.get("sub")})
        if user_profiles:
            user_profile = user_profiles[0]
            is_admin = user_profile.get("is_admin", False)
            user["is_admin"] = is_admin
            user["username"] = user_profile.get("username")
            user["email"] = user_profile.get("email")
    
    if can_read == "member" and not user:
        return templates.TemplateResponse(
            "403.html",
            {"request": request, "user": user},
            status_code=403
        )
    
    if can_read == "admin" and not is_admin:
        return templates.TemplateResponse(
            "403.html",
            {"request": request, "user": user},
            status_code=403
        )
    
    # Get author
    if post.get("user_id"):
        authors = db.select("users", filters={"id": post["user_id"]})
        if authors:
            post["author"] = authors[0]
    
    # Get comments with authors
    comments = db.select("comments", filters={"post_id": post_id, "is_active": True}, order_by="created_at asc")
    
    # Organize comments into tree structure
    comment_map = {}
    root_comments = []
    
    for comment in comments:
        # Get comment author
        if comment.get("user_id"):
            comment_authors = db.select("users", filters={"id": comment["user_id"]})
            if comment_authors:
                comment["author"] = comment_authors[0]
        
        comment["replies"] = []
        comment_map[comment["id"]] = comment
        
        if comment.get("parent_id"):
            parent = comment_map.get(comment["parent_id"])
            if parent:
                parent["replies"].append(comment)
        else:
            root_comments.append(comment)
    
    # Update view count - increment on every visit
    new_view_count = post.get("view_count", 0) + 1
    db.update("posts", {"view_count": new_view_count}, {"id": post_id})
    post["view_count"] = new_view_count
    
    csrf_token = generate_csrf_token()
    request.session["csrf_token"] = csrf_token
    
    # Check if user can edit/delete
    can_edit = False
    if user:
        if user.get("sub") == post.get("user_id") or is_admin:
            can_edit = True
    
    return templates.TemplateResponse(
        "posts/detail.html",
        {
            "request": request,
            "user": user,
            "board": board,
            "post": post,
            "comments": root_comments,
            "can_edit": can_edit,
            "csrf_token": csrf_token,
            "from_page": from_page
        }
    )

@app.get("/boards/{board_slug}/posts/{post_id}/edit", response_class=HTMLResponse)
async def edit_post_page(request: Request, board_slug: str, post_id: str):
    """Edit post page"""
    from .database import db
    
    # Check if user is logged in
    user = getattr(request.state, "user", None)
    if not user:
        return templates.TemplateResponse(
            "403.html",
            {"request": request, "user": user},
            status_code=403
        )
    
    # Get board
    boards = db.select("boards", filters={"slug": board_slug})
    if not boards:
        raise HTTPException(status_code=404, detail="Board not found")
    
    board = boards[0]
    
    # Get post
    posts = db.select("posts", filters={"id": post_id, "board_id": board["id"]})
    if not posts:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post = posts[0]
    
    # Check if user can edit and get user info
    is_admin = False
    user_profiles = db.select("users", filters={"id": user.get("sub")})
    if user_profiles:
        user_profile = user_profiles[0]
        is_admin = user_profile.get("is_admin", False)
        user["is_admin"] = is_admin
        user["username"] = user_profile.get("username")
        user["email"] = user_profile.get("email")
    
    if user.get("sub") != post.get("user_id") and not is_admin:
        return templates.TemplateResponse(
            "403.html",
            {"request": request, "user": user},
            status_code=403
        )
    
    csrf_token = generate_csrf_token()
    request.session["csrf_token"] = csrf_token
    
    return templates.TemplateResponse(
        "posts/edit.html",
        {
            "request": request,
            "user": user,
            "board": board,
            "post": post,
            "csrf_token": csrf_token
        }
    )

@app.get("/boards/new", response_class=HTMLResponse)
async def create_board_page(request: Request):
    """Create new board page - admin only"""
    from .database import db
    
    # Check if user is logged in
    user = getattr(request.state, "user", None)
    if not user:
        return templates.TemplateResponse(
            "403.html",
            {"request": request, "user": user},
            status_code=403
        )
    
    # Check if user is admin
    user_profiles = db.select("users", filters={"id": user.get("sub")})
    if not user_profiles or not user_profiles[0].get("is_admin", False):
        return templates.TemplateResponse(
            "403.html",
            {"request": request, "user": user},
            status_code=403
        )
    
    user_profile = user_profiles[0]
    user["is_admin"] = user_profile.get("is_admin", False)
    user["username"] = user_profile.get("username")
    user["email"] = user_profile.get("email")
    
    csrf_token = generate_csrf_token()
    request.session["csrf_token"] = csrf_token
    
    return templates.TemplateResponse(
        "boards/new.html",
        {
            "request": request,
            "user": user,
            "csrf_token": csrf_token
        }
    )

@app.get("/boards/{board_slug}", response_class=HTMLResponse)
async def board_list_page(request: Request, board_slug: str, page: int = 1, q: str = None):
    """Redirect board page to main page with board parameter"""
    from fastapi.responses import RedirectResponse
    
    # Build redirect URL
    redirect_url = f"/?board={board_slug}"
    if page and page > 1:
        redirect_url += f"&page={page}"
    if q:
        redirect_url += f"&q={q}"
    
    return RedirectResponse(url=redirect_url, status_code=302)

# ==================== Search API ====================

@app.get("/api/search/posts-html", response_class=HTMLResponse)
async def search_all_posts_html(
    request: Request,
    q: str,
    search_type: str = "all",
    page: int = 1
):
    """Search posts across all boards and return HTML for HTMX"""
    from .database import db
    
    # Get current user
    user = getattr(request.state, "user", None)
    
    # Get all boards user can read
    all_boards = db.select("boards", filters={"is_active": True}, order_by="display_order asc, name asc")
    visible_boards = []
    
    # Check if user is admin and get user info
    is_admin = False
    if user:
        user_profiles = db.select("users", filters={"id": user.get("sub")})
        if user_profiles:
            user_profile = user_profiles[0]
            is_admin = user_profile.get("is_admin", False)
            user["is_admin"] = is_admin
            user["username"] = user_profile.get("username")
            user["email"] = user_profile.get("email")
    
    # Filter boards by read permission
    board_ids = []
    for board in all_boards:
        can_read = board.get("can_read", "all")
        
        if can_read == "all":
            visible_boards.append(board)
            board_ids.append(board["id"])
        elif can_read == "member" and user:
            visible_boards.append(board)
            board_ids.append(board["id"])
        elif can_read == "admin" and is_admin:
            visible_boards.append(board)
            board_ids.append(board["id"])
    
    if not board_ids:
        # No boards accessible
        return templates.TemplateResponse(
            "partials/search_results.html",
            {
                "request": request,
                "posts": [],
                "search_query": q,
                "search_type": search_type,
                "page": page,
                "total_pages": 1
            }
        )
    
    # Search posts
    per_page = 20
    offset = (page - 1) * per_page
    
    try:
        # Use PostgreSQL full-text search via RPC
        search_results = db.rpc("search_posts", {
            "search_query": q,
            "search_type": search_type,
            "board_ids": board_ids if board_ids else None
        })
        
        # Add board info to each post
        for post in search_results:
            board = next(b for b in visible_boards if b["id"] == post["board_id"])
            post["board_name"] = board["name"]
            post["board_slug"] = board["slug"]
        
        # Get total count and paginate
        total_count = len(search_results)
        posts = search_results[offset:offset + per_page]
        
    except Exception as e:
        # Fallback to ILIKE search if RPC fails
        logger.error(f"Full-text search failed: {e}, falling back to ILIKE")
        
        # Search across all accessible boards
        all_posts = []
        for board_id in board_ids:
            try:
                query = db.client.table("posts").select("*")
                query = query.eq("board_id", board_id).eq("is_active", True)
                
                # Apply ILIKE search filter
                if search_type == "title":
                    query = query.ilike("title", f"%{q}%")
                elif search_type == "content":
                    query = query.ilike("content", f"%{q}%")
                else:
                    query = query.or_(f"title.ilike.%{q}%,content.ilike.%{q}%")
                
                # Order by
                query = query.order("is_pinned.desc.nullslast,created_at.desc.nullslast,id.desc.nullslast")
                query = query.limit(100)  # Get more posts for sorting across boards
                
                response = query.execute()
                board_posts = response.data
                
                # Add board info to each post
                board = next(b for b in visible_boards if b["id"] == board_id)
                for post in board_posts:
                    post["board_name"] = board["name"]
                    post["board_slug"] = board["slug"]
                    all_posts.append(post)
            except:
                continue
        
        # Sort all posts
        all_posts.sort(key=lambda x: (x.get("is_pinned", False), x.get("created_at", "")), reverse=True)
        
        # Get total count and paginate
        total_count = len(all_posts)
        posts = all_posts[offset:offset + per_page]
    
    # Enrich posts with author info and comment count
    for post in posts:
        # Get author
        if post.get("user_id"):
            authors = db.select("users", filters={"id": post["user_id"]})
            if authors:
                post["author_name"] = authors[0].get("username", "익명")
            else:
                post["author_name"] = "익명"
        else:
            post["author_name"] = "익명"
        
        # Get comment count
        comments = db.select("comments", filters={"post_id": post["id"], "is_active": True}, count=True)
        post["comment_count"] = comments[0]["count"] if comments else 0
    
    # Calculate total pages
    total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
    
    # Create page range for pagination
    page_range = list(range(1, total_pages + 1))
    
    # Render search results template
    return templates.TemplateResponse(
        "partials/search_results.html",
        {
            "request": request,
            "posts": posts,
            "search_query": q,
            "search_type": search_type,
            "page": page,
            "total_pages": total_pages,
            "page_range": page_range,
            "total_count": total_count
        }
    )

# ==================== Static Pages ====================

@app.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request):
    """Terms of service page"""
    user = getattr(request.state, "user", None)
    return templates.TemplateResponse(
        "terms.html",
        {"request": request, "user": user}
    )

@app.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    """Privacy policy page"""
    user = getattr(request.state, "user", None)
    return templates.TemplateResponse(
        "privacy.html",
        {"request": request, "user": user}
    )

# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": settings.app_name}

# ==================== Error Handlers ====================

@app.exception_handler(404)
async def not_found_handler(request: Request, _exc):
    """404 error handler"""
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=404,
            content={"error": "Not found"}
        )
    
    return templates.TemplateResponse(
        "404.html",
        {"request": request},
        status_code=404
    )

@app.exception_handler(403) 
async def forbidden_handler(request: Request, _exc):
    """403 error handler"""
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=403,
            content={"error": "Forbidden"}
        )
    
    user = getattr(request.state, "user", None)
    
    # Get user info if logged in
    if user:
        from .database import db
        user_profiles = db.select("users", filters={"id": user.get("sub")})
        if user_profiles:
            user_profile = user_profiles[0]
            user["is_admin"] = user_profile.get("is_admin", False)
            user["username"] = user_profile.get("username")
            user["email"] = user_profile.get("email")
    
    csrf_token = generate_csrf_token()
    request.session["csrf_token"] = csrf_token
    
    return templates.TemplateResponse(
        "403.html",
        {"request": request, "user": user, "csrf_token": csrf_token},
        status_code=403
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, _exc):
    """500 error handler"""
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )
    
    return templates.TemplateResponse(
        "500.html",
        {"request": request},
        status_code=500
    )