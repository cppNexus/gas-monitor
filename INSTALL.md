# Installation Guide

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Creating a Telegram Bot](#creating-a-telegram-bot)
3. [Local Installation](#local-installation)
4. [Docker Installation](#docker-installation)
5. [RPC Endpoints Configuration](#rpc-endpoints-configuration)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum
- Python 3.9 or higher
- 512 MB RAM
- 1 GB free disk space
- Stable internet connection

### Recommended
- Python 3.11
- 1 GB RAM
- 5 GB free disk space (for history and charts)
- VPS/Dedicated server for 24/7 operation

---

## Creating a Telegram Bot

### Step 1: Create the Bot

1. Open Telegram and find [@BotFather](https://t.me/BotFather)
2. Send the command `/newbot`
3. Choose a name for your bot (e.g., "Gas Monitor Bot")
4. Choose a username (e.g., "my_gas_monitor_bot")
5. Save the token provided by BotFather

Example token: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

### Step 2: Get Your Chat ID

**Method 1 (simple):**
1. Find [@userinfobot](https://t.me/userinfobot)
2. Send `/start`
3. Copy your ID (e.g., `123456789`)

**Method 2 (for groups):**
1. Add your bot to a group
2. Open https://api.telegram.org/bot`YOUR_BOT_TOKEN`/getUpdates
3. Find `"chat":{"id":-123456789}` in the response
4. Use this value as chat_id

### Step 3: Test the Bot

```bash
# Replace YOUR_BOT_TOKEN and YOUR_CHAT_ID
curl "https://api.telegram.org/botYOUR_BOT_TOKEN/sendMessage?chat_id=YOUR_CHAT_ID&text=Test"
```

If everything is configured correctly, you will receive a test message.

---

## Local Installation

### macOS / Linux

```bash
# 1. Clone the repository
git clone https://github.com/cppNexus/gas-monitor.git
cd gas-monitor

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate environment
source venv/bin/activate

# 4. Upgrade pip
pip install --upgrade pip

# 5. Install dependencies
pip install -r requirements.txt

# 6. Create .env file
cp .env.example .env

# 7. Edit .env
nano .env
# or
vim .env
# or use any text editor

# 8. Create necessary directories
mkdir -p logs charts data

# 9. Test configuration
python config.py

# 10. Start monitoring
python main.py
```

### Windows

```powershell
# 1. Clone the repository
git clone https://github.com/cppNexus/gas-monitor.git
cd gas-monitor

# 2. Create virtual environment
python -m venv venv

# 3. Activate environment
venv\Scripts\activate

# 4. Upgrade pip
python -m pip install --upgrade pip

# 5. Install dependencies
pip install -r requirements.txt

# 6. Create .env file
copy .env.example .env

# 7. Edit .env in Notepad
notepad .env

# 8. Create directories
mkdir logs charts data

# 9. Test configuration
python config.py

# 10. Start monitoring
python main.py
```

---

## Docker Installation

### Prerequisites

```bash
# Check Docker installation
docker --version
docker-compose --version
```

If Docker is not installed:
- **Linux**: https://docs.docker.com/engine/install/
- **macOS**: https://docs.docker.com/desktop/install/mac-install/
- **Windows**: https://docs.docker.com/desktop/install/windows-install/

### Installation and Setup

```bash
# 1. Clone the repository
git clone https://github.com/cppNexus/gas-monitor.git
cd gas-monitor

# 2. Create .env file
cp .env.example .env

# 3. Edit .env
nano .env

# 4. Build and start
docker-compose up -d

# 5. Check logs
docker-compose logs -f

# 6. Stop
docker-compose down

# 7. Restart
docker-compose restart
```

### Useful Docker Commands

```bash
# Real-time logs
docker-compose logs -f gas-monitor

# Last 100 log lines
docker-compose logs --tail=100 gas-monitor

# Enter container
docker-compose exec gas-monitor sh

# Restart after .env changes
docker-compose down
docker-compose up -d

# Full cleanup and rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## RPC Endpoints Configuration

### Free Public RPCs

The project uses public RPCs by default:

- **Ethereum**: Ankr, LlamaRPC
- **Arbitrum**: Ankr, LlamaRPC
- **Optimism**: Ankr, LlamaRPC
- **Base**: Ankr, LlamaRPC
- **Polygon**: Ankr, LlamaRPC

### Recommended Paid RPCs (better reliability)

1. **Alchemy** (https://www.alchemy.com/)
   - Free tier: 300M compute units/month
   - Excellent documentation

2. **Infura** (https://infura.io/)
   - Free tier: 100K requests/day
   - Simple registration

3. **QuickNode** (https://www.quicknode.com/)
   - Free trial
   - High speed

### Configure Your RPCs in .env

```env
# Ethereum
ETHEREUM_RPC_1=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
ETHEREUM_RPC_2=https://mainnet.infura.io/v3/YOUR_KEY

# Arbitrum
ARBITRUM_RPC_1=https://arb-mainnet.g.alchemy.com/v2/YOUR_KEY

# Optimism  
OPTIMISM_RPC_1=https://opt-mainnet.g.alchemy.com/v2/YOUR_KEY

# Base
BASE_RPC_1=https://base-mainnet.g.alchemy.com/v2/YOUR_KEY

# Polygon
POLYGON_RPC_1=https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY
```

---

## Verification

### 1. Test Configuration

```bash
python config.py
```

You should see:
```
Configuration loaded successfully
======================================================================
GAS MONITOR - CONFIGURATION
======================================================================
Networks (5): ethereum, arbitrum, optimism, base, polygon
Telegram: Configured
...
```

### 2. Test Run

```bash
python main.py
```

Within 30-60 seconds you should see:
- Network connections
- Gas data retrieval
- Log entries

### 3. Check Telegram Alerts

Wait until gas prices drop below thresholds, or temporarily increase thresholds for testing:

```env
# In config.py temporarily change for testing:
gas_thresholds={
    "low": 1000,  # High value for testing
    ...
}
```

### 4. Check Charts

After the first hour of operation, check the `charts/` folder:

```bash
ls -lh charts/
```

You should see `.png` files with charts.

---

## Troubleshooting

### Issue: `ModuleNotFoundError`

**Solution:**
```bash
# Ensure virtual environment is active
which python  # should show path in venv/

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Issue: Telegram Bot Not Responding

**Checks:**
1. Verify token and chat ID
2. Bot is not blocked
3. For groups: bot added as administrator

**Test:**
```bash
curl "https://api.telegram.org/bot<TOKEN>/getMe"
```

### Issue: RPC Errors

**Symptoms:**
```
WARNING - HTTP 429 (ethereum), attempt 1
ERROR - RPC error (ethereum): ...
```

**Solution:**
1. Use paid RPC endpoints
2. Increase `CHECK_INTERVAL` in `.env`
3. Add more RPC endpoints

### Issue: High Memory Usage

**Solution:**
```env
# Reduce history
MAX_HISTORY_HOURS=12

# Disable charts
ENABLE_CHARTS=false

# Increase interval
CHECK_INTERVAL=30
```

### Issue: Docker Container Crashes

**Check:**
```bash
# Logs
docker-compose logs gas-monitor

# Status
docker-compose ps

# Restart
docker-compose restart
```

### Issue: Charts Not Generating

**Check:**
```bash
# Verify matplotlib
python -c "import matplotlib; print(matplotlib.__version__)"

# Folder permissions
ls -ld charts/
chmod 755 charts/

# Logs
grep -i "chart" logs/gas_monitor.log
```

---

## Running as a Service (Linux)

### systemd service

Create `/etc/systemd/system/gas-monitor.service`:

```ini
[Unit]
Description=Gas Monitor Service
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/path/to/gas-monitor
Environment="PATH=/path/to/gas-monitor/venv/bin"
ExecStart=/path/to/gas-monitor/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Activate:
```bash
sudo systemctl daemon-reload
sudo systemctl enable gas-monitor
sudo systemctl start gas-monitor
sudo systemctl status gas-monitor
```

---

## Monitoring

### Logs

```bash
# Real-time
tail -f logs/gas_monitor.log

# Search errors
grep ERROR logs/gas_monitor.log

# Statistics
grep "Success:" logs/gas_monitor.log | tail -20
```

### Metrics

```bash
# History size
du -sh data/

# Chart count
ls -1 charts/*.png | wc -l

# Memory usage (if running)
ps aux | grep python
```

---

## Next Steps

1. Star the repository on GitHub
2. Create an issue if you find a bug
3. Contribute if you have ideas
4. Share the project

---

**Need help?** Create an issue on GitHub: https://github.com/cppNexus/gas-monitor/issues