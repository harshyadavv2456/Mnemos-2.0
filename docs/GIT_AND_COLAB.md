# Push to Git (private repo) and run on Colab

## 1. Push to GitHub (private repo "Mnemos 2.0")

### Option A: Using GitHub CLI (if installed)

```bash
cd "d:\Mnemos 2.0"
gh repo create Mnemos-2.0 --private --source=. --remote=origin --push --description "MNEMOS 2.1 - Institutional-grade Indian market intelligence"
```

### Option B: Manual (create repo on GitHub first)

1. **Create the repo on GitHub**
   - Go to https://github.com/new
   - Repository name: **Mnemos-2.0** (or **Mnemos-2.0**)
   - Visibility: **Private**
   - Do **not** add README, .gitignore, or license (we already have them)
   - Click Create repository

2. **Push from your machine**

   ```bash
   cd "d:\Mnemos 2.0"
   git remote add origin https://github.com/YOUR_GITHUB_USERNAME/Mnemos-2.0.git
   git branch -M main
   git push -u origin main
   ```

   Replace `YOUR_GITHUB_USERNAME` with your GitHub username. If GitHub asks for credentials, use a **Personal Access Token** (Settings → Developer settings → Personal access tokens) as the password.

---

## 2. Open and run on Colab

After the repo is on GitHub:

1. **Open the notebook in Colab**
   - Go to: **https://colab.research.google.com/github/YOUR_GITHUB_USERNAME/Mnemos-2.0/blob/main/colab_setup.ipynb**
   - Replace `YOUR_GITHUB_USERNAME` with your GitHub username.
   - Or: GitHub repo page → open `colab_setup.ipynb` → click "Open in Colab" (if the button is shown).

2. **Add your secrets (repo is private but .env is not in Git)**
   - In Colab, either:
     - **Colab Secrets**: Left sidebar → 🔑 Secrets → add `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `ALERT_EMAIL_TO`, `GROQ_API_KEY` (copy from your local `.env`), or
     - **Upload .env**: Upload your local `.env` file to the Colab session (e.g. to `/content/`), then in the env cell set `MNEMOS_ROOT = Path('/content')` and run `load_dotenv('/content/.env')` so the notebook loads it.

3. **Run all cells**
   - Runtime → Run all. The last cell runs MNEMOS 24/7 until the session disconnects.

---

## 3. One-time: ensure .env is never committed

The project `.gitignore` already includes `.env`. Never remove that. Your `.env` stays only on your machine (and you upload it to Colab manually or use Colab Secrets).
