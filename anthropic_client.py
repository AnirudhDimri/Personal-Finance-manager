import json
import os

from anthropic import Anthropic

_client = None

MODEL = "claude-sonnet-4-6"


def get_client() -> Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and fill it in."
            )
        _client = Anthropic(api_key=api_key)
    return _client


def call_stage_llm(system_prompt: str, user_message: str, history: list) -> dict:
    """
    Calls Claude with a system prompt that instructs it to reply with strict JSON:
        {"reply": str, "extracted": dict, "complete": bool}
    Falls back to treating the raw text as the reply if JSON parsing fails,
    so a malformed model response never crashes the app.
    """
    client = get_client()

    # Anthropic's API only accepts "user"/"assistant" roles in messages.
    clean_history = [
        {"role": m["role"], "content": m["content"]}
        for m in history
        if m.get("role") in ("user", "assistant")
    ]
    messages = clean_history + [{"role": "user", "content": user_message}]

    response = client.messages.create(
        model=MODEL,
        max_tokens=800,
        system=system_prompt,
        messages=messages,
    )

    text = "".join(block.text for block in response.content if block.type == "text")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"reply": text, "extracted": {}, "complete": False}


def call_plain(system_prompt: str, user_content: str, max_tokens: int = 500) -> str:
    """Plain-text call for stages that don't need structured extraction (Execute, Allocate)."""
    client = get_client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}],
    )
    return "".join(block.text for block in response.content if block.type == "text")
