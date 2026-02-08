# Colab deployment – always working

## Why "Notebook not found" happened

Colab **cannot open notebooks from private GitHub repos**. The "Open in Colab" link uses GitHub’s public API, which returns 404 for private repos.

**Fix applied:** The repo **Mnemos-2.0** is now **public**. No secrets are in the repo (`.env` is gitignored). Use Colab Secrets or upload `.env` for credentials.

---

## Method 1: Open in Colab (use this first)

1. Open: **https://colab.research.google.com/github/harshyadavv2456/Mnemos-2.0/blob/main/colab_setup.ipynb**
2. Add your secrets in the env cell or in Colab Secrets (🔑).
3. **Runtime → Run all.** The last cell runs MNEMOS 24/7 (2 min polling in market hours).

---

## Method 2: Clone and run (if the link still fails)

1. Go to **https://colab.research.google.com** and create a **New notebook**.
2. In the first cell, run:

   ```python
   !git clone https://github.com/harshyadavv2456/Mnemos-2.0.git
   %cd Mnemos-2.0
   ```

3. **File → Open notebook** → open `Mnemos-2.0/colab_setup.ipynb` from the file browser on the left.  
   Or copy the contents of `colab_setup.ipynb` from the repo into your notebook.
4. Run all cells of the setup notebook (install deps, set env, mount Drive, run MNEMOS).

---

## Keep it running (always live)

- **Polling:** Market hours = **2 min**; off hours = 30 min (configurable via env).
- **Session:** Free Colab can disconnect after ~90 min idle. To reduce disconnects:
  - Keep the browser tab active.
  - Optional: add a new cell with `%%javascript` and run it every ~60 min:  
    `document.querySelector('.colab-connect-button')?.click();`
- **After disconnect:** Re-open the Colab link (or your cloned notebook) and run **Run all** again. MNEMOS does not auto-reconnect; you need to re-run the notebook once per new session.

---

## Secrets (never in the repo)

Set these in Colab Secrets or in the env cell (or upload `.env` and load it):

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `GMAIL_USER`
- `GMAIL_APP_PASSWORD`
- `ALERT_EMAIL_TO` (comma-separated for mail trail)
- `GROQ_API_KEY`
