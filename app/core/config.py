from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Muse API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Defaulting to SQLite for easy team onboarding. 
    # Swap this to your PostgreSQL URL in the .env file later.
    DATABASE_URL: str = "sqlite:///./muse_dev.db" 

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()