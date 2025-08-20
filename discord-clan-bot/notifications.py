import aiohttp
import discord
import logging
from datetime import datetime
from typing import List, Dict
from config import Config

logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self):
        self.webhook_url = Config.DISCORD_WEBHOOK_URL
    
    async def send_webhook_message(self, embed_data: dict, content: str = None) -> bool:
        """Send message via Discord webhook"""
        try:
            payload = {"embeds": [embed_data]}
            if content:
                payload["content"] = content
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status == 204:
                        logger.info("✅ Webhook message sent successfully")
                        return True
                    else:
                        logger.error(f"❌ Webhook failed with status: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Failed to send webhook message: {e}")
            return False
    
    async def send_startup_notification(self) -> bool:
        """Send bot startup notification"""
        try:
            embed = {
                "title": "🤖 Bot Clan Storage Aktif",
                "description": "Bot berhasil terhubung dan siap digunakan!",
                "color": 0x00ff00,  # Green
                "timestamp": datetime.now(Config.TIMEZONE).isoformat(),
                "fields": [
                    {
                        "name": "📊 Status",
                        "value": "✅ Online dan Siap",
                        "inline": True
                    },
                    {
                        "name": "⏰ Waktu Aktif",
                        "value": datetime.now(Config.TIMEZONE).strftime('%Y-%m-%d %H:%M:%S WIB'),
                        "inline": True
                    },
                    {
                        "name": "🛠️ Commands Available",
                        "value": "• `/add_item` - Tambah item baru\n• `/list_items` - Lihat semua item\n• `/check_expiring` - Cek item expire\n• `/status` - Status bot",
                        "inline": False
                    }
                ],
                "footer": {
                    "text": "Clan Storage Bot v1.0"
                }
            }
            
            return await self.send_webhook_message(embed)
            
        except Exception as e:
            logger.error(f"❌ Failed to send startup notification: {e}")
            return False
    
    async def send_expiring_items_alert(self, expiring_items: List[Dict]) -> bool:
        """Send alert for expiring items with user mentions"""
        try:
            if not expiring_items:
                return True
            
            # Create mention string for participants
            mentions = []
            participant_names = set()
            
            for item in expiring_items:
                participants = item['participant'].split(',')
                for participant in participants:
                    participant_name = participant.strip()
                    if participant_name:
                        participant_names.add(participant_name)
            
            # Format items list
            items_list = []
            for item in expiring_items:
                days_until_expire = (item['expire_date'] - datetime.now(Config.TIMEZONE)).days
                
                if days_until_expire <= 0:
                    status_emoji = "🔴"
                    status_text = "EXPIRED"
                elif days_until_expire <= 3:
                    status_emoji = "🔴"
                    status_text = f"{days_until_expire} hari lagi"
                else:
                    status_emoji = "🟡"
                    status_text = f"{days_until_expire} hari lagi"
                
                items_list.append(
                    f"{status_emoji} **{item['nama_item']}** ({item['type']})\n"
                    f"👥 {item['participant']} | ⏰ {status_text}"
                )
            
            embed = {
                "title": "⚠️ PERINGATAN: Item Akan Expire!",
                "description": f"Ada **{len(expiring_items)}** item yang akan expire dalam {Config.NOTIFICATION_DAYS_BEFORE} hari:",
                "color": 0xff6600,  # Orange
                "timestamp": datetime.now(Config.TIMEZONE).isoformat(),
                "fields": [
                    {
                        "name": "📦 Daftar Item",
                        "value": "\n\n".join(items_list[:10]),  # Limit to 10 items per embed
                        "inline": False
                    },
                    {
                        "name": "👥 Participant Terlibat",
                        "value": ", ".join(sorted(participant_names)),
                        "inline": False
                    },
                    {
                        "name": "📝 Tindakan yang Diperlukan",
                        "value": "• Gunakan item sebelum expire\n• Koordinasi dengan participant lain\n• Update storage jika item sudah digunakan",
                        "inline": False
                    }
                ],
                "footer": {
                    "text": f"Cek otomatis setiap hari • Notifikasi {Config.NOTIFICATION_DAYS_BEFORE} hari sebelum expire"
                }
            }
            
            # Create content with @here mention
            content = "🚨 @here **PERINGATAN ITEM EXPIRE!** 🚨"
            
            # Send main notification
            success = await self.send_webhook_message(embed, content)
            
            # If there are more than 10 items, send additional embeds
            if len(expiring_items) > 10:
                remaining_items = items_list[10:]
                chunks = [remaining_items[i:i+10] for i in range(0, len(remaining_items), 10)]
                
                for i, chunk in enumerate(chunks, 1):
                    additional_embed = {
                        "title": f"⚠️ Item Expire - Lanjutan ({i})",
                        "description": f"Item lainnya yang akan expire:",
                        "color": 0xff6600,
                        "fields": [
                            {
                                "name": "📦 Daftar Item (Lanjutan)",
                                "value": "\n\n".join(chunk),
                                "inline": False
                            }
                        ],
                        "timestamp": datetime.now(Config.TIMEZONE).isoformat()
                    }
                    
                    await self.send_webhook_message(additional_embed)
            
            if success:
                logger.info(f"📢 Expiring items alert sent for {len(expiring_items)} items")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to send expiring items alert: {e}")
            return False
    
    async def send_item_added_notification(self, nama_item: str, item_type: str, participant: str, added_by: str) -> bool:
        """Send notification when new item is added"""
        try:
            embed = {
                "title": "✅ Item Baru Ditambahkan",
                "description": f"Item baru telah ditambahkan ke storage clan",
                "color": 0x00ff00,  # Green
                "timestamp": datetime.now(Config.TIMEZONE).isoformat(),
                "fields": [
                    {
                        "name": "📦 Nama Item",
                        "value": nama_item,
                        "inline": True
                    },
                    {
                        "name": "🏷️ Tipe",
                        "value": item_type,
                        "inline": True
                    },
                    {
                        "name": "👥 Participant",
                        "value": participant,
                        "inline": False
                    },
                    {
                        "name": "⏰ Expire",
                        "value": f"{Config.ITEM_EXPIRY_DAYS} hari dari sekarang",
                        "inline": True
                    },
                    {
                        "name": "👤 Ditambahkan oleh",
                        "value": added_by,
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "Jangan lupa gunakan sebelum expire!"
                }
            }
            
            return await self.send_webhook_message(embed)
            
        except Exception as e:
            logger.error(f"❌ Failed to send item added notification: {e}")
            return False
    
    async def send_error_notification(self, error_message: str, context: str = None) -> bool:
        """Send error notification to webhook"""
        try:
            embed = {
                "title": "❌ Bot Error",
                "description": "Terjadi kesalahan pada bot",
                "color": 0xff0000,  # Red
                "timestamp": datetime.now(Config.TIMEZONE).isoformat(),
                "fields": [
                    {
                        "name": "🐛 Error Message",
                        "value": f"```{error_message[:1000]}```",  # Limit to 1000 chars
                        "inline": False
                    }
                ]
            }
            
            if context:
                embed["fields"].append({
                    "name": "📍 Context",
                    "value": context,
                    "inline": False
                })
            
            embed["footer"] = {
                "text": "Bot mungkin memerlukan restart atau perbaikan"
            }
            
            return await self.send_webhook_message(embed)
            
        except Exception as e:
            logger.error(f"❌ Failed to send error notification: {e}")
            return False
    
    async def test_webhook(self) -> bool:
        """Test webhook connection"""
        try:
            embed = {
                "title": "🧪 Test Webhook",
                "description": "Webhook berfungsi dengan baik!",
                "color": 0x0099ff,  # Blue
                "timestamp": datetime.now(Config.TIMEZONE).isoformat(),
                "footer": {
                    "text": "Test notification"
                }
            }
            
            return await self.send_webhook_message(embed)
            
        except Exception as e:
            logger.error(f"❌ Webhook test failed: {e}")
            return False