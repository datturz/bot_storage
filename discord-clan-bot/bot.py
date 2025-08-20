import discord
from discord.ext import commands, tasks
import logging
from datetime import datetime
import asyncio
from typing import Optional
from config import Config
from database import DatabaseManager
from notifications import NotificationManager
from utils import safe_log_message

# Note: Logging is configured in utils.setup_logging() called from main.py
logger = logging.getLogger(__name__)

class ClanStorageBot(commands.Bot):
    def __init__(self):
        # Configure intents - only use what we need for slash commands
        intents = discord.Intents.default()
        # Note: message_content intent is privileged and not needed for slash commands
        # intents.message_content = True  # Disabled - requires privileged intent approval
        super().__init__(command_prefix='!', intents=intents)
        
        self.db = DatabaseManager()
        self.notifications = NotificationManager()
    
    async def setup_hook(self):
        """Initialize bot setup"""
        try:
            # Create logs directory
            import os
            os.makedirs('./logs', exist_ok=True)
            
            # Validate configuration
            Config.validate()
            
            # Start background tasks
            self.check_expiring_items.start()
            
            # Sync slash commands
            await self.tree.sync()
            logger.info(safe_log_message(
                "✅ Slash commands synced",
                "Slash commands synced"
            ))
            
        except Exception as e:
            logger.error(safe_log_message(
                f"❌ Setup failed: {e}",
                f"Error: Setup failed: {e}"
            ))
            raise
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(safe_log_message(
            f'🤖 Bot logged in as {self.user}',
            f'Bot logged in as {self.user}'
        ))
        
        sheets_status = "connected" if self.db.is_connected() else "disconnected"
        logger.info(safe_log_message(
            f'📊 Google Sheets connection: {"✅" if self.db.is_connected() else "❌"}',
            f'Google Sheets connection: {sheets_status}'
        ))
        
        # Send startup notification
        await self.notifications.send_startup_notification()
    
    @tasks.loop(hours=24)  # Check daily
    async def check_expiring_items(self):
        """Background task to check for expiring items"""
        try:
            expiring_items = self.db.get_expiring_items()
            if expiring_items:
                await self.notifications.send_expiring_items_alert(expiring_items)
                logger.info(f"📢 Sent notification for {len(expiring_items)} expiring items")
        except Exception as e:
            logger.error(f"❌ Failed to check expiring items: {e}")
    
    @check_expiring_items.before_loop
    async def before_check_expiring_items(self):
        """Wait until bot is ready before starting task"""
        await self.wait_until_ready()

# Initialize bot
bot = ClanStorageBot()

def is_authorized():
    """Decorator to check if user is authorized"""
    def predicate(interaction: discord.Interaction) -> bool:
        return str(interaction.user.id) in Config.AUTHORIZED_USERS
    return discord.app_commands.check(predicate)

