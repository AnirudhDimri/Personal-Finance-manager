import json
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "dream_app.db")


def _init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            user_id TEXT PRIMARY KEY,
            state TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


_init_db()


def _default_state(user_id: str) -> dict:
    return {
        "user_id": user_id,
        "stage": "diagnose",
        "financials": {},
        "dreams": [],
        "beliefs": [],
        "budget": {},
        "goal_gaps": [],
        "habits": [],
        "conversation_history": [],
        "last_message": "",
        "last_reply": "",
    }


def get_state(user_id: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT state FROM sessions WHERE user_id = ?", (user_id,)
    ).fetchone()
    conn.close()

    if row:
        return json.loads(row[0])
    return _default_state(user_id)


def save_state(user_id: str, state: dict) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO sessions (user_id, state) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET state = excluded.state
        """,
        (user_id, json.dumps(state)),
    )
    conn.commit()
    conn.close()
