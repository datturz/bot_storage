import logging
import functools
import asyncio
from datetime import datetime
from typing import Any, Callable, Optional
from config import Config

def setup_logging():
    """Setup cross-platform logging configuration with Unicode support"""
    import os
    import sys
    import platform
    
    # Create logs directory
    os.makedirs('./logs', exist_ok=True)
    
    # Configure console handler with proper encoding for Windows
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Set UTF-8 encoding for Windows console
    if platform.system() == 'Windows':
        try:
            # Try to set UTF-8 console encoding
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'replace')
        except Exception:
            # Fallback: use safe formatter without emojis
            pass
    
    # Setup logging with file handler (always UTF-8) and console handler
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('./logs/bot.log', encoding='utf-8'),
            console_handler
        ],
        force=True  # Override any existing handlers
    )
    
    # Suppress discord.py debug logs
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('discord.http').setLevel(logging.WARNING)

def log_command_usage(func: Callable) -> Callable:
    """Decorator to log command usage"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Get interaction from args (usually first argument)
        interaction = args[0] if args else None
        
        if hasattr(interaction, 'user') and hasattr(interaction, 'data'):
            command_name = interaction.data.get('name', 'unknown')
            user_id = interaction.user.id
            user_name = interaction.user.display_name
            
            logger = logging.getLogger(__name__)
            logger.info(f"🎮 Command '{command_name}' used by {user_name} (ID: {user_id})")
        
        return await func(*args, **kwargs)
    
    return wrapper

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry function on failure"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            logger = logging.getLogger(__name__)
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"❌ Function {func.__name__} failed after {max_retries} attempts: {e}")
                        raise
                    else:
                        logger.warning(f"⚠️ Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying...")
                        await asyncio.sleep(delay * (attempt + 1))  # Exponential backoff
            
        return wrapper
    return decorator

def format_datetime(dt: datetime, format_type: str = 'full') -> str:
    """Format datetime with timezone awareness"""
    if dt.tzinfo is None:
        dt = Config.TIMEZONE.localize(dt)
    
    local_dt = dt.astimezone(Config.TIMEZONE)
    
    if format_type == 'full':
        return local_dt.strftime('%Y-%m-%d %H:%M:%S WIB')
    elif format_type == 'date':
        return local_dt.strftime('%Y-%m-%d')
    elif format_type == 'time':
        return local_dt.strftime('%H:%M:%S')
    elif format_type == 'relative':
        now = datetime.now(Config.TIMEZONE)
        diff = local_dt - now
        
        if diff.days > 0:
            return f"{diff.days} hari lagi"
        elif diff.days == 0:
            hours = diff.seconds // 3600
            if hours > 0:
                return f"{hours} jam lagi"
            else:
                minutes = (diff.seconds % 3600) // 60
                return f"{minutes} menit lagi"
        else:
            return f"{abs(diff.days)} hari yang lalu"
    
    return str(local_dt)

def validate_item_type(item_type: str) -> bool:
    """Validate item type"""
    return item_type.upper() in Config.ITEM_TYPES

def sanitize_participant_names(participants: str) -> str:
    """Sanitize and format participant names"""
    # Split by comma, strip whitespace, remove empty strings
    names = [name.strip() for name in participants.split(',') if name.strip()]
    
    # Remove duplicates while preserving order
    unique_names = []
    for name in names:
        if name not in unique_names:
            unique_names.append(name)
    
    return ', '.join(unique_names)

def calculate_expire_date(created_at: datetime) -> datetime:
    """Calculate expire date based on creation date"""
    from datetime import timedelta
    return created_at + timedelta(days=Config.ITEM_EXPIRY_DAYS)

def parse_date_input(date_str: str) -> datetime:
    """Parse date input from various formats and return datetime with timezone"""
    from datetime import datetime
    import re
    
    date_str = date_str.strip()
    
    # Supported formats
    formats = [
        '%Y-%m-%d',        # 2024-01-15
        '%d/%m/%Y',        # 15/01/2024
        '%d-%m-%Y',        # 15-01-2024
        '%Y/%m/%d',        # 2024/01/15
        '%d.%m.%Y',        # 15.01.2024
        '%d %m %Y',        # 15 01 2024
    ]
    
    # Try each format
    parsed_date = None
    for format_str in formats:
        try:
            parsed_date = datetime.strptime(date_str, format_str)
            break
        except ValueError:
            continue
    
    if not parsed_date:
        raise ValueError(f"Format tanggal tidak dikenali: '{date_str}'")
    
    # Set time to current time and add timezone
    now = datetime.now(Config.TIMEZONE)
    parsed_date = parsed_date.replace(
        hour=now.hour, 
        minute=now.minute, 
        second=now.second
    )
    
    # Add timezone info
    parsed_date = Config.TIMEZONE.localize(parsed_date)
    
    # Validate date is not in the future (more than today)
    today = now.date()
    if parsed_date.date() > today:
        raise ValueError(f"Tanggal tidak boleh di masa depan: {parsed_date.date()}")
    
    return parsed_date

def get_item_status_emoji(days_until_expire: int) -> str:
    """Get status emoji based on days until expiration"""
    if days_until_expire <= 0:
        return "🔴"  # Expired
    elif days_until_expire <= 3:
        return "🔴"  # Critical
    elif days_until_expire <= 7:
        return "🟡"  # Warning
    else:
        return "🟢"  # Safe

def safe_log_message(message: str, fallback_message: str = None) -> str:
    """Create safe log message for cross-platform compatibility"""
    import platform
    
    # On Windows, check if we can safely display Unicode
    if platform.system() == 'Windows':
        try:
            # Test if message can be encoded with cp1252
            message.encode('cp1252')
            return message
        except UnicodeEncodeError:
            # Return fallback or sanitized version
            if fallback_message:
                return fallback_message
            # Remove emojis and Unicode chars
            import re
            # Remove emoji and special Unicode characters
            sanitized = re.sub(r'[^\x00-\x7F]+', '', message)
            return sanitized.strip() or "Bot message (Unicode not supported)"
    
    return message

def chunk_list(lst: list, chunk_size: int) -> list:
    """Split list into chunks of specified size"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def is_user_authorized(user_id: str) -> bool:
    """Check if user is authorized to use bot commands"""
    return str(user_id) in Config.AUTHORIZED_USERS

