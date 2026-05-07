"""
Comment management module for AICOM community service.
Handles comment CRUD operations with hierarchical structure.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from fastapi import APIRouter, Depends, HTTPException, Request, Query
import bleach

from .auth import get_current_user, csrf_protect
from .database import db
from .posts import get_post_with_details
from .boards import get_board_by_id_or_slug, check_read_permission

# ==================== Schemas ====================

class CommentCreate(BaseModel):
    """Schema for creating a comment"""
    post_id: str
    parent_id: Optional[str] = None
    content: str = Field(..., min_length=1)
    
    @field_validator('content')
    def sanitize_content(cls, v):
        if v:
            # Allow safe HTML tags for rich text
            allowed_tags = [
                'p', 'br', 'span', 'div',
                'strong', 'b', 'em', 'i', 'u',
                'ul', 'ol', 'li',
                'blockquote', 'pre', 'code',
                'a'
            ]
            allowed_attributes = {
                'a': ['href', 'title']
            }
            # Clean HTML
            cleaned = bleach.clean(
                v,
                tags=allowed_tags,
                attributes=allowed_attributes,
                protocols=['http', 'https', 'data'],  # Allow data for base64 images
                strip=True
            )
            return cleaned
        return v


class CommentUpdate(BaseModel):
    """Schema for updating a comment"""
    content: str = Field(..., min_length=1)
    
    @field_validator('content')
    def sanitize_content(cls, v):
        if v:
            # Same sanitization as CommentCreate
            allowed_tags = [
                'p', 'br', 'span', 'div',
                'strong', 'b', 'em', 'i', 'u',
                'ul', 'ol', 'li',
                'blockquote', 'pre', 'code',
                'a'
            ]
            allowed_attributes = {
                'a': ['href', 'title']
            }
            cleaned = bleach.clean(
                v,
                tags=allowed_tags,
                attributes=allowed_attributes,
                protocols=['http', 'https', 'data'],  # Allow data for base64 images
                strip=True
            )
            return cleaned
        return v


class CommentResponse(BaseModel):
    """Schema for comment response"""
    id: str
    post_id: str
    user_id: str
    parent_id: Optional[str]
    content: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    author: Optional[Dict[str, Any]] = None
    replies: List['CommentResponse'] = []


# Update forward reference
CommentResponse.model_rebuild()


# ==================== Helper Functions ====================

def get_comment_with_author(comment_id: str) -> Optional[dict]:
    """Get comment with author details"""
    comments = db.select("comments", filters={"id": comment_id, "is_active": True})
    if not comments:
        return None
    
    comment = comments[0]
    
    # Get author info
    authors = db.select("users", filters={"id": comment["user_id"]})
    if authors:
        comment["author"] = {
            "id": authors[0]["id"],
            "username": authors[0]["username"],
            "email": authors[0]["email"]
        }
    
    return comment


def build_comment_tree(comments: List[dict]) -> List[dict]:
    """Build hierarchical comment tree from flat list"""
    # Create a mapping of comment_id to comment
    comment_map = {comment["id"]: comment for comment in comments}
    
    # Initialize replies list for each comment
    for comment in comments:
        comment["replies"] = []
    
    # Build the tree
    root_comments = []
    for comment in comments:
        if comment["parent_id"] is None:
            # Top-level comment
            root_comments.append(comment)
        else:
            # Reply - add to parent's replies
            parent = comment_map.get(comment["parent_id"])
            if parent:
                parent["replies"].append(comment)
    
    # Sort root comments by created_at
    root_comments.sort(key=lambda x: x["created_at"])
    
    return root_comments


# ==================== API Routes ====================

router = APIRouter(prefix="/api/comments", tags=["comments"])


@router.post("", response_model=CommentResponse, status_code=201, dependencies=[Depends(csrf_protect)])
async def create_comment(
    request: Request,
    comment_data: CommentCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new comment"""
    # Check authentication
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    # Get post and check if it exists
    post = get_post_with_details(comment_data.post_id)
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    
    # Get board and check read permissions
    board = get_board_by_id_or_slug(post["board_id"])
    if not board or not check_read_permission(board, current_user):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to comment on this post"
        )
    
    # Check parent comment if provided
    if comment_data.parent_id:
        parent_comments = db.select("comments", filters={
            "id": comment_data.parent_id,
            "post_id": comment_data.post_id,
            "is_active": True
        })
        
        if not parent_comments:
            raise HTTPException(
                status_code=404,
                detail="Parent comment not found"
            )
        
        # Check if parent already has a parent (prevent 3+ levels)
        if parent_comments[0]["parent_id"] is not None:
            raise HTTPException(
                status_code=400,
                detail="Comments can only be nested up to 2 levels"
            )
    
    # Create comment
    comment_dict = comment_data.model_dump()
    comment_dict["user_id"] = current_user["id"]
    
    try:
        comment = db.insert("comments", comment_dict)
    except Exception as e:
        # Check if it's the depth constraint error
        if "nested up to 2 levels" in str(e):
            raise HTTPException(
                status_code=400,
                detail="Comments can only be nested up to 2 levels"
            )
        raise
    
    # Get full comment details
    full_comment = get_comment_with_author(comment["id"])
    full_comment["replies"] = []
    
    return CommentResponse(**full_comment)


