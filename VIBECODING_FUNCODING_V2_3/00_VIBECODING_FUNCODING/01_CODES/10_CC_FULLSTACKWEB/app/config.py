from pydantic_settings import BaseSettings
from pydantic import ConfigDict, field_validator
from typing import List
import json


class Settings(BaseSettings):
    # Supabase Configuration
    supabase_url: str
    supabase_anon_key: str
    supabase_jwt_secret: str
    supabase_service_role_key: str
    
    # App Configuration
    app_name: str = "AICOM"
    app_env: str = "development"
    secret_key: str
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Cookie Settings
    cookie_secure: bool = False
    cookie_httponly: bool = True
    cookie_samesite: str = "lax"
    
    # CORS Settings
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            # Parse JSON string from environment variable
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # If it's not valid JSON, treat it as a single origin
                return [v]
        return v
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


# Create a single settings instance
settings = Settings()