class RateLimiter:
    """Simple rate limiter for API calls"""
    def __init__(self, max_calls: int = 10, time_window: int = 60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if call is allowed for identifier"""
        now = datetime.now()
        
        if identifier not in self.calls:
            self.calls[identifier] = []
        
        # Remove old calls outside time window
        self.calls[identifier] = [
            call_time for call_time in self.calls[identifier]
            if (now - call_time).seconds < self.time_window
        ]
        
        # Check if under limit
        if len(self.calls[identifier]) < self.max_calls:
            self.calls[identifier].append(now)
            return True
        
        return False

class Cache:
    """Simple in-memory cache"""
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            value, expiry = self.cache[key]
            if datetime.now() < expiry:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        ttl = ttl or self.default_ttl
        expiry = datetime.now() + timedelta(seconds=ttl)
        self.cache[key] = (value, expiry)
    
    def clear(self) -> None:
        """Clear all cache"""
        self.cache.clear()
    
    def cleanup(self) -> None:
        """Remove expired entries"""
        now = datetime.now()
        expired_keys = [
            key for key, (_, expiry) in self.cache.items()
            if now >= expiry
        ]
        for key in expired_keys:
            del self.cache[key]

# Global instances
rate_limiter = RateLimiter()
cache = Cache()

def format_error_message(error: Exception, context: str = None) -> str:
    """Format error message for logging"""
    error_msg = f"{type(error).__name__}: {str(error)}"
    if context:
        error_msg = f"[{context}] {error_msg}"
    return error_msg

async def safe_send_message(channel, *args, **kwargs):
    """Safely send message with error handling"""
    try:
        return await channel.send(*args, **kwargs)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Failed to send message: {e}")
        return None