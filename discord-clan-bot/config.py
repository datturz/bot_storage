import os
from dotenv import load_dotenv
from typing import List
import pytz

load_dotenv()

class Config:
    # Discord Configuration
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', 
        'https://discord.com/api/webhooks/1407224359231426560/oS1htouI5MlFXg2TGZY-pF8RM_ScT3AEyc1t8O0aJ8zrlVrJf_9JdKe15glGA_rTVDNR')
    
    # Google Sheets Configuration
    GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID', '1fJxa8j66yuXiRYnWLbwfEJu4Tplb76Riu-F7y3PVcr4')
    GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', './credentials/google_service_account.json')
    WORKSHEET_NAME = 'Sheet1'
    
    # Authorization
    AUTHORIZED_USERS: List[str] = os.getenv('AUTHORIZED_USERS', '').split(',')
    
    # Bot Settings
    TIMEZONE = pytz.timezone(os.getenv('TIMEZONE', 'Asia/Jakarta'))
    NOTIFICATION_DAYS_BEFORE = int(os.getenv('NOTIFICATION_DAYS_BEFORE', '7'))
    ITEM_EXPIRY_DAYS = 30
    
    # Item Types
    ITEM_TYPES = ['UNIQUE', 'RED', 'CONSUMABLE']
    
    # Validation
    @classmethod
    def validate(cls):
        errors = []
        if not cls.DISCORD_TOKEN:
            errors.append("DISCORD_TOKEN is required")
        if not os.path.exists(cls.GOOGLE_CREDENTIALS_PATH):
            errors.append(f"Google credentials file not found: {cls.GOOGLE_CREDENTIALS_PATH}")
        if not cls.AUTHORIZED_USERS or cls.AUTHORIZED_USERS == ['']:
            errors.append("AUTHORIZED_USERS must be set")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True