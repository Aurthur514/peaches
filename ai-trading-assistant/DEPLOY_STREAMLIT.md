# Deploy Streamlit UI (ai-trading-assistant)

This document explains how to deploy the quick Streamlit UI (`streamlit_app.py`) to Streamlit Community Cloud (share.streamlit.io).

Files added for deploy
- `ai-trading-assistant/streamlit_app.py` — the Streamlit app
- `ai-trading-assistant/requirements-streamlit.txt` — minimal requirements for the app

Steps

1. Push changes to GitHub (already done in this repo). Ensure the `ai-trading-assistant/streamlit_app.py` file is in `main` branch.

2. Open Streamlit Community Cloud: https://share.streamlit.io/

3. Click **New app** → Connect to GitHub (if not connected) → select repository `Aurthur514/peaches` → Branch `main`.

4. For **File path**, enter:

```
ai-trading-assistant/streamlit_app.py
```

5. For **Requirements file**, set the path to:

```
ai-trading-assistant/requirements-streamlit.txt
```

6. (Optional, recommended) Add secrets for `BACKEND_URL` and `ADMIN_TOKEN` in the **Secrets** section. Click **Advanced settings** → **Secrets** and add a TOML snippet like:

```toml
BACKEND_URL = "https://<your-backend-url>.onrender.com"
ADMIN_TOKEN = "<your-admin-token>"
```

Notes
- The app reads `BACKEND_URL` from `st.secrets["BACKEND_URL"]` or environment variable `BACKEND_URL`. If neither is set, it defaults to `http://127.0.0.1:8000`.
- Admin model uploads use the `X-ADMIN-TOKEN` header; set `ADMIN_TOKEN` as a secret and paste it into the sidebar on first run, or keep it in the sidebar manually.
- If your backend is on Render (or elsewhere) secure the backend deployment first and set its public URL as `BACKEND_URL`.

Testing after deploy

- Open the Streamlit app URL provided by Streamlit Cloud.
- Use **Check backend /health** in the sidebar to verify connectivity.
- Upload an image and click **Send to backend**; the app will POST to `/process-frame` and display the response.

Troubleshooting

- If the app fails to start, check the **Logs** on Streamlit Cloud — missing packages or import errors will be shown.
- If backend calls are timing out, ensure `BACKEND_URL` is reachable from the public internet and that CORS / firewall rules allow requests.
