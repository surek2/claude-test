"""
Post management module for AICOM community service.
Handles post CRUD operations and view tracking.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
import bleach

from .auth import get_current_user, csrf_protect
from .database import db
from .boards import get_board_by_id_or_slug, check_read_permission, check_write_permission
from .config import settings

# ==================== Schemas ====================

class PostCreate(BaseModel):
    """Schema for creating a post"""
    board_id: str
    title: str = Field(..., min_length=1, max_length=200)
    content: Optional[str] = None
    is_pinned: Optional[bool] = False
    
    @field_validator('content')
    def sanitize_content(cls, v):
        if v:
            # Allow safe HTML tags for rich text editor
            allowed_tags = [
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                'p', 'br', 'span', 'div',
                'strong', 'b', 'em', 'i', 'u',
                'ul', 'ol', 'li',
                'blockquote', 'pre', 'code',
                'a', 'img',
                'table', 'thead', 'tbody', 'tr', 'th', 'td'
            ]
            allowed_attributes = {
                'a': ['href', 'title'],  # target removed to prevent tabnabbing
                'img': ['src', 'alt', 'width', 'height'],
                'span': ['style'],
                'div': ['style'],
                'p': ['style'],
                'h1': ['style'], 'h2': ['style'], 'h3': ['style'],
                'h4': ['style'], 'h5': ['style'], 'h6': ['style']
            }
            allowed_styles = ['color', 'background-color', 'font-weight', 'font-style', 'text-decoration']
            allowed_protocols = ['http', 'https', 'data']  # Only allow these protocols
            
            # Custom filter for img src validation
            def filter_img_src(tag, name, value):
                if tag == 'img' and name == 'src':
                    # Only allow base64 data URIs for images
                    if value.startswith('data:image/'):
                        return True
                    return False
                return True
            
            # Clean HTML with enhanced security
            cleaned = bleach.clean(
                v,
                tags=allowed_tags,
                attributes=allowed_attributes,
                protocols=allowed_protocols,
                strip=True
            )
            
            # Second pass to ensure img src validation and size limit
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(cleaned, 'html.parser')
            max_image_size = 1 * 1024 * 1024  # 1MB limit
            
            for img in soup.find_all('img'):
                src = img.get('src', '')
                if not src.startswith('data:image/'):
                    img.decompose()  # Remove img tag if src is not base64
                elif len(src) > max_image_size * 1.33:  # Base64 is ~33% larger
                    # Replace large image with error message
                    error_span = soup.new_tag('span', attrs={'class': 'text-red-500'})
                    error_span.string = '[이미지 크기가 1MB를 초과합니다]'
                    img.replace_with(error_span)
            
            return str(soup)
        return v


class PostUpdate(BaseModel):
    """Schema for updating a post"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = None
    is_pinned: Optional[bool] = None
    
    @field_validator('content')
    def sanitize_content(cls, v):
        if v:
            # Same sanitization as PostCreate
            allowed_tags = [
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                'p', 'br', 'span', 'div',
                'strong', 'b', 'em', 'i', 'u',
                'ul', 'ol', 'li',
                'blockquote', 'pre', 'code',
                'a', 'img',
                'table', 'thead', 'tbody', 'tr', 'th', 'td'
            ]
            allowed_attributes = {
                'a': ['href', 'title'],  # target removed to prevent tabnabbing
                'img': ['src', 'alt', 'width', 'height'],
                'span': ['style'],
                'div': ['style'],
                'p': ['style'],
                'h1': ['style'], 'h2': ['style'], 'h3': ['style'],
                'h4': ['style'], 'h5': ['style'], 'h6': ['style']
            }
            allowed_styles = ['color', 'background-color', 'font-weight', 'font-style', 'text-decoration']
            allowed_protocols = ['http', 'https', 'data']  # Only allow these protocols
            
            cleaned = bleach.clean(
                v,
                tags=allowed_tags,
                attributes=allowed_attributes,
                protocols=allowed_protocols,
                strip=True
            )
            
            # Second pass to ensure img src validation and size limit
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(cleaned, 'html.parser')
            max_image_size = 1 * 1024 * 1024  # 1MB limit
            
            for img in soup.find_all('img'):
                src = img.get('src', '')
                if not src.startswith('data:image/'):
                    img.decompose()  # Remove img tag if src is not base64
                elif len(src) > max_image_size * 1.33:  # Base64 is ~33% larger
                    # Replace large image with error message
                    error_span = soup.new_tag('span', attrs={'class': 'text-red-500'})
                    error_span.string = '[이미지 크기가 1MB를 초과합니다]'
                    img.replace_with(error_span)
            
            return str(soup)
        return v


