import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Config:
    # Google Sheets
    GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
    SERVICE_ACCOUNT_FILE = Path(__file__).parent.parent.parent / 'config' / 'service-account-key.json'
    
    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Google Drive
    GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
    
    # Application Settings
    CHECK_INTERVAL_MINUTES = int(os.getenv('CHECK_INTERVAL_MINUTES', '5'))
    MAX_PHOTOS_PER_RUN = int(os.getenv('MAX_PHOTOS_PER_RUN', '10'))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # File tracking
    PROCESSED_FILES_DB = Path(__file__).parent.parent.parent / 'data' / 'processed_files.json'
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        errors = []
        
        if not cls.GOOGLE_SHEET_ID:
            errors.append("GOOGLE_SHEET_ID is required")
        
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")
        
        if not cls.SERVICE_ACCOUNT_FILE.exists():
            errors.append(f"Service account file not found at {cls.SERVICE_ACCOUNT_FILE}")
        
        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(errors))
        
        # Create data directory if it doesn't exist
        cls.PROCESSED_FILES_DB.parent.mkdir(exist_ok=True)
        
        return True

config = Config()