# Deploy on Colab – Final Step

Your `.env` is already configured with:

- **Telegram bot**: @mnemosupdatebot (token set)
- **Gmail**: studyharsh19@gmail.com (app password set)
- **Mail trail**: studyharsh19@gmail.com, harshyadavv2456@gmail.com (add more in `ALERT_EMAIL_TO` in `.env` to include others)
- **GROQ**: API key set for free Llama analysis on alerts

## You must do this once

1. **Get your Telegram Chat ID**
   - Open Telegram and message **@userinfobot**
   - Send any message; it will reply with your numeric **Id**
   - Open `.env` and set:  
     `TELEGRAM_CHAT_ID=your_numeric_id`

2. **Deploy on Colab**
   - Zip the project folder (include the `.env` file) or clone from your repo and add `.env` manually.
   - Upload to Colab, unzip to `/content/mnemos2.0` (or set `MNEMOS_ROOT` in the notebook).
   - Open `colab_setup.ipynb` and run all cells. The notebook loads `.env` from the project, so Telegram, Gmail, GROQ, and mail trail are used automatically.
   - If you don’t upload `.env`, set the same variables in the Colab env cell (or Colab Secrets):  
     `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `ALERT_EMAIL_TO`, `GROQ_API_KEY`.

After that, MNEMOS runs 24/7; alerts (with optional GROQ analysis) go to Telegram and to everyone in the `ALERT_EMAIL_TO` mail trail.
