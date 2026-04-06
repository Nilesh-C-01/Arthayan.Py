import os

class Settings:
    PROJECT_NAME: str = "Zorvyn Finance Analytics"
    PROJECT_VERSION: str = "1.0.0"
    
    # Using SQLite for easy local testing, but this structure allows easy switch to Postgres
    SQLALCHEMY_DATABASE_URL: str = "sqlite:///./finance_prod.db"
    
settings = Settings()