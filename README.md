# xinwen-nl-alexa

Dutch news → Chinese audio MP3 generator.

## What It Does

- Daily auto-scrape xinwen.nl Dutch news
- Convert to Chinese voice MP3 using TTS
- Upload to Google Drive

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Google Drive

Two authentication methods (choose one):

#### Option A: Service Account (default)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project → Enable Google Drive API
3. Create Service Account → Download JSON credentials
4. Rename to `credentials.json` in project root
5. Share target folder with Service Account email (editor permissions)

> Note: Service account has no storage quota, so target folder must be in a Shared Drive.

#### Option B: OAuth User Authorization

1. Enable Google Drive API in Cloud Console
2. Create OAuth 2.0 Client ID (Desktop app type)
3. Download `client_secrets.json` to project root
4. First run will open browser for login
5. Credentials saved to `~/.gdrive_token.pickle`

### 3. Run

```bash
python main.py
```

### 4. Set Up Cron Job

```bash
# Edit crontab
crontab -e

# Run daily at 8am
0 8 * * * /path/to/venv/bin/python /path/to/main.py >> /path/to/cron.log 2>&1
```

## Project Structure

```
xinwen-nl-alexa/
├── src/              # Source code
│   ├── scraper.py    # News scraper
│   ├── tts.py       # TTS synthesis
│   ├── gdrive.py    # Google Drive upload
│   └── main.py      # Main entry
├── api/              # Flask API (if needed)
├── config/           # Configuration files
├── output/           # Generated MP3 files
├── public/           # Static web files
├── .keys/            # API keys
└── requirements.txt
```

## Environment Variables

Create `.env.local` or set these:

```bash
# Google Drive Folder ID
FOLDER_ID=your_folder_id

# TTS Voice (optional)
VOICE_NAME=zh-CN-XiaoxiaoNeural
```

## Output

- MP3 files saved to: `output/`
- Also uploaded to Google Drive folder

## Troubleshooting

```bash
# Check logs
tail -f cron.log

# Test run manually
python main.py --debug

# Verify GDrive credentials
python -c "from src.gdrive import GDrive; print('OK')"
```
