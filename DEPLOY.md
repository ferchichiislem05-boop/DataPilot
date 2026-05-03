# Deploying DataPilot on Streamlit Community Cloud

**Streamlit Community Cloud is the only supported deployment target.**
This app is a Streamlit app — it cannot run on Vercel, Netlify, or any static hosting platform.

---

## Prerequisites

- A GitHub account
- An Anthropic API key — get one free at [console.anthropic.com](https://console.anthropic.com)

---

## Steps

### 1. Fork the repository

Go to **https://github.com/ferchichiislem05-boop/DataPilot** and click **Fork**.

### 2. Go to Streamlit Community Cloud

Open **https://share.streamlit.io** and sign in with GitHub.

### 3. Create a new app

Click **"New app"** and fill in the form:

| Field | Value |
|---|---|
| Repository | `your-username/DataPilot` |
| Branch | `main` |
| Main file path | `app/main.py` |

### 4. Add your API key

Before clicking Deploy, open **"Advanced settings"** → **"Secrets"** tab and paste:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

Replace `sk-ant-...` with your real Anthropic key.

### 5. Deploy

Click **"Deploy"**. The app will be live in ~2 minutes at:
```
https://your-username-datapilot-app-main-xxxxx.streamlit.app
```

---

## Updating the app

Every `git push` to the `main` branch triggers an automatic redeploy — no action needed.

---

## Local development

```bash
# Install dependencies
pip install -r requirements.txt

# Add your key
cp .env.example .env
# Edit .env → set ANTHROPIC_API_KEY=sk-ant-...

# Run
streamlit run app/main.py
```

---

## Notes

- The SQLite database (`data/sample.db`) is created automatically on first launch — it is not committed to git.
- Secrets are stored in Streamlit Cloud's encrypted vault — never in the repository.
- Do **not** commit `.streamlit/secrets.toml` — it is excluded by `.gitignore`.
