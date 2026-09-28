import os

from dotenv import load_dotenv

load_dotenv()  # must run before llm_client reads DEEPSEEK_API_KEY

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from db import get_state, save_state
from graph import build_graph
from report import generate_report, report_file_path

app = FastAPI(title="DREAM Wealth Framework API")
graph = build_graph()

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/app", StaticFiles(directory=STATIC_DIR, html=True), name="static")


class ChatRequest(BaseModel):
    user_id: str
    message: str


@app.post("/chat")
def chat(req: ChatRequest):
    state = get_state(req.user_id)
    state["user_id"] = req.user_id
    state.setdefault("conversation_history", [])
    state["conversation_history"].append({"role": "user", "content": req.message})

    result = graph.invoke(state)
    save_state(req.user_id, result)

    return {
        "reply": result.get("last_reply", ""),
        "stage": result.get("stage"),
    }


@app.get("/state/{user_id}")
def get_user_state(user_id: str):
    return get_state(user_id)


@app.post("/report/{user_id}")
def create_report(user_id: str):
    state = get_state(user_id)
    if state.get("stage") != "done":
        raise HTTPException(
            status_code=400,
            detail="Report is only available once the flow reaches the 'done' stage.",
        )
    path = generate_report(user_id, state)
    return {"report_path": path}


@app.get("/report/{user_id}/download")
def download_report(user_id: str):
    path = report_file_path(user_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Report not generated yet — POST /report/{user_id} first.")
    return FileResponse(path, media_type="application/pdf", filename="money_clarity_report.pdf")


@app.get("/")
def root():
    return {"message": "DREAM Wealth Framework API. Open /app/index.html for the demo chat UI."}
