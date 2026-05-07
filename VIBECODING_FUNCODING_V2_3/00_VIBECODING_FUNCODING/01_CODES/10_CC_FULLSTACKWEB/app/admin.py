"""
Admin module for AICOM community service.
Handles admin dashboard and management functionality.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request, Depends, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from .config import settings
from .database import db
from .auth import require_admin, generate_csrf_token, csrf_protect
from .boards import BoardUpdate

# Templates
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

router = APIRouter(prefix="/admin", tags=["Admin"])

# ==================== Page Routes ====================

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Admin dashboard page"""
    # Check admin manually for HTML pages
    user = getattr(request.state, "user", None)
    
    if not user:
        return templates.TemplateResponse(
            "403.html",
            {"request": request, "user": user},
            status_code=403
        )
    
    # Get user profile to check admin status
    profiles = db.select("users", filters={"id": user.get("sub")})
    
    if not profiles or not profiles[0].get("is_admin", False):
        return templates.TemplateResponse(
            "403.html",
            {"request": request, "user": user},
            status_code=403
        )
    
    # Add user info to the user dict
    user["email"] = profiles[0].get("email")
    user["username"] = profiles[0].get("username")
    user["is_admin"] = profiles[0].get("is_admin")
    
    csrf_token = generate_csrf_token()
    request.session["csrf_token"] = csrf_token
    
    # Get all boards
    boards = db.select("boards")
    
    # Get all users
    users = db.select("users")
    
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "csrf_token": csrf_token,
            "user": user,
            "boards": boards,
            "users": users,
            "total_boards": len(boards),
            "total_users": len(users),
            "admin_users": len([u for u in users if u.get("is_admin", False)])
        }
    )

@router.get("/boards", response_class=HTMLResponse)
async def admin_boards(request: Request):
    """Admin boards management page"""
    # Check admin manually for HTML pages
    user = getattr(request.state, "user", None)
    
    if not user:
        return templates.TemplateResponse(
            "403.html",
            {"request": request, "user": user},
            status_code=403
        )
    
    # Get user profile to check admin status
    profiles = db.select("users", filters={"id": user.get("sub")})
    
    if not profiles or not profiles[0].get("is_admin", False):
        return templates.TemplateResponse(
            "403.html",
            {"request": request, "user": user},
            status_code=403
        )
    
    # Add user info to the user dict
    user["email"] = profiles[0].get("email")
    user["username"] = profiles[0].get("username")
    user["is_admin"] = profiles[0].get("is_admin")
    
    csrf_token = generate_csrf_token()
    request.session["csrf_token"] = csrf_token
    
    # Get all boards with stats
    boards = db.select("boards")
    
    # Get post count for each board
    for board in boards:
        posts = db.select("posts", filters={"board_id": board["id"]})
        board["post_count"] = len(posts)
    
    return templates.TemplateResponse(
        "admin/boards.html",
        {
            "request": request,
            "csrf_token": csrf_token,
            "user": user,
            "boards": boards
        }
    )

@router.get("/users", response_class=HTMLResponse)
async def admin_users(request: Request):
    """Admin users management page"""
    # Check admin manually for HTML pages
    user = getattr(request.state, "user", None)
    
    if not user:
        return templates.TemplateResponse(
            "403.html",
            {"request": request, "user": user},
            status_code=403
        )
    
    # Get user profile to check admin status
    profiles = db.select("users", filters={"id": user.get("sub")})
    
    if not profiles or not profiles[0].get("is_admin", False):
        return templates.TemplateResponse(
            "403.html",
            {"request": request, "user": user},
            status_code=403
        )
    
    # Add user info to the user dict
    user["email"] = profiles[0].get("email")
    user["username"] = profiles[0].get("username")
    user["is_admin"] = profiles[0].get("is_admin")
    
    csrf_token = generate_csrf_token()
    request.session["csrf_token"] = csrf_token
    
    # Get all users with stats
    users = db.select("users")
    
    # Get post count for each user
    for user_data in users:
        posts = db.select("posts", filters={"user_id": user_data["id"]})
        user_data["post_count"] = len(posts)
        comments = db.select("comments", filters={"user_id": user_data["id"]})
        user_data["comment_count"] = len(comments)
    
    return templates.TemplateResponse(
        "admin/users.html",
        {
            "request": request,
            "csrf_token": csrf_token,
            "user": user,
            "users": users
        }
    )

