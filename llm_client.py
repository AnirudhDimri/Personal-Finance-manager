import json
import os
from typing import Optional

from openai import OpenAI

_client = None

MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")


def get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError(
                "DEEPSEEK_API_KEY is not set. Copy .env.example to .env and fill it in."
            )
        _client = OpenAI(api_key=api_key, base_url=BASE_URL)
    return _client


def _text_from_response(response) -> str:
    return (response.choices[0].message.content or "").strip()


# Cap what we send to the model; full history still stays in SQLite.
_MAX_HISTORY_MESSAGES = 20


def _chat_messages(history: list) -> list:
    msgs = [
        {"role": m["role"], "content": m["content"]}
        for m in history
        if m.get("role") in ("user", "assistant")
    ]
    return msgs[-_MAX_HISTORY_MESSAGES:]


def call_stage_llm(
    system_prompt: str,
    history: list,
    extra_user: Optional[str] = None,
) -> dict:
    """
    Calls DeepSeek with a system prompt that instructs it to reply with strict JSON:
        {"reply": str, "extracted": dict, "complete": bool}
    Falls back to treating the raw text as the reply if JSON parsing fails.
    Pass extra_user only when that turn is not already the last item in history
    (e.g. Habits, which sends budget/gaps as a one-off prompt).
    """
    messages = [{"role": "system", "content": system_prompt}] + _chat_messages(history)
    if extra_user:
        messages.append({"role": "user", "content": extra_user})

    response = get_client().chat.completions.create(
        model=MODEL,
        max_tokens=800,
        response_format={"type": "json_object"},
        messages=messages,
    )
    text = _text_from_response(response)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"reply": text, "extracted": {}, "complete": False}


def call_plain(system_prompt: str, user_content: str, max_tokens: int = 500) -> str:
    """Plain-text call for stages that don't need structured extraction (Execute, Allocate)."""
    response = get_client().chat.completions.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )
    return _text_from_response(response)
