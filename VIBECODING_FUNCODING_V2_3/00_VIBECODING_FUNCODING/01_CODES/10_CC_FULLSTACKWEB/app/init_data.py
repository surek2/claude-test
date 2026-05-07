"""
Initialize test data for AICOM community service
"""
import base64
from pathlib import Path
from .database import db
from .boards import create_initial_boards
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def clean_all_data():
    """Delete all existing data from tables"""
    try:
        # Delete in order to respect foreign key constraints
        logger.info("Cleaning existing data...")
        
        # Delete comments first
        db.client.table("comments").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        logger.info("Deleted all comments")
        
        # Delete posts
        db.client.table("posts").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        logger.info("Deleted all posts")
        
        # Delete boards
        db.client.table("boards").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        logger.info("Deleted all boards")
        
        # Delete users
        db.client.table("users").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        logger.info("Deleted all users")
        
        logger.info("All data cleaned successfully")
    except Exception as e:
        logger.error(f"Error cleaning data: {e}")
        raise


def create_admin_user():
    """Create admin user account as defined in TESTDATA.md"""
    admin_email = "admin@example.com"
    admin_password = "admin123"
    admin_username = "Admin User"
    
    try:
        # Create admin user in users table directly
        # Note: This won't create auth credentials - that needs to be done via Supabase dashboard
        user_data = {
            "id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",  # Fixed ID for consistency
            "email": admin_email,
            "username": admin_username,
            "is_admin": True,
            "created_at": datetime.utcnow().isoformat()
        }
        
        db.client.table("users").insert(user_data).execute()
        logger.info(f"Admin user created: {admin_email}")
        return user_data["id"]
            
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        return None


def create_test_user():
    """Create test user account as defined in TESTDATA.md"""
    test_email = "testuser@example.com"
    test_password = "test123"
    test_username = "testuser"
    
    try:
        # Create test user in users table directly
        # Note: This won't create auth credentials - that needs to be done via Supabase dashboard
        user_data = {
            "id": "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy",  # Fixed ID for consistency
            "email": test_email,
            "username": test_username,
            "is_admin": False,
            "created_at": datetime.utcnow().isoformat()
        }
        
        db.client.table("users").insert(user_data).execute()
        logger.info(f"Test user created: {test_email}")
        return user_data["id"]
            
    except Exception as e:
        logger.error(f"Error creating test user: {e}")
        return None


def create_test_image():
    """Create a simple test image and return as base64"""
    # Create a simple 100x100 red square as test image
    from PIL import Image
    import io
    
    # Create a simple red square image
    img = Image.new('RGB', (100, 100), color='red')
    
    # Add text to make it identifiable
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    
    # Try to use default font, fallback to basic if not available
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    # Draw text
    draw.text((10, 40), "TEST", fill='white', font=font)
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return f"data:image/jpeg;base64,{img_base64}"


def create_boards():
    """Create boards as defined in TESTDATA.md"""
    try:
        boards_data = [
            {
                "name": "공지사항",
                "slug": "notice",
                "description": "중요한 공지사항을 게시하는 게시판입니다.",
                "can_read": "all",  # 모든 사용자가 읽을 수 있음
                "can_write": "admin",  # 관리자만 쓸 수 있음
                "display_order": 0,
                "is_active": True
            },
            {
                "name": "뉴스레터",
                "slug": "newsletter",
                "description": "AICOM 뉴스레터를 모아놓은 게시판입니다.",
                "can_read": "all",  # 모든 사용자가 읽을 수 있음
                "can_write": "admin",  # 관리자만 쓸 수 있음
                "display_order": 1,
                "is_active": True
            },
            {
                "name": "자유게시판",
                "slug": "free",
                "description": "자유롭게 글을 작성할 수 있는 게시판입니다.",
                "can_read": "all",  # 모든 사용자가 읽을 수 있음
                "can_write": "member",  # 로그인된 사용자만 쓸 수 있음
                "display_order": 2,
                "is_active": True
            }
        ]
        
        for board_data in boards_data:
            db.client.table("boards").insert(board_data).execute()
            logger.info(f"Created board: {board_data['name']}")
            
    except Exception as e:
        logger.error(f"Error creating boards: {e}")
        raise


def create_initial_posts():
    """Create initial posts as defined in TESTDATA.md"""
    try:
        # Get admin user ID
        admin_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        
        # Get boards
        boards_response = db.client.table("boards").select("*").execute()
        boards = boards_response.data
        board_map = {board["slug"]: board["id"] for board in boards}
        
        # Create test image
        test_image = create_test_image()
        
        # Posts to create
        posts_data = [
            {
                "board_id": board_map["notice"],
                "title": "공지사항입니다",
                "content": f'<p>안녕하세요 공지사항입니다</p><p><img src="{test_image}" alt="testimg.jpg"></p>',
                "user_id": admin_id,
                "is_pinned": False,
                "view_count": 0,
                "is_active": True
            },
            {
                "board_id": board_map["newsletter"], 
                "title": "1차 뉴스레터",
                "content": f'<p>안녕하세요 뉴스레터입니다</p><p><img src="{test_image}" alt="testimg.jpg"></p>',
                "user_id": admin_id,
                "is_pinned": False,
                "view_count": 0,
                "is_active": True
            },
            {
                "board_id": board_map["free"],
                "title": "안녕하세요. 가입인사드립니다",
                "content": '<p>안녕하세요 Admin User입니다 가입인사 드립니다.</p>',
                "user_id": admin_id,
                "is_pinned": False,
                "view_count": 0,
                "is_active": True
            }
        ]
        
        for post_data in posts_data:
            db.client.table("posts").insert(post_data).execute()
            logger.info(f"Created post: {post_data['title']}")
            
    except Exception as e:
        logger.error(f"Error creating initial posts: {e}")
        raise


def init_all_data():
    """Initialize all test data according to TESTDATA.md"""
    logger.info("Initializing test data...")
    
    try:
        # Clean all existing data first
        clean_all_data()
        
        # Create users
        create_admin_user()
        create_test_user()
        
        # Create boards
        create_boards()
        
        # Create initial posts
        create_initial_posts()
        
        logger.info("Test data initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        raise


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize all data
    init_all_data()