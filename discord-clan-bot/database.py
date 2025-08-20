import gspread
from google.auth import default
from google.auth.exceptions import GoogleAuthError
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from config import Config
import sqlite3
import os

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.gc = None
        self.worksheet = None
        self.backup_db_path = './data/backup.db'
        self._init_backup_db()
        self._connect_google_sheets()
    
    def _init_backup_db(self):
        """Initialize local SQLite backup database"""
        os.makedirs('./data', exist_ok=True)
        conn = sqlite3.connect(self.backup_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                no INTEGER,
                nama_item TEXT NOT NULL,
                type TEXT NOT NULL,
                participant TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expire_date TIMESTAMP NOT NULL,
                synced BOOLEAN DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Local backup database initialized")
    
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
            logger.info("📱 Using local backup database only")
    
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
    
    def add_item(self, nama_item: str, item_type: str, participant: str) -> bool:
        """Add new item to storage"""
        try:
            now = datetime.now(Config.TIMEZONE)
            expire_date = now + timedelta(days=Config.ITEM_EXPIRY_DAYS)
            
            # Get next number
            next_no = self._get_next_number()
            
            # Format dates for sheets
            created_str = now.strftime('%Y-%m-%d %H:%M:%S')
            expire_str = expire_date.strftime('%Y-%m-%d %H:%M:%S')
            
            # Try Google Sheets first
            success = False
            if self.worksheet:
                try:
                    row = [next_no, nama_item, item_type.upper(), participant, created_str, created_str, expire_str]
                    self.worksheet.append_row(row)
                    success = True
                    logger.info(f"✅ Item added to Google Sheets: {nama_item}")
                except Exception as e:
                    logger.error(f"❌ Failed to add to Google Sheets: {e}")
            
            # Add to local backup
            self._add_to_backup(next_no, nama_item, item_type.upper(), participant, now, expire_date, success)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add item: {e}")
            return False
    
    def _get_next_number(self) -> int:
        """Get next sequential number for items"""
        try:
            if self.worksheet:
                # Get all values and find max number
                values = self.worksheet.get_all_values()
                if len(values) > 1:  # Skip header
                    numbers = []
                    for row in values[1:]:
                        if row and row[0].isdigit():
                            numbers.append(int(row[0]))
                    return max(numbers) + 1 if numbers else 1
            
            # Fallback to backup database
            conn = sqlite3.connect(self.backup_db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT MAX(no) FROM items')
            result = cursor.fetchone()
            conn.close()
            
            return (result[0] + 1) if result[0] else 1
            
        except Exception as e:
            logger.error(f"❌ Failed to get next number: {e}")
            return 1
    
    def _add_to_backup(self, no: int, nama_item: str, item_type: str, participant: str, 
                       created_at: datetime, expire_date: datetime, synced: bool):
        """Add item to local backup database"""
        try:
            conn = sqlite3.connect(self.backup_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO items (no, nama_item, type, participant, created_at, updated_at, expire_date, synced)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (no, nama_item, item_type, participant, created_at, created_at, expire_date, synced))
            
            conn.commit()
            conn.close()
            logger.info(f"📱 Item backed up locally: {nama_item}")
            
        except Exception as e:
            logger.error(f"❌ Failed to backup item: {e}")
    
    def get_expiring_items(self) -> List[Dict]:
        """Get items expiring within notification period"""
        try:
            notification_date = datetime.now(Config.TIMEZONE) + timedelta(days=Config.NOTIFICATION_DAYS_BEFORE)
            expiring_items = []
            
            # Check Google Sheets first
            if self.worksheet:
                try:
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
                                
                except Exception as e:
                    logger.error(f"❌ Failed to check Google Sheets for expiring items: {e}")
            
            # Fallback to backup database
            if not expiring_items:
                conn = sqlite3.connect(self.backup_db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT no, nama_item, type, participant, expire_date
                    FROM items 
                    WHERE expire_date <= ?
                    ORDER BY expire_date ASC
                ''', (notification_date,))
                
                results = cursor.fetchall()
                conn.close()
                
                for row in results:
                    expire_date = datetime.fromisoformat(row[4])
                    if expire_date.tzinfo is None:
                        expire_date = Config.TIMEZONE.localize(expire_date)
                    
                    expiring_items.append({
                        'no': row[0],
                        'nama_item': row[1],
                        'type': row[2],
                        'participant': row[3],
                        'expire_date': expire_date
                    })
            
            return expiring_items
            
        except Exception as e:
            logger.error(f"❌ Failed to get expiring items: {e}")
            return []
    
    def get_all_items(self) -> List[Dict]:
        """Get all items from storage"""
        try:
            if self.worksheet:
                return self.worksheet.get_all_records()
            else:
                # Use backup database
                conn = sqlite3.connect(self.backup_db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM items ORDER BY no ASC')
                results = cursor.fetchall()
                conn.close()
                
                items = []
                for row in results:
                    items.append({
                        'No': row[1],
                        'Nama Item': row[2],
                        'Type': row[3],
                        'Participant': row[4],
                        'CreatedAt': row[5],
                        'UpdateAt': row[6],
                        'Expire': row[7]
                    })
                return items
                
        except Exception as e:
            logger.error(f"❌ Failed to get all items: {e}")
            return []
    
    def is_connected(self) -> bool:
        """Check if Google Sheets is connected"""
        return self.worksheet is not None