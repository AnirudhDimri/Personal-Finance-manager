# D.R.E.A.M. Wealth Framework — AI App

A conversational AI app that walks a user through the D.R.E.A.M. Wealth Framework
(Dream & Diagnose → Rewire → Execute → Allocate → Money Habits), ending in a
downloadable "Money Clarity Report" PDF.

## Setup

```bash
cd Personal-Finance-manager
python -m venv ve
ve\Scripts\activate            # macOS/Linux: source ve/bin/activate
pip install -r requirements.txt
copy .env.example .env         # macOS/Linux: cp .env.example .env
# then paste your DEEPSEEK_API_KEY into .env
python -m uvicorn main:app --reload
```

Open **http://localhost:8000/app/index.html** in a browser to try the chat demo.

## How it's wired

- **`graph.py`** — LangGraph `StateGraph` with one node per DREAM stage. Each
  incoming chat message is routed to whichever stage the session is currently
  in (`route_stage`). Diagnose and Rewire each handle one user turn at a time
  and wait for the next message; once Rewire completes, the graph
  automatically cascades through Execute → Allocate → Habits in the same
  request, since those three stages are deterministic and need no further
  user input to produce their first output.
- **`nodes.py`** — the actual logic for each of the 5 stages.
- **`calculations.py`** — net worth, required monthly savings, goal-gap, and
  budget math. This is **plain Python, not the LLM** — the model explains
  these numbers, it never computes them.
- **`rag.py`** — retrieval for the Rewire stage's money-mindset reframes.
  Ships as simple keyword-overlap search over a small hardcoded corpus so the
  project runs with zero extra infrastructure. Swap `retrieve_reframe()` for a
  real vector store (Chroma, pgvector, etc.) once you have a bigger content
  library — nothing else in the app needs to change.
- **`db.py`** — SQLite-backed session state, keyed by `user_id`, so a user can
  close the tab and resume later.
- **`report.py`** — builds the final PDF summary with `reportlab`.
- **`main.py`** — FastAPI app: `/chat`, `/state/{user_id}`,
  `/report/{user_id}` (generate), `/report/{user_id}/download`.
- **`static/index.html`** — a minimal one-page chat UI for demos. Swap in a
  real frontend later; the API doesn't change.

## API quick reference

| Method | Path                          | Purpose                                  |
|--------|-------------------------------|-------------------------------------------|
| POST   | `/chat`                       | `{user_id, message}` → `{reply, stage}`   |
| GET    | `/state/{user_id}`            | Full session state (for debugging/resume) |
| POST   | `/report/{user_id}`           | Generates the PDF (stage must be `done`)  |
| GET    | `/report/{user_id}/download`  | Downloads the generated PDF               |

## What's deliberately not built yet

- No auth / multi-user accounts (single `user_id` string).
- No bank/UPI statement parsing — all figures are self-reported.
- No WhatsApp/Telegram nudges for the Habits stage.
- No real vector DB for the mindset corpus (see `rag.py`).
