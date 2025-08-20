# 🎮 Discord Clan Storage Bot

Bot Discord ringan untuk mengelola storage item clan game dengan notifikasi otomatis untuk item yang akan expire.

## ✨ Fitur

- ✅ **Slash Commands** - Interface yang mudah digunakan
- 📊 **Google Sheets Integration** - Sinkronisasi data real-time
- 🔒 **Permission System** - Hanya user terotorisasi yang bisa mengakses
- ⏰ **Auto Notifications** - Peringatan 7 hari sebelum expire
- 🛡️ **Backup System** - Local SQLite backup jika Sheets offline
- 🌐 **Multi-language** - Support Bahasa Indonesia
- 🪶 **Lightweight** - Resource usage minimal
- 🐳 **Docker Ready** - Easy deployment

## 🚀 Quick Start

### 1. Persiapan Bot Discord

1. Buat aplikasi di [Discord Developer Portal](https://discord.com/developers/applications)
2. Buat bot dan copy token
3. Invite bot ke server dengan permissions:
   - `applications.commands` (slash commands)
   - `Send Messages`
   - `Use Slash Commands`

### 2. Setup Google Sheets

1. Buka [Google Cloud Console](https://console.cloud.google.com)
2. Buat project baru atau pilih yang sudah ada
3. Enable Google Sheets API
4. Buat Service Account:
   - IAM & Admin > Service Accounts
   - Create Service Account
   - Download JSON key → simpan sebagai `credentials/google_service_account.json`
5. Share Google Sheet dengan email service account
6. Copy Sheet ID dari URL

### 3. Installation

#### Manual Installation
```bash
# Clone repository
git clone <repository-url>
cd discord-clan-bot

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env dengan konfigurasi Anda

# Jalankan bot
python main.py
```

#### Docker Installation
```bash
# Copy environment file
cp .env.example .env
# Edit .env dengan konfigurasi Anda

# Jalankan dengan Docker Compose
docker-compose up -d
```

## 🔧 Konfigurasi

Edit file `.env`:

```env
# Discord Bot Token
DISCORD_TOKEN=your_discord_bot_token_here

# Discord Webhook URL (sudah disediakan)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/1407224359231426560/oS1htouI5MlFXg2TGZY-pF8RM_ScT3AEyc1t8O0aJ8zrlVrJf_9JdKe15glGA_rTVDNR

# Google Sheets Configuration
GOOGLE_SHEETS_ID=1fJxa8j66yuXiRYnWLbwfEJu4Tplb76Riu-F7y3PVcr4

# User IDs yang diizinkan menggunakan bot (pisahkan dengan koma)
AUTHORIZED_USERS=123456789012345678,987654321098765432

# Timezone
TIMEZONE=Asia/Jakarta

# Notifikasi berapa hari sebelum expire
NOTIFICATION_DAYS_BEFORE=7
```

## 📋 Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `/add_item` | Tambah item baru | `/add_item nama_item:Sword tipe:UNIQUE participant:Player1,Player2` |
| `/list_items` | Lihat semua item | `/list_items` |
| `/check_expiring` | Cek item yang akan expire | `/check_expiring` |
| `/status` | Status bot dan koneksi | `/status` |

### Parameter Types
- **tipe**: `UNIQUE`, `RED`, `CONSUMABLE`
- **participant**: Nama karakter (pisahkan dengan koma untuk multiple)

## 📊 Data Structure

| Column | Description | Example |
|--------|-------------|---------|
| No | Nomor urut | 1, 2, 3... |
| Nama Item | Nama item | \"Dragon Sword\" |
| Type | Jenis item | UNIQUE/RED/CONSUMABLE |
| Participant | Player yang ikut | \"Player1, Player2\" |
| CreatedAt | Tanggal dibuat | 2024-01-15 14:30:00 |
| UpdateAt | Tanggal update | 2024-01-15 14:30:00 |
| Expire | Tanggal expire | 2024-02-15 14:30:00 |

## 🔔 Notifikasi

Bot akan otomatis:
- ✅ Kirim notifikasi saat startup
- ⚠️ Kirim peringatan 7 hari sebelum item expire
- 🚨 Tag `@here` untuk item yang critical
- 📊 Kirim summary harian jika ada item expire

## 🛠️ Development

### Project Structure
```
discord-clan-bot/
├── bot.py              # Bot utama dan slash commands
├── database.py         # Google Sheets & SQLite integration  
├── notifications.py    # Webhook notifications
├── config.py          # Konfigurasi
├── utils.py           # Utility functions
├── main.py            # Entry point
├── requirements.txt   # Dependencies
├── Dockerfile         # Docker configuration
├── docker-compose.yml # Docker Compose
└── credentials/       # Google service account
    └── google_service_account.json
```

### Features Implemented

#### ✅ Core Features
- [x] Discord slash commands
- [x] Google Sheets integration
- [x] Permission system
- [x] Automated notifications
- [x] Local backup system
- [x] Error handling & logging
- [x] Docker deployment

#### 🔧 Enhanced Features  
- [x] Rich Discord embeds
- [x] Multi-language support (ID)
- [x] Rate limiting
- [x] Cache system
- [x] Health checks
- [x] Graceful shutdown
- [x] Timezone support

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

## 🚀 Deployment

### Production Deployment

1. **VPS/Server dengan Docker**:
```bash
# Clone dan setup
git clone <repo>
cd discord-clan-bot
cp .env.example .env

# Edit konfigurasi
nano .env

# Deploy
docker-compose up -d

# Monitor logs
docker-compose logs -f discord-bot
```

2. **Heroku/Railway**:
   - Fork repository
   - Connect ke platform
   - Set environment variables
   - Deploy

3. **Systemd Service** (Linux):
```bash
# Copy service file
sudo cp discord-bot.service /etc/systemd/system/

# Enable dan start
sudo systemctl enable discord-bot
sudo systemctl start discord-bot
```

## 📈 Monitoring

### Health Checks
```bash
# Docker health check
docker-compose ps

# Manual health check
curl http://localhost:8080/health
```

### Logs
```bash
# Docker logs
docker-compose logs -f discord-bot

# Manual logs
tail -f logs/bot.log
```

## 🔒 Security

- ✅ Permission-based access control
- ✅ User ID validation
- ✅ Rate limiting
- ✅ Input sanitization
- ✅ Non-root Docker user
- ✅ Environment variables for secrets

## 🐛 Troubleshooting

### Common Issues

1. **Bot tidak response**:
   - Check token Discord
   - Verify bot permissions
   - Check logs untuk error

2. **Google Sheets error**:
   - Verify service account JSON
   - Check sheet sharing permissions
   - Validate sheet ID

3. **Webhook tidak kirim**:
   - Test webhook URL manual
   - Check network connectivity
   - Verify webhook permissions

4. **Permission denied**:
   - Check `AUTHORIZED_USERS` di .env
   - Verify user ID format
   - Check Discord user ID

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py
```

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Credits

- Discord.py untuk bot framework
- gspread untuk Google Sheets integration
- aiohttp untuk async HTTP requests

---

💡 **Tips**: Untuk performa optimal, jalankan bot di server dengan koneksi internet stabil dan minimal Python 3.8+