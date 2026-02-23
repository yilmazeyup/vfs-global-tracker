# 🤖 VFS Global Randevu Takip Sistemi

**Enterprise-grade VFS Global appointment monitoring system with React frontend**

⚡ **Developed by Manaliza Enterprise Solutions**

![VFS Tracker](https://img.shields.io/badge/VFS-Tracker-blue?style=for-the-badge)
![React](https://img.shields.io/badge/React-18.2.0-61dafb?style=for-the-badge&logo=react)
![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=for-the-badge&logo=python)

## 🎯 Overview

Automated VFS Global appointment tracking system that monitors multiple countries and offices simultaneously, with instant Telegram notifications when appointments become available.

### 🌍 Supported Countries (11)

- 🇳🇱 Netherlands (Ankara & İstanbul)
- 🇩🇪 Germany (Ankara, İstanbul, İzmir)
- 🇮🇹 Italy (Ankara & İstanbul)
- 🇳🇴 Norway (Ankara)
- 🇨🇦 Canada (Ankara & İstanbul)
- 🇭🇺 Hungary (Ankara)
- 🇩🇰 Denmark (Ankara & İstanbul)
- 🇱🇹 Lithuania (Ankara)
- 🇸🇪 Sweden (Ankara & İstanbul)
- 🇫🇮 Finland (Ankara)
- 🇵🇱 Poland (Ankara & İstanbul)

## 🚀 Features

### Core Features
- ✅ **Multi-Country Support**: 11 countries with multiple office locations
- ✅ **Anti-Detection**: Advanced bot protection bypass with undetected-chromedriver
- ✅ **Real-time Monitoring**: Continuous appointment scanning
- ✅ **Instant Notifications**: Telegram alerts with screenshots
- ✅ **Session Management**: Persistent login sessions
- ✅ **Smart Retry Engine**: Automatic error recovery
- ✅ **React Dashboard**: Modern web interface

### Technical Features
- 🔐 **Secure Credential Storage**: Encrypted environment variables
- 📊 **Performance Monitoring**: Real-time stats and analytics
- 🌙 **Dark Mode Support**: Eye-friendly interface
- 📱 **Responsive Design**: Works on all devices
- 🔄 **Auto-refresh**: Live status updates
- 📸 **Screenshot Capture**: Visual appointment confirmations

## 📁 Project Structure

```
vfs_global_randevu_sistemi/
├── backend/                    # Python backend
│   ├── core/                   # Core modules
│   │   ├── authentication.py   # Session management
│   │   ├── scraper.py         # VFS scanning engine
│   │   ├── retry_engine.py    # Error handling
│   │   └── telegram_bot.py    # Notification system
│   ├── config/                # Configuration
│   ├── utils/                 # Utilities
│   └── main.py               # Entry point
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   │   ├── Dashboard.js  # Main dashboard
│   │   │   ├── Settings.js   # Configuration UI
│   │   │   ├── Sidebar.js    # Navigation
│   │   │   └── Header.js     # Top bar
│   │   └── App.js           # Main app
│   └── public/
├── config/                   # Shared configuration
├── docs/                     # Documentation
└── tests/                    # Test suites
```

## 🛠️ Installation

### Prerequisites
- Python 3.11+
- Node.js 16+
- Chrome/Chromium browser
- Git

### Backend Setup

```bash
# Clone repository
git clone https://github.com/yilmazeyup/vfs-global-tracker.git
cd vfs-global-tracker

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp config/secrets.env.example config/secrets.env
# Edit secrets.env with your credentials
```

### Frontend Setup

```bash
# Frontend setup
cd ../frontend
npm install

# Development server
npm start
```

### Environment Configuration

Create `config/secrets.env`:

```env
# VFS Credentials
VFS_EMAIL=your_email@example.com
VFS_PASSWORD=your_password

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Browser Settings
HEADLESS_MODE=False
CHROME_DRIVER_PATH=/usr/bin/chromedriver

# Timing
CHECK_INTERVAL=300
MIN_DELAY=30
MAX_DELAY=120
```

## 🚀 Usage

### Command Line

```bash
# Start monitoring Netherlands (Ankara office)
python main.py --country netherlands --office ankara

# Monitor multiple offices
python main.py --country netherlands --office ankara,istanbul

# Run in headless mode
python main.py --country germany --headless
```

### Web Dashboard

1. Start the backend: `python main.py --web`
2. Start the frontend: `cd frontend && npm start`
3. Open browser: http://localhost:3000

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f
```

## 📱 Telegram Bot Setup

1. Create bot with [@BotFather](https://t.me/botfather)
2. Get your bot token
3. Start conversation with bot
4. Get your chat ID: https://api.telegram.org/bot<TOKEN>/getUpdates
5. Add credentials to `secrets.env`

## 🔧 Advanced Configuration

### Anti-Detection Features
- Randomized user agents
- Natural mouse movements
- Random delays between actions
- Session fingerprint rotation
- Proxy support

### Performance Tuning
```python
# Adjust in config/settings.py
PARALLEL_OFFICES = 2  # Simultaneous office checks
MAX_RETRIES = 3      # Retry attempts
TIMEOUT = 30         # Page load timeout
```

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | System status |
| `/api/start` | POST | Start monitoring |
| `/api/stop` | POST | Stop monitoring |
| `/api/stats` | GET | Statistics |
| `/api/config` | GET/POST | Configuration |

## 🐛 Troubleshooting

### Common Issues

**Bot Detection:**
- Enable anti-detection features
- Increase random delays
- Use residential proxies

**Login Failures:**
- Check VFS credentials
- Clear browser cache
- Update chromedriver

**No Appointments Found:**
- Verify office selection
- Check VFS website manually
- Adjust scan intervals

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push branch: `git push origin feature-name`
5. Submit pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file

## 🙏 Acknowledgments

- VFS Global for appointment services
- Selenium community
- undetected-chromedriver developers

---

**⚡ Manaliza Enterprise Solutions**  
*Building tomorrow's automation today*

**Support:** support@manaliza.com  
**Website:** https://manaliza.com