class PostResponse(BaseModel):
    """Schema for post response"""
    id: str
    board_id: str
    user_id: str
    title: str
    content: Optional[str]
    view_count: int
    is_pinned: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    author: Optional[Dict[str, Any]] = None
    board: Optional[Dict[str, Any]] = None


class PostListResponse(BaseModel):
    """Schema for paginated post list"""
    items: List[PostResponse]
    total: int
    page: int
    pages: int
    limit: int


class PinRequest(BaseModel):
    """Schema for pin/unpin request"""
    is_pinned: bool


# ==================== Helper Functions ====================

def get_post_with_details(post_id: str) -> Optional[dict]:
    """Get post with author and board details"""
    posts = db.select("posts", filters={"id": post_id, "is_active": True})
    if not posts:
        return None
    
    post = posts[0]
    
    # Get author info
    authors = db.select("users", filters={"id": post["user_id"]})
    if authors:
        post["author"] = {
            "id": authors[0]["id"],
            "username": authors[0]["username"],
            "email": authors[0]["email"]
        }
    
    # Get board info
    boards = db.select("boards", filters={"id": post["board_id"]})
    if boards:
        post["board"] = boards[0]  # Include all board fields
    
    
    return post


def track_view(request: Request, post_id: str, user_id: Optional[str]) -> bool:
    """Track post view and increment counter
    According to PROGRESS.md: '조회수 매번 증가하도록 변경 - 세션 기반 중복 방지 로직 제거'
    """
    # Increment view count every time
    post = db.select("posts", filters={"id": post_id})[0]
    new_count = post["view_count"] + 1
    db.update("posts", {"view_count": new_count}, {"id": post_id})
    
    return True


# ==================== API Routes ====================

router = APIRouter(prefix="/api/posts", tags=["posts"])


