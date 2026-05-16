# 🚀 Divi Version Monitor

This bot continuously monitors the official DIVI update and changelog sources 24/7. Whenever a new DIVI version, feature update, bug fix, security patch, or changelog is released, the bot instantly sends an automatic alert notification to our connected platforms such as Slack and Telegram. This helps us stay updated in real time without manually checking the website repeatedly. The system is designed to be lightweight, automated, reliable, and fast, ensuring we never miss any important DIVI updates or announcements.

Automated RSS monitoring system that sends Telegram notifications when new Divi WordPress theme versions are released.

## Features

✅ Monitors Divi changelog RSS feed every 30 minutes
✅ Sends Telegram notifications on new releases
✅ Optional Slack notifications
✅ Automated GitHub Actions workflow
✅ Secure environment variable handling

## Setup Instructions

### 1. Local Testing Setup

**Clone the repository:**
```bash
git clone https://github.com/MHMITHUN/Divi-New-Version-Monitor.git
cd Divi-New-Version-Monitor
```

**Create virtual environment:**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

**Copy `.env` template:**
```bash
cp .env.example .env
```

**Edit `.env` with your credentials:**
```
TG_TOKEN=your_telegram_bot_token
TG_CHAT=your_telegram_chat_id
SLACK_WEBHOOK=your_slack_webhook_url_optional
```

### 3. Get Your Telegram Credentials

1. **Create a Telegram Bot:**
   - Chat with `@BotFather` on Telegram
   - Create a new bot: `/newbot`
   - Copy the **API Token** → `TG_TOKEN`

2. **Get Chat ID:**
   - Send a message to your bot
   - Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   - Find your `chat.id` → `TG_CHAT`

### 4. Test Locally

```bash
python check.py
```

Expected output:
```
✅ New Update Found
Latest: Version 5.5.1
Old: Version 5.4.1
✅ Telegram Sent
```

### 5. GitHub Actions Setup

**Add repository secrets:**

Go to: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

Add these secrets:
- `TG_TOKEN` - Your Telegram bot token
- `TG_CHAT` - Your Telegram chat ID
- `SLACK_WEBHOOK` - (Optional) Your Slack webhook URL

The workflow will automatically run every 30 minutes.

## File Structure

```
Divi-New-Version-Monitor/
├── .github/
│   └── workflows/
│       └── main.yml          # GitHub Actions workflow
├── .env                      # Local environment variables (ignored)
├── .gitignore               # Git ignore rules
├── check.py                 # Main monitoring script
├── latest.txt               # Latest version tracker
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TG_TOKEN` | Telegram Bot API Token | Yes |
| `TG_CHAT` | Telegram Chat ID | Yes |
| `SLACK_WEBHOOK` | Slack Webhook URL | No |
| `RSS_URL` | RSS Feed URL | No (default provided) |

## How It Works

1. **Fetch RSS Feed** → Gets latest Divi version from official changelog
2. **Compare Version** → Checks against stored version in `latest.txt`
3. **Send Notification** → If new version found, sends Telegram alert
4. **Update Tracker** → Saves new version to `latest.txt`
5. **Git Commit** → Automatically commits changes to GitHub

## Troubleshooting

### "ModuleNotFoundError: No module named 'dotenv'"
```bash
pip install python-dotenv
```

### Telegram notification not sending
- Verify `TG_TOKEN` and `TG_CHAT` in `.env`
- Check token hasn't expired at `@BotFather`
- Ensure bot has permission to send messages

### Workflow failing in GitHub Actions
- Verify secrets are added correctly in repository settings
- Check `Actions` tab for error logs
- Ensure `RSS_URL` is accessible

## Security Notes

⚠️ **Never commit `.env` file** - It's in `.gitignore`
⚠️ **Never share your bot token** - Keep it secret!
⚠️ **Use GitHub Secrets for production** - Not local `.env`

## License

MIT License - Feel free to use and modify

## Support

For issues or questions, open a GitHub issue on the repository.