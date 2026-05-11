# Boat Lift VFX Tracker Bot

Monitors a Google Sheet for VFX shot status changes and sends notification emails to the relevant recipients. Designed to run as a cron job.

## How It Works

On each run the app fetches the current sheet data and compares it against a local snapshot (`state.json`) from the previous run. When a row's STATUS column changes, an email is sent based on who should be notified for that status:

| STATUS | Recipients |
|---|---|
| `ACTIVE` | The assigned artist (looked up by name) |
| `FINAL` | The assigned artist (looked up by name) |
| `REVIEW` | Fixed recipient list |
| `DELIVERED` | Fixed recipient list |
| `_` or empty | No notification |

## Setup

### 1. Install dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Google Service Account

Create a service account in [Google Cloud Console](https://console.cloud.google.com):
- Enable the **Google Sheets API**
- Create a service account and download its JSON key as `credentials.json`
- Share your Google Sheet with the service account email (Viewer access)

### 3. Gmail App Password

To send email via Gmail SMTP:
- Enable 2-step verification on the sender Gmail account
- Go to **Google Account → Security → App Passwords** and generate a password
- Store it in `.env` as `GMAIL_APP_PASSWORD`

### 4. Configure `.env`

Set secret environment values into a `.env` file in the project root:

### 5. Configure `config.yaml`

Key settings to verify:

```yaml
google:
  sheet_name: "VFX SHOTS"   # exact tab name
  header_row: 2             # 1-indexed row containing column headers
  monitored_columns:
    - STATUS
  artist_statuses:
    - ACTIVE
    - FINAL
```

### 6. Run

```bash
venv/bin/python main.py
```

The first run saves a baseline snapshot and sends no emails. Subsequent runs only send emails for rows where STATUS changed.

## Cron Setup

To run every 2 minutes, add to crontab (`crontab -e`):

```
*/2 * * * * cd /path/to/boat-lift-tracker-bot && venv/bin/python main.py >> /tmp/boat-lift.log 2>&1
```

Start the cron service if not running:

```bash
sudo systemctl start crond
sudo systemctl enable crond
```

## Adding a New Artist

1. Add to `config.yaml` under `artist_emails`:
   ```yaml
   _NewArtist: "${ARTIST_NEWARTIST_EMAIL}"
   ```
2. Add to `.env`:
   ```
   ARTIST_NEWARTIST_EMAIL=newartist@example.com
   ```

## File Reference

| File | Purpose |
|---|---|
| `main.py` | Entry point — orchestrates fetch, diff, email, save |
| `sheets.py` | Google Sheets API (read-only) |
| `state_manager.py` | Load/save/diff `state.json` |
| `email_builder.py` | Builds email subject and HTML body |
| `mailer.py` | Gmail SMTP connection and send |
| `config.yaml` | All non-secret configuration |
| `.env` | Secrets and email addresses (not committed) |
| `credentials.json` | Google service account key (not committed) |
| `state.json` | Auto-generated run snapshot (not committed) |