@router.post("/create", response_model=PostResponse, status_code=201, dependencies=[Depends(csrf_protect)])
async def create_post(
    request: Request,
    post_data: PostCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new post"""
    # Check authentication
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    # Get board and check permissions
    board = get_board_by_id_or_slug(post_data.board_id)
    if not board:
        raise HTTPException(
            status_code=404,
            detail="Board not found"
        )
    
    if not check_write_permission(board, current_user):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to write in this board"
        )
    
    # Create post
    post_dict = post_data.model_dump()
    post_dict["user_id"] = current_user["id"]
    post_dict["board_id"] = board["id"]  # Use board ID from database, not the input
    
    # Ensure content is not None (empty string is fine)
    if post_dict.get("content") is None:
        post_dict["content"] = ""
    
    # Only admin can pin posts
    if not current_user.get("is_admin", False):
        post_dict["is_pinned"] = False
    
    post = db.insert("posts", post_dict)
    
    # Get full post details
    full_post = get_post_with_details(post["id"])
    
    return PostResponse(**full_post)


@router.get("", response_model=PostListResponse)
async def list_posts(
    request: Request,
    board_id: str,
    page: int = 1,
    limit: int = 10
):
    """List posts in a board with pagination"""
    # Get current user (optional)
    user = get_current_user(request)
    
    # Get board and check permissions
    board = get_board_by_id_or_slug(board_id)
    if not board:
        raise HTTPException(
            status_code=404,
            detail="Board not found"
        )
    
    if not check_read_permission(board, user):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to read this board"
        )
    
    # Get total count
    count_result = db.select("posts", filters={"board_id": board["id"], "is_active": True}, count=True)
    total = count_result[0]["count"] if count_result else 0
    
    # Calculate pagination
    offset = (page - 1) * limit
    pages = (total + limit - 1) // limit if total > 0 else 1
    
    # Get posts with proper ordering using Supabase
    query = db.client.table("posts").select("*")
    query = query.eq("board_id", board["id"]).eq("is_active", True)
    # Use raw SQL ordering to ensure proper multi-column sort
    query = query.order("is_pinned.desc.nullslast,created_at.desc.nullslast,id.desc.nullslast")
    query = query.limit(limit).offset(offset)
    
    response = query.execute()
    paginated_posts = response.data
    
    # Get posts with author info
    posts = []
    
    for post in paginated_posts:
        full_post = get_post_with_details(post["id"])
        if full_post:
            posts.append(PostResponse(**full_post))
    
    return PostListResponse(
        items=posts,
        total=total,
        page=page,
        pages=pages,
        limit=limit
    )


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    request: Request,
    post_id: str
):
    """Get post details by ID"""
    # Get current user (optional)
    user = get_current_user(request)
    
    # Get post
    post = get_post_with_details(post_id)
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    
    # Get board and check permissions
    board = get_board_by_id_or_slug(post["board_id"])
    if not board or not check_read_permission(board, user):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to read this post"
        )
    
    # Track view
    user_id = user["id"] if user else None
    track_view(request, post_id, user_id)
    
    # Refresh post data to get updated view count
    post = get_post_with_details(post_id)
    
    return PostResponse(**post)


@router.patch("/{post_id}/update", response_model=PostResponse, dependencies=[Depends(csrf_protect)])
async def update_post(
    request: Request,
    post_id: str,
    post_data: PostUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a post"""
    # Check authentication
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    # Get post
    post = get_post_with_details(post_id)
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    
    # Check permission (author or admin)
    if post["user_id"] != current_user["id"] and not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to update this post"
        )
    
    # Update post
    update_data = post_data.model_dump(exclude_none=True)
    
    # Only admin can change pin status
    if "is_pinned" in update_data and not current_user.get("is_admin", False):
        del update_data["is_pinned"]
    
    if update_data:
        db.update("posts", update_data, {"id": post_id})
    
    # Get updated post
    updated_post = get_post_with_details(post_id)
    
    return PostResponse(**updated_post)


@router.delete("/{post_id}", dependencies=[Depends(csrf_protect)])
async def delete_post(
    request: Request,
    post_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Soft delete a post"""
    # Check authentication
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    # Get post
    posts = db.select("posts", filters={"id": post_id, "is_active": True})
    if not posts:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    
    post = posts[0]
    
    # Check permission (author or admin)
    if post["user_id"] != current_user["id"] and not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to delete this post"
        )
    
    # Soft delete
    db.update("posts", {"is_active": False}, {"id": post_id})
    
    # Return 204 No Content status code
    return Response(status_code=204)


@router.patch("/{post_id}/pin", response_model=PostResponse, dependencies=[Depends(csrf_protect)])
async def pin_post(
    request: Request,
    post_id: str,
    pin_data: PinRequest,
    current_user: dict = Depends(get_current_user)
):
    """Pin or unpin a post (admin only)"""
    # Check authentication
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    # Check admin permission
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=403,
            detail="Only administrators can pin posts"
        )
    
    # Get post
    post = get_post_with_details(post_id)
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    
    # Update pin status
    db.update("posts", {"is_pinned": pin_data.is_pinned}, {"id": post_id})
    
    # Get updated post
    updated_post = get_post_with_details(post_id)
    
    return PostResponse(**updated_post)