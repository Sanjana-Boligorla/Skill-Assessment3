import os
import threading
import uuid
from typing import Dict

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dotenv import load_dotenv
load_dotenv()

os.environ.setdefault("OPENAI_API_KEY", "learner052")
os.environ["OPENAI_BASE_URL"] = "https://keygateway.arshnivlabs.com/v1"

app = FastAPI(title="ProductIQ API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── in-memory store ───────────────────────────────────────────────────────────
_store: Dict[str, dict] = {
    "files": [],          # parsed file dicts
    "pipeline_state": {}, # final agent outputs
    "pipeline_run": False,
    "pipeline_running": False,
    "agent_statuses": {},  # {agent_id: "pending"|"active"|"done"|"error"}
    "current_agent": None,
    "report_bytes": None,
    "chat_history": [],
}

AGENT_ORDER = [
    "data_ingestion", "customer_feedback", "market_research",
    "swot_analysis", "feature_prioritization",
    "strategy_recommendation", "executive_report",
]

# ── helpers ───────────────────────────────────────────────────────────────────
def _reset_pipeline():
    _store["pipeline_run"] = False
    _store["pipeline_running"] = False
    _store["pipeline_state"] = {}
    _store["agent_statuses"] = {a: "pending" for a in AGENT_ORDER}
    _store["current_agent"] = None
    _store["report_bytes"] = None


# ── routes ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    from utils.data_parser import parse_uploaded_file
    parsed = []
    for f in files:
        content = await f.read()
        try:
            result = parse_uploaded_file(f.filename, content)
            # strip heavy dataframe_json to keep response small
            result.pop("dataframe_json", None)
            parsed.append(result)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error parsing {f.filename}: {e}")
    _store["files"] = parsed
    _reset_pipeline()
    return {"uploaded": len(parsed), "files": [{"name": p["filename"], "type": p["type"]} for p in parsed]}


@app.get("/files")
def get_files():
    summaries = []
    for f in _store["files"]:
        s = {"filename": f["filename"], "type": f["type"]}
        if f["type"] == "csv":
            s.update({
                "records": f.get("total_records", 0),
                "revenue": f.get("total_revenue", 0),
                "profit": f.get("total_profit", 0),
                "units": f.get("total_units", 0),
                "avg_rating": f.get("avg_rating", 0),
                "returns": f.get("total_returns", 0),
                "products": f.get("products", []),
                "categories": f.get("categories", []),
                "regions": f.get("regions", []),
                "date_range": f.get("date_range", ""),
                "product_performance": f.get("product_performance", []),
                "regional_performance": f.get("regional_performance", []),
                "category_performance": f.get("category_performance", []),
            })
        return summaries.append(s) or summaries
    return summaries


@app.post("/run")
def run_pipeline():
    if not _store["files"]:
        raise HTTPException(status_code=400, detail="No files uploaded")
    if _store["pipeline_running"]:
        return {"status": "already_running"}

    _reset_pipeline()
    _store["pipeline_running"] = True

    def _worker():
        try:
            from utils.data_parser import build_context_string, parse_uploaded_file
            import json

            # Re-read files (need dataframe_json for build_context)
            full_files = _store.get("_full_files", _store["files"])
            context = build_context_string(full_files)

            from agents.orchestrator import AGENT_SEQUENCE
            state = {
                "parsed_files": full_files,
                "data_context": context,
                "agent_logs": [],
                "pipeline_complete": False,
            }
            for i, (name, desc, fn) in enumerate(AGENT_SEQUENCE):
                aid = name.lower().replace(" ", "_")
                _store["current_agent"] = aid
                _store["agent_statuses"][aid] = "active"
                try:
                    state = fn(state)
                    _store["agent_statuses"][aid] = "done"
                except Exception as e:
                    _store["agent_statuses"][aid] = "error"
                    state[aid + "_error"] = str(e)

            _store["current_agent"] = None
            _store["pipeline_state"] = state
            _store["pipeline_run"] = True
            _store["pipeline_running"] = False

            # Generate PDF
            try:
                from utils.pdf_generator import generate_report
                pdf = generate_report({
                    "key_metrics":             state.get("key_metrics", {}),
                    "customer_insights":       state.get("customer_insights", ""),
                    "market_research":         state.get("market_research", ""),
                    "swot_analysis":           state.get("swot_analysis", ""),
                    "opportunity_assessment":  state.get("opportunity_assessment", ""),
                    "feature_prioritization":  state.get("feature_prioritization", ""),
                    "strategy_recommendations":state.get("strategy_recommendations", ""),
                    "executive_summary":       state.get("executive_summary", ""),
                })
                _store["report_bytes"] = pdf
            except Exception:
                pass
        except Exception as e:
            _store["pipeline_running"] = False
            _store["pipeline_state"]["error"] = str(e)

    threading.Thread(target=_worker, daemon=True).start()
    return {"status": "started"}


@app.post("/upload-full")
async def upload_full(files: list[UploadFile] = File(...)):
    """Store full parsed data including dataframe_json for pipeline use."""
    from utils.data_parser import parse_uploaded_file
    parsed = []
    for f in files:
        content = await f.read()
        try:
            result = parse_uploaded_file(f.filename, content)
            parsed.append(result)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    _store["_full_files"] = parsed
    _store["files"] = [{k: v for k, v in p.items() if k != "dataframe_json"} for p in parsed]
    _reset_pipeline()
    return {"uploaded": len(parsed)}


@app.get("/status")
def get_status():
    return {
        "pipeline_run": _store["pipeline_run"],
        "pipeline_running": _store["pipeline_running"],
        "current_agent": _store["current_agent"],
        "agent_statuses": _store["agent_statuses"],
        "has_report": _store["report_bytes"] is not None,
        "key_metrics": _store["pipeline_state"].get("key_metrics", {}),
    }


@app.get("/insights")
def get_insights():
    s = _store["pipeline_state"]
    return {
        "customer_insights":       s.get("customer_insights", ""),
        "market_research":         s.get("market_research", ""),
        "swot_analysis":           s.get("swot_analysis", ""),
        "opportunity_assessment":  s.get("opportunity_assessment", ""),
        "feature_prioritization":  s.get("feature_prioritization", ""),
        "strategy_recommendations":s.get("strategy_recommendations", ""),
        "executive_summary":       s.get("executive_summary", ""),
        "key_metrics":             s.get("key_metrics", {}),
        "ingestion_status":        s.get("ingestion_status", ""),
    }


@app.get("/report")
def download_report():
    from fastapi.responses import Response
    if not _store["report_bytes"]:
        raise HTTPException(status_code=404, detail="Report not generated yet")
    return Response(
        content=_store["report_bytes"],
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=strategy_report.pdf"},
    )


class ChatRequest(BaseModel):
    question: str


@app.post("/chat")
def chat(req: ChatRequest):
    if not _store["pipeline_run"]:
        raise HTTPException(status_code=400, detail="Run the pipeline first")
    from agents.orchestrator import run_chat_query
    answer = run_chat_query(req.question, _store["pipeline_state"])
    _store["chat_history"].append({"role": "user", "content": req.question})
    _store["chat_history"].append({"role": "assistant", "content": answer})
    return {"answer": answer}


@app.get("/chat/history")
def chat_history():
    return {"history": _store["chat_history"]}


@app.delete("/chat/history")
def clear_chat():
    _store["chat_history"] = []
    return {"status": "cleared"}
