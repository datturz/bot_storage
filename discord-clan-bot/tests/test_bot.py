import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from config import Config
from database import DatabaseManager
from notifications import NotificationManager


class TestDatabaseManager:
    @pytest.fixture
    def db_manager(self):
        with patch('database.gspread'):
            return DatabaseManager()
    
    def test_get_next_number(self, db_manager):
        """Test getting next sequential number"""
        with patch.object(db_manager, 'worksheet') as mock_worksheet:
            mock_worksheet.get_all_values.return_value = [
                ['No', 'Nama Item', 'Type'],  # Header
                ['1', 'Item 1', 'UNIQUE'],
                ['2', 'Item 2', 'RED']
            ]
            
            next_no = db_manager._get_next_number()
            assert next_no == 3
    
    def test_validate_item_type(self):
        """Test item type validation"""
        from utils import validate_item_type
        
        assert validate_item_type('UNIQUE') == True
        assert validate_item_type('unique') == True
        assert validate_item_type('RED') == True
        assert validate_item_type('CONSUMABLE') == True
        assert validate_item_type('INVALID') == False
    
    def test_sanitize_participant_names(self):
        """Test participant name sanitization"""
        from utils import sanitize_participant_names
        
        result = sanitize_participant_names("Player1, Player2 ,  Player3")
        assert result == "Player1, Player2, Player3"
        
        result = sanitize_participant_names("Player1,,Player2,")
        assert result == "Player1, Player2"


class TestNotificationManager:
    @pytest.fixture
    def notification_manager(self):
        return NotificationManager()
    
    @pytest.mark.asyncio
    async def test_send_webhook_message(self, notification_manager):
        """Test webhook message sending"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 204
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            embed_data = {
                "title": "Test",
                "description": "Test message",
                "color": 0x00ff00
            }
            
            result = await notification_manager.send_webhook_message(embed_data)
            assert result == True
    
    @pytest.mark.asyncio
    async def test_send_expiring_items_alert(self, notification_manager):
        """Test expiring items alert"""
        expiring_items = [
            {
                'no': 1,
                'nama_item': 'Test Item',
                'type': 'UNIQUE',
                'participant': 'Player1',
                'expire_date': datetime.now(Config.TIMEZONE) + timedelta(days=3)
            }
        ]
        
        with patch.object(notification_manager, 'send_webhook_message', return_value=True) as mock_send:
            result = await notification_manager.send_expiring_items_alert(expiring_items)
            assert result == True
            mock_send.assert_called()


class TestUtils:
    def test_format_datetime(self):
        """Test datetime formatting"""
        from utils import format_datetime
        
        dt = datetime(2024, 1, 15, 14, 30, 0)
        dt_with_tz = Config.TIMEZONE.localize(dt)
        
        result = format_datetime(dt_with_tz, 'full')
        assert '2024-01-15 14:30:00 WIB' in result
        
        result = format_datetime(dt_with_tz, 'date')
        assert result == '2024-01-15'
    
    def test_get_item_status_emoji(self):
        """Test item status emoji"""
        from utils import get_item_status_emoji
        
        assert get_item_status_emoji(-1) == "🔴"  # Expired
        assert get_item_status_emoji(1) == "🔴"   # Critical
        assert get_item_status_emoji(5) == "🟡"   # Warning
        assert get_item_status_emoji(10) == "🟢"  # Safe
    
    def test_chunk_list(self):
        """Test list chunking"""
        from utils import chunk_list
        
        test_list = list(range(10))
        chunks = chunk_list(test_list, 3)
        
        assert len(chunks) == 4
        assert chunks[0] == [0, 1, 2]
        assert chunks[-1] == [9]
    
    def test_is_user_authorized(self):
        """Test user authorization"""
        from utils import is_user_authorized
        
        # Mock authorized users
        with patch.object(Config, 'AUTHORIZED_USERS', ['123456789', '987654321']):
            assert is_user_authorized('123456789') == True
            assert is_user_authorized('999999999') == False


class TestRateLimiter:
    def test_rate_limiter(self):
        """Test rate limiting"""
        from utils import RateLimiter
        
        limiter = RateLimiter(max_calls=2, time_window=60)
        
        # First two calls should be allowed
        assert limiter.is_allowed('user1') == True
        assert limiter.is_allowed('user1') == True
        
        # Third call should be blocked
        assert limiter.is_allowed('user1') == False
        
        # Different user should be allowed
        assert limiter.is_allowed('user2') == True


class TestCache:
    def test_cache_operations(self):
        """Test cache get/set operations"""
        from utils import Cache
        
        cache = Cache(default_ttl=300)
        
        # Test set and get
        cache.set('key1', 'value1')
        assert cache.get('key1') == 'value1'
        
        # Test non-existent key
        assert cache.get('nonexistent') is None
        
        # Test TTL
        cache.set('key2', 'value2', ttl=1)
        assert cache.get('key2') == 'value2'
        
        # Wait for expiration (in real test, use mock time)
        import time
        time.sleep(1.1)
        assert cache.get('key2') is None


class TestConfig:
    def test_config_validation(self):
        """Test configuration validation"""
        # Mock missing token
        with patch.object(Config, 'DISCORD_TOKEN', None):
            with pytest.raises(ValueError, match="DISCORD_TOKEN is required"):
                Config.validate()
        
        # Mock missing credentials file
        with patch('os.path.exists', return_value=False):
            with pytest.raises(ValueError, match="Google credentials file not found"):
                Config.validate()


@pytest.mark.asyncio
async def test_bot_startup():
    """Test bot startup process"""
    from bot import ClanStorageBot
    
    with patch('bot.DatabaseManager'), \
         patch('bot.NotificationManager'), \
         patch.object(Config, 'validate'), \
         patch('discord.ext.commands.Bot.tree') as mock_tree:
        
        bot = ClanStorageBot()
        mock_tree.sync = AsyncMock()
        
        # Test setup hook
        await bot.setup_hook()
        mock_tree.sync.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])