from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from ocr.reader import extract_numbers
from indicators.compute import compute_features
from models.predictor import predict_signal, reload_onnx
from backend import config
import asyncio
import os
from pathlib import Path

app = FastAPI(title='AI Trading Assistant Backend')

# Simple in-memory set of connected WebSocket clients
ws_clients = set()

async def broadcast_message(message: dict):
    # send JSON to all connected clients; remove dead connections
    dead = []
    for ws in list(ws_clients):
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        try:
            ws_clients.remove(ws)
        except KeyError:
            pass


@app.post('/process-frame')
async def process_frame(frame: UploadFile = File(...)):
    try:
        contents = await frame.read()
        # OCR stub: extract numbers/text from the image/frame
        ocr_data = extract_numbers(contents)

        # Compute indicators/features stub
        features = compute_features(ocr_data)

        # Predict signal (dummy model)
        result = predict_signal(features)

        # Broadcast to any connected WebSocket clients (best-effort)
        asyncio.create_task(broadcast_message(result))

        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(content={'error': str(e)}, status_code=500)


@app.websocket('/ws/signals')
async def ws_signals(websocket: WebSocket):
    await websocket.accept()
    ws_clients.add(websocket)
    try:
        # Keep connection open. We don't require the client to send messages.
        while True:
            await asyncio.sleep(60)
    except WebSocketDisconnect:
        try:
            ws_clients.remove(websocket)
        except KeyError:
            pass


@app.get('/health')
async def health():
    return {'status': 'ok'}


@app.post('/upload-model')
async def upload_model(request: "fastapi.Request", file: UploadFile = File(...)):
    """Upload an ONNX model file and replace the current model.

    Requires header `X-ADMIN-TOKEN` to match `ADMIN_TOKEN` in `backend/config.py`.
    """
    try:
        rt = request.headers.get('x-admin-token')
        if not config.ADMIN_TOKEN:
            return JSONResponse(content={'status': 'error', 'message': 'ADMIN_TOKEN not configured on server'}, status_code=500)
        if not rt or rt != config.ADMIN_TOKEN:
            return JSONResponse(content={'status': 'unauthorized', 'message': 'invalid admin token'}, status_code=401)

        data = await file.read()
        models_dir = Path(__file__).resolve().parents[0] / 'models'
        models_dir.mkdir(parents=True, exist_ok=True)
        target = models_dir / 'model.onnx'
        with open(target, 'wb') as f:
            f.write(data)

        # attempt to reload model in predictor
        ok = reload_onnx()
        if not ok:
            return JSONResponse(content={'status': 'error', 'message': 'Model saved but failed to load'}, status_code=500)
        return JSONResponse(content={'status': 'ok', 'message': 'Model uploaded and loaded'})
    except Exception as e:
        return JSONResponse(content={'status': 'error', 'message': str(e)}, status_code=500)
    


@app.get('/model-info')
async def model_info(request: "fastapi.Request"):
    """Return model inputs/outputs information for the currently deployed model (if any)."""
    try:
        rt = request.headers.get('x-admin-token')
        if not config.ADMIN_TOKEN:
            return JSONResponse(content={'status': 'error', 'message': 'ADMIN_TOKEN not configured on server'}, status_code=500)
        if not rt or rt != config.ADMIN_TOKEN:
            return JSONResponse(content={'status': 'unauthorized', 'message': 'invalid admin token'}, status_code=401)
        
        model_path = config.resolve_model_path()
        if not model_path.exists():
            return JSONResponse(content={'status': 'no_model', 'message': str(model_path)}, status_code=404)
        try:
            import onnxruntime as ort
            sess = ort.InferenceSession(str(model_path))
            inputs = []
            for inp in sess.get_inputs():
                inputs.append({'name': inp.name, 'shape': [d.dim_value for d in inp.type.tensor_type.shape.dim]})
            outputs = []
            for out in sess.get_outputs():
                outputs.append({'name': out.name, 'shape': [d.dim_value for d in out.type.tensor_type.shape.dim]})
            return JSONResponse(content={'status': 'ok', 'model': str(model_path), 'inputs': inputs, 'outputs': outputs})
        except Exception as e:
            return JSONResponse(content={'status': 'error', 'message': str(e)}, status_code=500)
    except Exception as e:
        return JSONResponse(content={'status': 'error', 'message': str(e)}, status_code=500)
