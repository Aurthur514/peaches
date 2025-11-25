import streamlit as st
import requests
import os
from pathlib import Path

st.set_page_config(page_title="AI Trading Assistant (Streamlit)", layout="wide")

DEFAULT_BACKEND = os.environ.get("BACKEND_URL") or st.secrets.get("BACKEND_URL", "http://127.0.0.1:8000")

st.title("AI Manual Trading Assistant — Streamlit UI")

with st.sidebar.form("config"):
    backend_url = st.text_input("Backend URL", value=DEFAULT_BACKEND)
    # allow admin token from secrets if present
    default_admin = os.environ.get("ADMIN_TOKEN") or st.secrets.get("ADMIN_TOKEN", "")
    admin_token = st.text_input("Admin token (optional)", value=default_admin, type="password")
    enable_easyocr = st.selectbox("Enable EasyOCR on backend?", options=["0", "1"], index=0)
    submit_cfg = st.form_submit_button("Apply")

st.sidebar.markdown("---")
st.sidebar.markdown("Quick actions:")
if st.sidebar.button("Check backend /health"):
    try:
        r = requests.get(f"{backend_url}/health", timeout=10)
        st.sidebar.success(f"Health: {r.status_code} {r.text}")
    except Exception as e:
        st.sidebar.error(f"Health check failed: {e}")

col1, col2 = st.columns([2, 1])

with col1:
    st.header("Send Frame")
    uploaded = st.file_uploader("Upload image/frame (jpg/png)", type=["jpg", "jpeg", "png"], accept_multiple_files=False)
    if uploaded is not None:
        st.image(uploaded, caption="Preview", use_column_width=True)
    send = st.button("Send to backend")
    if send:
        if uploaded is None:
            st.warning("Upload an image first")
        else:
            files = {"frame": (uploaded.name, uploaded.getvalue())}
            try:
                resp = requests.post(f"{backend_url}/process-frame", files=files, timeout=30)
                st.subheader("Response")
                try:
                    st.json(resp.json())
                except Exception:
                    st.text(resp.text)
            except Exception as e:
                st.error(f"Request failed: {e}")

with col2:
    st.header("Admin — Model Upload")
    st.markdown("Upload an ONNX model to the backend (admin token required).")
    onnx_file = st.file_uploader("ONNX model file", type=["onnx"]) 
    if st.button("Upload model"):
        if onnx_file is None:
            st.warning("Choose an ONNX file to upload")
        elif not admin_token:
            st.warning("Enter admin token in the sidebar")
        else:
            headers = {"X-ADMIN-TOKEN": admin_token}
            files = {"model": (onnx_file.name, onnx_file.getvalue())}
            try:
                r = requests.post(f"{backend_url}/upload-model", headers=headers, files=files, timeout=60)
                if r.status_code in (200, 201):
                    st.success("Model uploaded successfully")
                    st.write(r.text)
                else:
                    st.error(f"Upload failed: {r.status_code} {r.text}")
            except Exception as e:
                st.error(f"Upload request failed: {e}")

st.markdown("---")
st.markdown("Troubleshooting & notes:")
st.markdown("- This UI posts frames to the backend `/process-frame` endpoint. Ensure the backend is reachable from this host.")
st.markdown("- For a full interactive capture frontend (screen capture + floating widget) continue to use the React frontend. This Streamlit UI is a lightweight alternative for fast deployment and testing.")

if __name__ == '__main__':
    st.write("Streamlit UI loaded")
