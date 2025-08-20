import gspread
from google.auth import default
from google.auth.exceptions import GoogleAuthError
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from config import Config
import os

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.gc = None
        self.worksheet = None
        self._connect_google_sheets()
    
    
    def _connect_google_sheets(self):
        """Connect to Google Sheets"""
        try:
            if os.path.exists(Config.GOOGLE_CREDENTIALS_PATH):
                self.gc = gspread.service_account(filename=Config.GOOGLE_CREDENTIALS_PATH)
            else:
                # Fallback to default credentials
                creds, _ = default()
                self.gc = gspread.authorize(creds)
            
            self.worksheet = self.gc.open_by_key(Config.GOOGLE_SHEETS_ID).worksheet(Config.WORKSHEET_NAME)
            
            # Ensure headers exist
            self._ensure_headers()
            logger.info("✅ Connected to Google Sheets")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Google Sheets: {e}")
            logger.info("📱 Google Sheets connection required for bot operation")
    
    def _ensure_headers(self):
        """Ensure Google Sheets has proper headers"""
        if not self.worksheet:
            return
        
        headers = ['No', 'Nama Item', 'Type', 'Participant', 'CreatedAt', 'UpdateAt', 'Expire']
        
        try:
            existing_headers = self.worksheet.row_values(1)
            if not existing_headers or existing_headers != headers:
                self.worksheet.update('A1:G1', [headers])
                logger.info("📋 Headers updated in Google Sheets")
        except Exception as e:
            logger.error(f"❌ Failed to update headers: {e}")
    
    def add_item(self, nama_item: str, item_type: str, participant: str, custom_created_at: datetime = None) -> bool:
        """Add new item to storage with optional custom creation date"""
        try:
            # Use custom created date or current time
            if custom_created_at:
                created_at = custom_created_at
            else:
                created_at = datetime.now(Config.TIMEZONE)
            
            expire_date = created_at + timedelta(days=Config.ITEM_EXPIRY_DAYS)
            
            # Get next number
            next_no = self._get_next_number()
            
            # Format dates for sheets
            created_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
            expire_str = expire_date.strftime('%Y-%m-%d %H:%M:%S')
            
            # Add to Google Sheets
            if not self.worksheet:
                logger.error("❌ Google Sheets not connected")
                return False
            
            try:
                row = [next_no, nama_item, item_type.upper(), participant, created_str, created_str, expire_str]
                self.worksheet.append_row(row)
                logger.info(f"✅ Item added to Google Sheets: {nama_item}")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to add to Google Sheets: {e}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Failed to add item: {e}")
            return False
    
    def _get_next_number(self) -> int:
        """Get next sequential number for items"""
        try:
            if not self.worksheet:
                return 1
            
            # Get all values and find max number
            values = self.worksheet.get_all_values()
            if len(values) > 1:  # Skip header
                numbers = []
                for row in values[1:]:
                    if row and row[0].isdigit():
                        numbers.append(int(row[0]))
                return max(numbers) + 1 if numbers else 1
            
            return 1
            
        except Exception as e:
            logger.error(f"❌ Failed to get next number: {e}")
            return 1
    
    
    def get_expiring_items(self) -> List[Dict]:
        """Get items expiring within notification period"""
        try:
            if not self.worksheet:
                logger.error("❌ Google Sheets not connected")
                return []
            
            notification_date = datetime.now(Config.TIMEZONE) + timedelta(days=Config.NOTIFICATION_DAYS_BEFORE)
            expiring_items = []
            
            records = self.worksheet.get_all_records()
            for record in records:
                expire_str = record.get('Expire', '')
                if expire_str:
                    expire_date = datetime.strptime(expire_str, '%Y-%m-%d %H:%M:%S')
                    expire_date = Config.TIMEZONE.localize(expire_date)
                    
                    if expire_date <= notification_date:
                        expiring_items.append({
                            'no': record.get('No'),
                            'nama_item': record.get('Nama Item'),
                            'type': record.get('Type'),
                            'participant': record.get('Participant'),
                            'expire_date': expire_date
                        })
            
            return expiring_items
            
        except Exception as e:
            logger.error(f"❌ Failed to get expiring items: {e}")
            return []
    
    def get_all_items(self) -> List[Dict]:
        """Get all items from storage"""
        try:
            if not self.worksheet:
                logger.error("❌ Google Sheets not connected")
                return []
            
            return self.worksheet.get_all_records()
                
        except Exception as e:
            logger.error(f"❌ Failed to get all items: {e}")
            return []
    
    def is_connected(self) -> bool:
        """Check if Google Sheets is connected"""
        return self.worksheet is not None