# AI Trading Assistant — Manual Mode (React + FastAPI)
This is a lightweight **starter project** for the AI Manual Trading Assistant you requested.
It captures a selected screen/window in the browser (you choose what to share), sends frames to a local FastAPI backend,
and the backend returns a dummy trading signal. All execution is local and manual — no automatic order placement.

## What's included
- `frontend/` — Minimal React app (Vite-style structure) with screen capture & floating signal widget.
- `backend/` — FastAPI app with endpoints to receive frames, run OCR stub, compute indicators stub, and return a dummy prediction.
- `models/` — placeholder for model files.
- `run_frontend.sh` and `run_backend.sh` — quick run scripts.

## Quick start (Linux / WSL / macOS)
1. Backend:
   - `cd backend`
   - `python3 -m venv .venv && source .venv/bin/activate`
   - `pip install -r requirements.txt`
   - `uvicorn main:app --reload --host 127.0.0.1 --port 8000`
2. Frontend:
   - `cd frontend`
   - `npm install` (or `pnpm`/`yarn`)
   - `npm run dev` (Vite default — app served on http://localhost:5173)
3. Open the frontend in your browser, click "Start Capture", and allow capturing the chart window.

## Notes
- This is a starter skeleton. OCR, real model, and robust feature extraction are provided as stubs that you can replace with real implementations.
- All processing runs locally by default. No keys, no cloud required.

## Docker / Compose (quick local demo)
From the `ai-trading-assistant/ai-trading-assistant` directory you can build and run both services with Docker Compose:

```bash
docker compose build
docker compose up
```

After the stack starts:
- Backend API: `http://127.0.0.1:8000`
- Frontend (static): `http://127.0.0.1:3000`

Use the included test script to send a quick frame to the backend (requires `requests` and `Pillow`):

```bash
python -m pip install requests pillow
python tests/send_sample_frame.py
```

Health check endpoint: `GET /health` (returns `{ "status": "ok" }`).

Security note: this demo is intentionally simple. If you expose services to a network, secure the endpoints and restrict screen capture origins.

## Going live (production checklist)

This project includes Dockerfiles and a `docker-compose.yml`. For a minimal production deploy on a VPS or cloud VM (DigitalOcean, AWS EC2, Hetzner, etc):

1. Copy the repo to the server and create a strong admin token:

```bash
# generate a random admin token
python - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
```

2. Create `.env` in `backend/` (or run `python backend/tools/init_env.py` and edit it) and set `ADMIN_TOKEN` and any other variables.

3. Start the stack with Docker Compose (detached):

```bash
cd ai-trading-assistant/ai-trading-assistant
docker compose build
docker compose up -d
```

4. Set up an HTTPS reverse proxy (recommended):
   - Run `nginx` on the host, proxy `/` to the frontend (port 3000) and `/api` or `/` to backend port 8000 as appropriate.
   - Use Certbot (Let's Encrypt) to obtain certificates and enable TLS.

Example `nginx` server block (simplified):

```nginx
server {
   listen 80;
   server_name your.domain.example;
   location / {
      proxy_pass http://127.0.0.1:3000;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
   }
   location /upload-model {
      proxy_pass http://127.0.0.1:8000/upload-model;
   }
}
```

5. Firewall & security:
   - Allow only necessary ports (80/443) and SSH.
   - Do not expose `/upload-model` or `/model-info` publicly without further authentication; the admin token is a minimal protection — consider IP whitelisting or stronger auth.

6. Monitoring and service management:
   - Use `docker compose` in restart policy or systemd unit to ensure service restarts on failure.
   - Configure logging and rotate logs; consider running Prometheus/Alerting if needed.

Notes:
- The admin token is passed via the `X-ADMIN-TOKEN` HTTP header. Keep it secret.
- For production ONNX GPU inference, use `Dockerfile.gpu` and ensure the host has NVIDIA Container Toolkit installed.
- If you require CI/CD, connect your repo to a CI service and deploy by running remote `docker compose pull && docker compose up -d`.

## Model integration plan

- Drop an ONNX model named `model.onnx` into `backend/models/` and the backend will attempt to use it for prediction. The predictor will:
   - Try `onnxruntime` to load `models/model.onnx` at startup/use-time.
   - Map common inputs (`ema20`, `ema50`, `rsi`, `last_price`) to model inputs where possible.
   - Fall back to the internal heuristic if the model load or inference fails.

Notes:
- ONNX models typically expect inputs as numpy arrays; adapt `backend/models/predictor.py` to match your model's input names and shapes.
- For GPU inferencing use an `onnxruntime-gpu` build and the provided `Dockerfile.gpu` example. That requires NVIDIA Container Toolkit on the host.

### Uploading a model at runtime

You can upload a model at runtime via the API:

```
POST /upload-model
form-data: file -> model.onnx
```

The backend will save the model to `backend/models/model.onnx` and attempt to load it. If the model fails to load, the API returns an error and the previous model remains cached.

### ONNX inspection helper

Use `python backend/tools/onnx_inspect.py` to print model inputs/outputs and receive suggested key mappings.

### EasyOCR-enabled container

If you want to use EasyOCR, build the `backend/Dockerfile.eocr` image (it installs CPU PyTorch and EasyOCR, the image will be larger):

```bash
docker build -f backend/Dockerfile.eocr -t trading-backend-eocr .
```


## OCR / Inference choices

- The backend supports optional `pytesseract` OCR if you install Tesseract on the host or in the container. The `backend/Dockerfile` installs Tesseract by default.
- If you need more accurate OCR, consider integrating `EasyOCR` or other model-based readers — replace the `extract_numbers` implementation in `backend/ocr/reader.py`.

## Security & Compliance Checklist (starter)

- Do not enable automatic order placement in this project; keep manual-only gating on signals.
- If exposing the API beyond localhost, add authentication (API keys or OAuth) and TLS termination.
- Restrict origins and implement CORS rules to only allow your frontend origin.
- Validate and sanitize all uploaded frames; limit file sizes and rate-limit requests to avoid DoS.
- Log access and decisions with audit metadata, but avoid logging sensitive images persistently unless encrypted and consented.
- Rotate any credentials and never commit secrets to the repo. Use environment variables or secret managers.
- Review local regulatory rules (e.g., SEBI) around automated trading signals and keep a human-in-the-loop for any trade execution.
