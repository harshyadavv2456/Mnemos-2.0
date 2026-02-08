# MNEMOS 2.1 – Deployment Guide (Google Colab)

Deploy on free Google Colab so the system runs in the cloud with no local machine.

## Step-by-step

### 1. Get your project into Colab

**Option A – Upload zip**

1. On your PC, zip the project: e.g. `mnemos2.0` folder → `mnemos2.0.zip`.
2. In Colab: File → Upload to session storage (or drag the zip into the file panel).
3. In a cell run:
   ```python
   !unzip -o mnemos2.0.zip -d /content
   ```
4. In the env cell set: `MNEMOS_ROOT = Path('/content/mnemos2.0')`.

**Option B – Clone from GitHub**

1. Upload the repo to GitHub (private or public).
2. In Colab:
   ```python
   !git clone https://github.com/YOUR_USER/mnemos2.0.git /content/mnemos2.0
   ```
3. Set `MNEMOS_ROOT = Path('/content/mnemos2.0')`.

**Option C – Manual upload of folder**

1. Upload the `mnemos2.0` folder into Colab (e.g. under `/content/`).
2. Set `MNEMOS_ROOT` to that path.

### 2. Get Telegram credentials

1. Open Telegram, search **@BotFather**. Send `/newbot`, follow prompts, copy the **bot token**.
2. Search **@userinfobot**, send any message, copy your **chat ID** (numeric).

### 3. Get Gmail app password

1. Google Account → Security → 2-Step Verification (enable if needed).
2. Security → App passwords → Generate for “Mail” / “Other”. Copy the 16-character password.
3. Use this in `GMAIL_APP_PASSWORD`, not your normal Gmail password.

### 4. Set secrets in Colab

In the **“Upload / clone MNEMOS and set environment”** cell, either:

- **Paste directly** (session only; lost when runtime ends):
  ```python
  os.environ['TELEGRAM_BOT_TOKEN'] = '123456:ABC-...'
  os.environ['TELEGRAM_CHAT_ID']   = '987654321'
  os.environ['GMAIL_USER']         = 'you@gmail.com'
  os.environ['GMAIL_APP_PASSWORD'] = 'abcd efgh ijkl mnop'
  os.environ['ALERT_EMAIL_TO']     = 'you@gmail.com'
  ```
- Or use **Colab Secrets**: Left sidebar → Key icon → add `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `ALERT_EMAIL_TO`. The notebook already reads them with `os.environ.get('...', '')`.

### 5. Run the notebook

1. **Runtime → Run all** (or run cells one by one).
2. When “Mount Google Drive” runs, approve access if you want DB backups on Drive.
3. The last cell starts the engine. You’ll see heartbeat lines; alerts go to Telegram and email.

### 6. One-click startup

After the first run you can:

- **Runtime → Run before** (to run everything before the last cell), then run only the last cell to start MNEMOS.
- Or use **Runtime → Run all** each time you open the notebook.

### 7. Persistence and disconnects

- **Session storage**: Colab disk is cleared when the runtime is recycled. Export DB from `data/mnemos.db` if you need it (e.g. download or copy to Drive).
- **Drive backup**: With Drive mounted and `set_drive_mount(Path('/content/drive/MyDrive'))`, the app backs up the DB to a folder (default `mnemos_backups`) every N ticks.
- **Auto-restart**: Colab does not auto-restart after disconnect. You need to open the notebook again and **Run all** (or run the last cell). For “auto-resume” you can use external schedulers (e.g. cron on a free-tier VM) to hit a Colab URL that re-runs the notebook, or run MNEMOS locally when you’re at the PC.

### 8. Keepalive (reduce disconnects)

- Keep the Colab tab active.
- Optional: add a new cell with:
  ```javascript
  %%javascript
  document.querySelector('.colab-connect-button')?.click();
  ```
  Run this cell every ~60 minutes to try to keep the session connected.
- Some users use a browser extension to refresh the tab periodically (use with care to avoid rate limits).

## Checklist

- [ ] Project available at `MNEMOS_ROOT` in Colab
- [ ] Dependencies installed (first cell)
- [ ] Telegram token and chat ID set
- [ ] Gmail user and app password set; `ALERT_EMAIL_TO` set
- [ ] Drive mounted if you want backups
- [ ] “Run MNEMOS forever” cell running; heartbeats visible

## Where your input is necessary

You **must** provide:

- **TELEGRAM_BOT_TOKEN** and **TELEGRAM_CHAT_ID** if you want Telegram alerts.
- **GMAIL_USER**, **GMAIL_APP_PASSWORD**, **ALERT_EMAIL_TO** if you want email alerts.

Watchlist, intervals, and thresholds have defaults; override in the env cell or via `.env` if you upload one.
