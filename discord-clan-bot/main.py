#!/usr/bin/env python3
"""
Discord Clan Storage Bot
A lightweight bot for managing game clan storage items with automatic expiration notifications.
"""

import asyncio
import signal
import sys
import logging
from datetime import datetime

from config import Config
from bot import bot
from utils import setup_logging, safe_log_message
from notifications import NotificationManager

logger = logging.getLogger(__name__)

class BotManager:
    def __init__(self):
        self.bot = bot
        self.notifications = NotificationManager()
        self.running = False
    
    async def start(self):
        """Start the bot with proper error handling"""
        try:
            # Setup logging
            setup_logging()
            logger.info(safe_log_message(
                "🚀 Starting Discord Clan Storage Bot...",
                "Starting Discord Clan Storage Bot..."
            ))
            
            # Validate configuration
            logger.info(safe_log_message(
                "🔧 Validating configuration...",
                "Validating configuration..."
            ))
            Config.validate()
            logger.info(safe_log_message(
                "✅ Configuration validated",
                "Configuration validated"
            ))
            
            # Test webhook connection
            logger.info(safe_log_message(
                "🔗 Testing webhook connection...",
                "Testing webhook connection..."
            ))
            webhook_test = await self.notifications.test_webhook()
            if webhook_test:
                logger.info(safe_log_message(
                    "✅ Webhook connection successful",
                    "Webhook connection successful"
                ))
            else:
                logger.warning(safe_log_message(
                    "⚠️ Webhook test failed, notifications may not work",
                    "Warning: Webhook test failed, notifications may not work"
                ))
            
            # Start bot
            self.running = True
            logger.info(safe_log_message(
                "🤖 Starting Discord bot...",
                "Starting Discord bot..."
            ))
            await self.bot.start(Config.DISCORD_TOKEN)
            
        except KeyboardInterrupt:
            logger.info(safe_log_message(
                "🛑 Received interrupt signal, shutting down...",
                "Received interrupt signal, shutting down..."
            ))
            await self.shutdown()
        except Exception as e:
            logger.error(safe_log_message(
                f"❌ Failed to start bot: {e}",
                f"Error: Failed to start bot: {e}"
            ))
            await self.notifications.send_error_notification(str(e), "Bot Startup")
            raise
    
    async def shutdown(self):
        """Gracefully shutdown the bot"""
        if self.running:
            logger.info(safe_log_message(
                "🛑 Shutting down bot...",
                "Shutting down bot..."
            ))
            self.running = False
            
            # Close bot connection
            if not self.bot.is_closed():
                await self.bot.close()
            
            # Send shutdown notification
            try:
                embed = {
                    "title": "🛑 Bot Shutdown",
                    "description": "Bot telah dimatikan",
                    "color": 0xff6600,  # Orange
                    "timestamp": datetime.now(Config.TIMEZONE).isoformat(),
                    "footer": {
                        "text": "Bot akan restart otomatis jika menggunakan process manager"
                    }
                }
                await self.notifications.send_webhook_message(embed)
            except Exception as e:
                logger.error(safe_log_message(
                    f"❌ Failed to send shutdown notification: {e}",
                    f"Error: Failed to send shutdown notification: {e}"
                ))
            
            logger.info(safe_log_message(
                "✅ Bot shutdown complete",
                "Bot shutdown complete"
            ))

def setup_signal_handlers(bot_manager):
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(safe_log_message(
            f"🛑 Received signal {signum}",
            f"Received signal {signum}"
        ))
        loop = asyncio.get_event_loop()
        loop.create_task(bot_manager.shutdown())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Main entry point"""
    bot_manager = BotManager()
    
    # Setup signal handlers
    setup_signal_handlers(bot_manager)
    
    try:
        await bot_manager.start()
    except Exception as e:
        logger.error(safe_log_message(
            f"❌ Bot crashed: {e}",
            f"Error: Bot crashed: {e}"
        ))
        sys.exit(1)

if __name__ == "__main__":
    try:
        # Check Python version
        if sys.version_info < (3, 8):
            print("Error: Python 3.8 or higher is required")
            sys.exit(1)
        
        # Run the bot
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)