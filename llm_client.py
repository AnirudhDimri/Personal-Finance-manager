import json
import os

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


def call_stage_llm(system_prompt: str, user_message: str, history: list) -> dict:
    """
    Calls DeepSeek with a system prompt that instructs it to reply with strict JSON:
        {"reply": str, "extracted": dict, "complete": bool}
    Falls back to treating the raw text as the reply if JSON parsing fails,
    so a malformed model response never crashes the app.
    """
    client = get_client()

    clean_history = [
        {"role": m["role"], "content": m["content"]}
        for m in history
        if m.get("role") in ("user", "assistant")
    ]
    messages = (
        [{"role": "system", "content": system_prompt}]
        + clean_history
        + [{"role": "user", "content": user_message}]
    )

    response = client.chat.completions.create(
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
    client = get_client()
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )
    return _text_from_response(response)
