import os
import threading
import time
import socket

from dotenv import load_dotenv
load_dotenv()

os.environ.setdefault("OPENAI_API_KEY", "learner052")
os.environ["OPENAI_BASE_URL"] = "https://keygateway.arshnivlabs.com/v1"

import streamlit as st

st.set_page_config(
    page_title="ProductIQ — AI Strategy Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── hide all Streamlit chrome ─────────────────────────────────────────────────
st.markdown("""
<style>
  #MainMenu, header, footer, .stDeployButton,
  [data-testid="stToolbar"], [data-testid="stDecoration"],
  [data-testid="stStatusWidget"], section[data-testid="stSidebar"] { display:none !important; }
  .main .block-container { padding:0 !important; max-width:100% !important; }
  .main { padding:0 !important; }
</style>
""", unsafe_allow_html=True)

API_PORT = 8000


def _port_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) != 0


def _start_api():
    if not _port_free(API_PORT):
        return  # already running
    import uvicorn
    from api import app as fastapi_app
    uvicorn.run(fastapi_app, host="0.0.0.0", port=API_PORT, log_level="error")


# Start FastAPI in background thread once
if "api_started" not in st.session_state:
    st.session_state.api_started = True
    t = threading.Thread(target=_start_api, daemon=True)
    t.start()
    time.sleep(2)  # give uvicorn a moment to bind

# ── wait for API to be ready then render React ────────────────────────────────
from react_app import get_html
import streamlit.components.v1 as components

components.html(
    get_html(api_base=f"http://localhost:{API_PORT}"),
    height=900,
    scrolling=False,
)
