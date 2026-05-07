from supabase import create_client, Client
from typing import Optional, Dict, Any, List
from .config import settings
import logging

logger = logging.getLogger(__name__)


class Database:
    """Database helper class for Supabase operations"""
    
    def __init__(self):
        # Ensure we're using service role key for all operations
        self.client: Client = create_client(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_service_role_key  # Use service role for server-side operations
        )
        # Set the auth header to use service role
        self.client.postgrest.auth(settings.supabase_service_role_key)
        self.auth_client = self.client.auth
        self.storage_client = self.client.storage
    
    # Auth operations
    def sign_up(self, email: str, password: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Sign up a new user with email and password"""
        try:
            response = self.auth_client.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "email_redirect_to": None,  # No email confirmation
                    "data": metadata or {}
                }
            })
            return response
        except Exception as e:
            logger.error(f"Sign up error: {str(e)}")
            raise
    
    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in a user with email and password"""
        try:
            response = self.auth_client.sign_in_with_password({
                "email": email,
                "password": password
            })
            return response
        except Exception as e:
            logger.error(f"Sign in error: {str(e)}")
            raise
    
    def sign_out(self, access_token: str) -> None:
        """Sign out a user"""
        try:
            # Set the access token for this request
            self.auth_client.sign_out(access_token)
        except Exception as e:
            logger.error(f"Sign out error: {str(e)}")
            raise
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            response = self.auth_client.refresh_session(refresh_token)
            return response
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise
    
    def get_user(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user details using access token"""
        try:
            response = self.auth_client.get_user(access_token)
            return response.user if response else None
        except Exception as e:
            logger.error(f"Get user error: {str(e)}")
            return None
    
    # Database operations
    def select(self, table: str, columns: str = "*", filters: Dict[str, Any] = None,
               order_by: str = None, limit: int = None, offset: int = None, 
               count: bool = False) -> List[Dict[str, Any]]:
        """Select data from a table with optional ordering, pagination, and count"""
        try:
            # If count is True, we want count instead of data
            if count:
                query = self.client.table(table).select(columns, count="exact")
            else:
                query = self.client.table(table).select(columns)
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            # Apply ordering
            if order_by and not count:
                # Parse order_by string (e.g., "created_at desc, name asc")
                # Apply all order clauses in the specified order
                order_clauses = order_by.split(",")
                for order_clause in order_clauses:
                    parts = order_clause.strip().split()
                    if len(parts) == 2:
                        column, direction = parts
                        query = query.order(column, desc=(direction.lower() == "desc"))
                    elif len(parts) == 1:
                        # Default to ascending if no direction specified
                        query = query.order(parts[0], desc=False)
            
            # Apply limit and offset
            if limit is not None and not count:
                query = query.limit(limit)
            if offset is not None and not count:
                query = query.offset(offset)
            
            response = query.execute()
            
            # Return count result if requested
            if count:
                return [{"count": response.count}]
            
            return response.data
        except Exception as e:
            logger.error(f"Select error: {str(e)}")
            raise
    
    def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert data into a table"""
        try:
            response = self.client.table(table).insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Insert error: {str(e)}")
            raise
    
    def update(self, table: str, data: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Update data in a table"""
        try:
            query = self.client.table(table).update(data)
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            response = query.execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Update error: {str(e)}")
            raise
    
    def delete(self, table: str, filters: Dict[str, Any]) -> bool:
        """Delete data from a table"""
        try:
            query = self.client.table(table).delete()
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            response = query.execute()
            return True
        except Exception as e:
            logger.error(f"Delete error: {str(e)}")
            raise
    
    # Storage operations
    def upload_file(self, bucket: str, path: str, file_data: bytes, content_type: str = None) -> str:
        """Upload a file to storage"""
        try:
            response = self.storage_client.from_(bucket).upload(
                path,
                file_data,
                file_options={"content-type": content_type} if content_type else None
            )
            
            # Get public URL
            public_url = self.storage_client.from_(bucket).get_public_url(path)
            return public_url
        except Exception as e:
            logger.error(f"File upload error: {str(e)}")
            raise
    
    def delete_file(self, bucket: str, paths: List[str]) -> bool:
        """Delete files from storage"""
        try:
            response = self.storage_client.from_(bucket).remove(paths)
            return True
        except Exception as e:
            logger.error(f"File delete error: {str(e)}")
            raise
    
    def get_file_url(self, bucket: str, path: str) -> str:
        """Get public URL for a file"""
        try:
            return self.storage_client.from_(bucket).get_public_url(path)
        except Exception as e:
            logger.error(f"Get file URL error: {str(e)}")
            raise
    
    # RPC operations
    def rpc(self, function_name: str, params: Dict[str, Any] = None) -> Any:
        """Execute a database function via RPC"""
        try:
            response = self.client.rpc(function_name, params or {}).execute()
            return response.data
        except Exception as e:
            logger.error(f"RPC error for {function_name}: {str(e)}")
            raise


# Create a single database instance
db = Database()