# Colab deployment – step-by-step (secure, 24/7)

## How 24/7 automated works

1. You open the notebook and **Run all** cells.
2. The **last cell** runs `run_forever()`: a loop that every **2 min** (market hours) or 30 min (off hours):
   - Fetches NSE + indices + Gold/Silver data
   - Computes friction and confidence
   - Sends alerts to Telegram and Email (and GROQ analysis when enabled)
   - Logs heartbeats, backs up DB to Drive
3. That loop runs **continuously** until you click **Runtime → Interrupt execution** or until Colab disconnects (free tier often ~90 min idle).
4. **When Colab disconnects:** The loop stops. To run 24/7 again: re-open the same notebook link and click **Runtime → Run all**. No code changes needed.
5. **Keepalive:** Keep the browser tab active, or add a cell with `%%javascript` and run it every ~60 min: `document.querySelector('.colab-connect-button')?.click();`

---

## Add secrets (required – all secure, never in the repo)

You must set these **once per Colab session** (or use Colab Secrets so they persist for the session). No secrets are stored in the GitHub repo.

### Option A – Colab Secrets (recommended)

1. In Colab, click the **key icon** in the **left sidebar** (Secrets).
2. Click **Add new secret** for each of the following. Use the **exact** name; value is your real secret.
3. **Important:** For each secret, turn **ON** the **"Notebook access"** toggle so this notebook can read it (Colab does not inject secrets into the environment automatically; the notebook reads them via `userdata.get()`).

| Secret name | Example / where to get it |
|-------------|---------------------------|
| `TELEGRAM_BOT_TOKEN` | From @BotFather on Telegram (e.g. `123456:ABC-...`) |
| `TELEGRAM_CHAT_ID` | From @userinfobot on Telegram – send any message, copy your numeric Id (e.g. `7997663618`) |
| `GMAIL_USER` | Your Gmail address (e.g. `you@gmail.com`) |
| `GMAIL_APP_PASSWORD` | Google Account → Security → 2-Step Verification → App passwords → generate for “Mail” – 16 characters, **not** your normal password |
| `ALERT_EMAIL_TO` | Same as GMAIL_USER, or comma-separated for mail trail: `a@gmail.com,b@gmail.com` |
| `GROQ_API_KEY` | From console.groq.com (free tier key) |

3. The notebook code reads these automatically. Do **not** paste secrets in the notebook when using Secrets.

### Option B – Paste in the env cell

1. In the notebook, find the cell **“## 2. Set project path and secrets”**.
2. The code already has `os.environ.setdefault('TELEGRAM_BOT_TOKEN', os.environ.get('TELEGRAM_BOT_TOKEN', ''))` etc. Colab Secrets override the empty string. If you **don’t** use Secrets, you can set variables explicitly **before** that block, for example:

   ```python
   os.environ['TELEGRAM_BOT_TOKEN'] = 'your_bot_token_here'
   os.environ['TELEGRAM_CHAT_ID']   = '7997663618'
   os.environ['GMAIL_USER']         = 'your_email@gmail.com'
   os.environ['GMAIL_APP_PASSWORD'] = 'your_16_char_app_password'
   os.environ['ALERT_EMAIL_TO']     = 'you@gmail.com,other@gmail.com'
   os.environ['GROQ_API_KEY']       = 'your_groq_key'
   ```

3. **Do not** commit or share the notebook after pasting real values. Prefer Colab Secrets.

---

## Security (Telegram, Gmail, APIs)

- **Repo:** No tokens or passwords are in the GitHub repo. `.env` is gitignored; the notebook only has placeholders or reads from Colab Secrets.
- **Colab:** Secrets are stored in Colab’s secret store (tied to your Google account) and injected into the runtime. Don’t share your Colab notebook if you pasted secrets in the cell.
- **Telegram:** Use a bot token from @BotFather and your chat ID from @userinfobot. Don’t share the token.
- **Gmail:** Use an **App Password**, not your main password. You can revoke it anytime in Google Account → Security → App passwords.
- **GROQ:** Use a key from console.groq.com; free tier has rate limits. Rotate the key if it’s ever exposed.

---

## Open in Colab

1. Open: **https://colab.research.google.com/github/harshyadavv2456/Mnemos-2.0/blob/main/colab_setup.ipynb**
2. Add secrets (Colab Secrets or paste in Section 2 cell).
3. **Runtime → Run all.** The last cell runs MNEMOS 24/7.

If the link fails, use **Method 2** in the same doc (clone the repo in Colab, then open `colab_setup.ipynb` from the cloned folder).