@bot.tree.command(name="add_item", description="🎒 Tambah item baru ke storage clan")
@discord.app_commands.describe(
    nama_item="Nama item yang akan ditambahkan",
    tipe="Jenis item (UNIQUE/RED/CONSUMABLE)",
    participant="Nama karakter yang ikut boss time (pisahkan dengan koma jika lebih dari 1)",
    created_date="Tanggal dibuat (opsional, format: YYYY-MM-DD atau DD/MM/YYYY)"
)
@is_authorized()
async def add_item(interaction: discord.Interaction, nama_item: str, tipe: str, participant: str, created_date: str = None):
    """Add new item to clan storage"""
    await interaction.response.defer()
    
    try:
        # Validate item type
        if tipe.upper() not in Config.ITEM_TYPES:
            embed = discord.Embed(
                title="❌ Tipe Item Tidak Valid",
                description=f"Tipe harus salah satu dari: {', '.join(Config.ITEM_TYPES)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Parse created_date if provided
        custom_created_at = None
        if created_date:
            try:
                from utils import parse_date_input
                custom_created_at = parse_date_input(created_date)
                logger.info(f"Using custom created date: {custom_created_at}")
            except ValueError as e:
                embed = discord.Embed(
                    title="❌ Format Tanggal Tidak Valid",
                    description=f"Format tanggal salah: {e}\n\nContoh format yang benar:\n• `2024-01-15` (YYYY-MM-DD)\n• `15/01/2024` (DD/MM/YYYY)\n• `15-01-2024` (DD-MM-YYYY)",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
        
        # Add item to database
        success = bot.db.add_item(nama_item, tipe.upper(), participant, custom_created_at)
        
        if success:
            # Create success embed
            embed = discord.Embed(
                title="✅ Item Berhasil Ditambahkan",
                color=discord.Color.green(),
                timestamp=datetime.now(Config.TIMEZONE)
            )
            embed.add_field(name="📦 Nama Item", value=nama_item, inline=True)
            embed.add_field(name="🏷️ Tipe", value=tipe.upper(), inline=True)
            embed.add_field(name="👥 Participant", value=participant, inline=False)
            # Calculate and display expire date
            if custom_created_at:
                from utils import calculate_expire_date, format_datetime
                expire_date = calculate_expire_date(custom_created_at)
                expire_str = format_datetime(expire_date, 'date')
                created_str = format_datetime(custom_created_at, 'date')
                embed.add_field(name="📅 Dibuat", value=created_str, inline=True)
                embed.add_field(name="⏰ Expire", value=expire_str, inline=True)
            else:
                embed.add_field(name="⏰ Expire", value=f"30 hari dari sekarang", inline=True)
            embed.set_footer(text=f"Ditambahkan oleh {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed)
            logger.info(f"✅ Item added by {interaction.user}: {nama_item}")
            
        else:
            embed = discord.Embed(
                title="❌ Gagal Menambahkan Item",
                description="Terjadi kesalahan saat menyimpan item. Silakan coba lagi.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
    except Exception as e:
        logger.error(f"❌ Error in add_item command: {e}")
        embed = discord.Embed(
            title="❌ Terjadi Kesalahan",
            description="Maaf, terjadi kesalahan sistem. Silakan coba lagi nanti.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="list_items", description="📋 Lihat semua item di storage clan")
@is_authorized()
async def list_items(interaction: discord.Interaction):
    """List all items in clan storage"""
    await interaction.response.defer()
    
    try:
        items = bot.db.get_all_items()
        
        if not items:
            embed = discord.Embed(
                title="📭 Storage Kosong",
                description="Belum ada item yang tersimpan di storage clan.",
                color=discord.Color.orange()
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Create paginated embeds (10 items per page)
        items_per_page = 10
        total_pages = (len(items) + items_per_page - 1) // items_per_page
        
        for page in range(total_pages):
            start_idx = page * items_per_page
            end_idx = min((page + 1) * items_per_page, len(items))
            page_items = items[start_idx:end_idx]
            
            embed = discord.Embed(
                title=f"📋 Storage Clan - Halaman {page + 1}/{total_pages}",
                description=f"Total: {len(items)} item",
                color=discord.Color.blue(),
                timestamp=datetime.now(Config.TIMEZONE)
            )
            
            for item in page_items:
                expire_date = datetime.strptime(item['Expire'], '%Y-%m-%d %H:%M:%S')
                days_until_expire = (expire_date - datetime.now()).days
                
                status_emoji = "🟢" if days_until_expire > 7 else "🟡" if days_until_expire > 0 else "🔴"
                
                embed.add_field(
                    name=f"{status_emoji} {item['No']}. {item['Nama Item']} ({item['Type']})",
                    value=f"👥 {item['Participant']}\n⏰ Expire: {days_until_expire} hari lagi",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            
            # Add delay between pages to avoid rate limiting
            if page < total_pages - 1:
                await asyncio.sleep(1)
        
        logger.info(f"📋 Items listed by {interaction.user}")
        
    except Exception as e:
        logger.error(f"❌ Error in list_items command: {e}")
        embed = discord.Embed(
            title="❌ Terjadi Kesalahan",
            description="Maaf, terjadi kesalahan saat mengambil data. Silakan coba lagi nanti.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="check_expiring", description="⏰ Cek item yang akan expire")
@is_authorized()
async def check_expiring(interaction: discord.Interaction):
    """Check items that are about to expire"""
    await interaction.response.defer()
    
    try:
        expiring_items = bot.db.get_expiring_items()
        
        if not expiring_items:
            embed = discord.Embed(
                title="✅ Tidak Ada Item yang Akan Expire",
                description=f"Tidak ada item yang akan expire dalam {Config.NOTIFICATION_DAYS_BEFORE} hari ke depan.",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="⚠️ Item yang Akan Expire",
            description=f"Ada {len(expiring_items)} item yang akan expire:",
            color=discord.Color.orange(),
            timestamp=datetime.now(Config.TIMEZONE)
        )
        
        for item in expiring_items:
            days_until_expire = (item['expire_date'] - datetime.now(Config.TIMEZONE)).days
            
            if days_until_expire <= 0:
                status = "🔴 EXPIRED"
            elif days_until_expire <= 3:
                status = f"🔴 {days_until_expire} hari lagi"
            else:
                status = f"🟡 {days_until_expire} hari lagi"
            
            embed.add_field(
                name=f"{item['no']}. {item['nama_item']} ({item['type']})",
                value=f"👥 {item['participant']}\n⏰ {status}",
                inline=True
            )
        
        await interaction.followup.send(embed=embed)
        logger.info(f"⏰ Expiring items checked by {interaction.user}")
        
    except Exception as e:
        logger.error(f"❌ Error in check_expiring command: {e}")
        embed = discord.Embed(
            title="❌ Terjadi Kesalahan",
            description="Maaf, terjadi kesalahan saat mengecek item. Silakan coba lagi nanti.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="status", description="📊 Cek status bot dan koneksi")
@is_authorized()
async def status(interaction: discord.Interaction):
    """Check bot status and connections"""
    await interaction.response.defer()
    
    try:
        embed = discord.Embed(
            title="📊 Status Bot",
            color=discord.Color.blue(),
            timestamp=datetime.now(Config.TIMEZONE)
        )
        
        # Check Google Sheets connection
        sheets_status = "✅ Terhubung" if bot.db.is_connected() else "❌ Tidak terhubung"
        embed.add_field(name="📊 Google Sheets", value=sheets_status, inline=True)
        
        # Bot uptime
        uptime = datetime.now(Config.TIMEZONE) - bot.launch_time if hasattr(bot, 'launch_time') else "Unknown"
        embed.add_field(name="⏰ Uptime", value=str(uptime), inline=True)
        
        # Total items
        total_items = len(bot.db.get_all_items())
        embed.add_field(name="📦 Total Items", value=str(total_items), inline=True)
        
        # Expiring items
        expiring_count = len(bot.db.get_expiring_items())
        embed.add_field(name="⚠️ Items Akan Expire", value=str(expiring_count), inline=True)
        
        embed.set_footer(text=f"Dicek oleh {interaction.user.display_name}")
        
        await interaction.followup.send(embed=embed)
        logger.info(f"📊 Status checked by {interaction.user}")
        
    except Exception as e:
        logger.error(f"❌ Error in status command: {e}")
        embed = discord.Embed(
            title="❌ Terjadi Kesalahan",
            description="Maaf, terjadi kesalahan saat mengecek status. Silakan coba lagi nanti.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

# Error handlers
@add_item.error
@list_items.error
@check_expiring.error
@status.error
async def command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    """Handle command errors"""
    if isinstance(error, discord.app_commands.CheckFailure):
        embed = discord.Embed(
            title="🚫 Akses Ditolak",
            description="Anda tidak memiliki izin untuk menggunakan command ini.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        logger.error(f"❌ Command error: {error}")
        embed = discord.Embed(
            title="❌ Terjadi Kesalahan",
            description="Maaf, terjadi kesalahan sistem. Silakan coba lagi nanti.",
            color=discord.Color.red()
        )
        if not interaction.response.is_done():
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(embed=embed, ephemeral=True)

if __name__ == "__main__":
    try:
        bot.launch_time = datetime.now(Config.TIMEZONE)
        bot.run(Config.DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        raise