# ==================== API Routes ====================

@router.patch(
    "/api/boards/{board_id}",
    dependencies=[Depends(require_admin), Depends(csrf_protect)]
)
async def update_board_permissions(
    board_id: str,
    board_update: BoardUpdate
):
    """Update board permissions (admin only)"""
    # Check if board exists
    boards = db.select("boards", filters={"id": board_id})
    if not boards:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
    
    # Update board
    update_data = board_update.model_dump(exclude_unset=True)
    if update_data:
        db.update("boards", update_data, {"id": board_id})
    
    return {"message": "Board updated successfully"}

@router.post(
    "/api/users/{user_id}/toggle-admin",
    dependencies=[Depends(require_admin), Depends(csrf_protect)],
    response_class=HTMLResponse
)
async def toggle_user_admin(request: Request, user_id: str):
    """Toggle user admin status"""
    # Check if user exists
    users = db.select("users", filters={"id": user_id})
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_data = users[0]
    
    # Prevent removing last admin
    if user_data.get("is_admin", False):
        admin_count = len(db.select("users", filters={"is_admin": True}))
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last admin"
            )
    
    # Toggle admin status
    new_status = not user_data.get("is_admin", False)
    db.update("users", {"is_admin": new_status}, {"id": user_id})
    
    # Get updated user data with counts
    user_data["is_admin"] = new_status
    posts = db.select("posts", filters={"user_id": user_id})
    user_data["post_count"] = len(posts)
    comments = db.select("comments", filters={"user_id": user_id})
    user_data["comment_count"] = len(comments)
    
    # Get current user from request
    current_user = getattr(request.state, "user", {})
    csrf_token = request.session.get("csrf_token", "")
    
    # Return updated row HTML
    return f"""
    <tr class="border-b">
        <td class="p-4">
            <div class="font-medium">{user_data.get('username', '')}</div>
            <div class="text-sm text-muted-foreground">{user_data.get('email', '')}</div>
        </td>
        <td class="p-4 text-center">{user_data['post_count']}</td>
        <td class="p-4 text-center">{user_data['comment_count']}</td>
        <td class="p-4 text-center text-sm">
            {user_data.get('created_at', '')[:10] if user_data.get('created_at') else '-'}
        </td>
        <td class="p-4 text-center">
            {'<span class="inline-flex items-center rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary">관리자</span>' if new_status else '<span class="inline-flex items-center rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium text-muted-foreground">일반</span>'}
        </td>
        <td class="p-4 text-right">
            <button
                id="toggle-admin-{user_id}"
                hx-post="/admin/api/users/{user_id}/toggle-admin"
                hx-headers='{{"X-CSRF-Token": "{csrf_token}"}}'
                hx-target="closest tr"
                hx-swap="outerHTML"
                class="text-sm text-primary hover:underline {'hidden' if user_id == current_user.get('sub') else ''}"
            >
                {'관리자 해제' if new_status else '관리자 지정'}
            </button>
            {'<span class="text-sm text-muted-foreground">본인</span>' if user_id == current_user.get('sub') else ''}
        </td>
    </tr>
    """

@router.delete(
    "/api/boards/{board_id}",
    dependencies=[Depends(require_admin), Depends(csrf_protect)]
)
async def delete_board(board_id: str):
    """Delete a board"""
    # Check if board exists
    boards = db.select("boards", filters={"id": board_id})
    if not boards:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
    
    # Check if board has posts
    posts = db.select("posts", filters={"board_id": board_id})
    if posts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete board with existing posts"
        )
    
    # Soft delete the board
    db.update("boards", {"is_active": False}, {"id": board_id})
    
    return {"message": "Board deleted successfully"}