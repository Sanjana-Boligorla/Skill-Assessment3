"""Loads the React app HTML and injects the API base URL."""
import os

_DIR = os.path.dirname(os.path.abspath(__file__))

def get_html(api_base: str = "http://localhost:8000") -> str:
    path = os.path.join(_DIR, "frontend", "index.html")
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    return html.replace("__API_BASE__", api_base)