@router.get("", response_model=List[CommentResponse])
async def list_comments(
    request: Request,
    post_id: str = Query(..., description="Post ID to get comments for")
):
    """List comments for a post in hierarchical structure"""
    # Get current user (optional)
    user = get_current_user(request)
    
    # Get post and check if it exists
    post = get_post_with_details(post_id)
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    
    # Get board and check read permissions
    board = get_board_by_id_or_slug(post["board_id"])
    if not board or not check_read_permission(board, user):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to view comments for this post"
        )
    
    # Get all active comments for the post
    comments = db.select("comments", filters={"post_id": post_id, "is_active": True})
    
    # Add author info to each comment
    for comment in comments:
        authors = db.select("users", filters={"id": comment["user_id"]})
        if authors:
            comment["author"] = {
                "id": authors[0]["id"],
                "username": authors[0]["username"],
                "email": authors[0]["email"]
            }
    
    # Build hierarchical structure
    comment_tree = build_comment_tree(comments)
    
    return [CommentResponse(**comment) for comment in comment_tree]


@router.patch("/{comment_id}", response_model=CommentResponse, dependencies=[Depends(csrf_protect)])
async def update_comment(
    request: Request,
    comment_id: str,
    comment_data: CommentUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a comment"""
    # Check authentication
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    # Get comment
    comment = get_comment_with_author(comment_id)
    if not comment:
        raise HTTPException(
            status_code=404,
            detail="Comment not found"
        )
    
    # Check permission (author or admin)
    if comment["user_id"] != current_user["id"] and not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to update this comment"
        )
    
    # Update comment
    update_data = comment_data.model_dump()
    db.update("comments", update_data, {"id": comment_id})
    
    # Get updated comment
    updated_comment = get_comment_with_author(comment_id)
    updated_comment["replies"] = []
    
    return CommentResponse(**updated_comment)


@router.delete("/{comment_id}", status_code=204, dependencies=[Depends(csrf_protect)])
async def delete_comment(
    request: Request,
    comment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Soft delete a comment"""
    # Check authentication
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    # Get comment
    comments = db.select("comments", filters={"id": comment_id, "is_active": True})
    if not comments:
        raise HTTPException(
            status_code=404,
            detail="Comment not found"
        )
    
    comment = comments[0]
    
    # Check permission (author or admin)
    if comment["user_id"] != current_user["id"] and not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to delete this comment"
        )
    
    # Soft delete comment and all its replies
    def delete_comment_tree(comment_id: str):
        """Recursively delete comment and its replies"""
        # Delete the comment itself
        db.update("comments", {"is_active": False}, {"id": comment_id})
        
        # Find and delete all replies
        replies = db.select("comments", filters={"parent_id": comment_id, "is_active": True})
        for reply in replies:
            delete_comment_tree(reply["id"])
    
    delete_comment_tree(comment_id)
    
    # Return 204 No Content (no response body)
    return None