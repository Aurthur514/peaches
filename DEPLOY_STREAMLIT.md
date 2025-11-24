Deploying Task 3 Streamlit App to Streamlit Cloud

This document explains how to host `task_3_glr_streamlit.py` on Streamlit Cloud.

Prerequisites
- Your repository is on GitHub (branch `feature/task3-glr` exists).
- The app entrypoint file is `task_3_glr_streamlit.py` at the repository root.
- Python dependencies are listed in `task_3_requirements.txt` (we also placed a `requirements.txt` at repo root if you prefer).

Steps (Streamlit Cloud)
1. Push your branch to GitHub (already done): `feature/task3-glr`.
2. Go to https://share.streamlit.io and sign in with your GitHub account.
3. Click "New app".
4. Select the repository `Aurthur514/peaches` (or your fork), then select the branch `feature/task3-glr` and set the "Main file path" to `task_3_glr_streamlit.py`.
5. Click "Deploy".

Setting secrets (API keys)
- Do not commit API keys to the repo. Use Streamlit Cloud Secrets:
  - Open the deployed app's settings in Streamlit Cloud.
  - Under "Secrets", add keys like:
    - `GEMINI_API_KEY` = <your key>
    - `OPENROUTER_API_KEY` = <your key> (optional)
    - `OPENAI_API_KEY` = <your key> (optional)
  - Save secrets and redeploy.

If your PDF inputs may be scanned images (OCR required)
- Install Tesseract and Poppler on the host.
- Streamlit Cloud currently does not provide arbitrary native binaries; you will likely need to use a Docker-based host (e.g., Render, Fly, or a VM) to include native dependencies.
- As a workaround, convert scanned PDFs to text locally and upload the text to the app, or use an external OCR API.

Alternative: Docker (self-hosted)
If you prefer to host on a server with native dependencies, use Docker.
1. Create a `Dockerfile` (example below).
2. Build and run on any container host (DigitalOcean, AWS, Render with Docker, etc.).

Example `Dockerfile` (simple):

```
FROM python:3.11-slim
RUN apt-get update && apt-get install -y poppler-utils tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r task_3_requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "task_3_glr_streamlit.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
```

Notes & Troubleshooting
- If Streamlit Cloud fails to install dependencies, check the app logs for pip errors.
- If LLM calls fail, verify the environment secrets and that the provider supports REST API keys in the way the script uses them.
- For Gemini/Google Generative Language, you may need a Google Cloud service-account-style setup or a particular endpoint — check your Google Cloud console and IAM/API settings.

If you want, I can:
- Create the `requirements.txt` at repo root (copying `task_3_requirements.txt`).
- Create a basic `Dockerfile` in the repo for self-hosting.
- Open a draft PR with these deployment files.

Tell me which (if any) of the above you want me to add now.
