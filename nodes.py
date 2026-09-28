from calculations import compute_goal_gaps, compute_net_worth, generate_budget
from llm_client import call_plain, call_stage_llm
from rag import retrieve_reframe


def _last_user_text(state: dict) -> str:
    for message in reversed(state.get("conversation_history") or []):
        if message.get("role") == "user":
            return message.get("content") or ""
    return ""


def _set_reply(state: dict, reply: str) -> None:
    state["last_reply"] = reply or ""
    state.setdefault("conversation_history", []).append(
        {"role": "assistant", "content": state["last_reply"]}
    )


DIAGNOSE_SYSTEM = """You are the "Diagnose" stage of a personal finance assistant \
built on the D.R.E.A.M. Wealth Framework.

Your job in this stage, ask ONE question at a time until you have collected ALL of:
- monthly income
- monthly expenses
- total loans and EMIs
- monthly savings & investments
- one dream with an approximate cost for EACH of: short term (0-2 years), \
medium term (3-7 years), long term (8+ years)

Be warm and non-judgmental — this is a safe space for the user to be honest \
about their numbers. Do not comment on whether their numbers are "good" or "bad".

Once you have every field above, set "complete" to true and include everything \
you've collected in "extracted", in this exact shape:
{
  "income": <number>,
  "expenses": <number>,
  "loans_emis": <number>,
  "savings_investments": <number>,
  "dreams": [
    {"term": "short", "description": "<str>", "cost": <number>},
    {"term": "medium", "description": "<str>", "cost": <number>},
    {"term": "long", "description": "<str>", "cost": <number>}
  ]
}

Respond with STRICT JSON ONLY, no markdown fences, no extra text, in this shape:
{"reply": "<what to say to the user next>", "extracted": {...fields confirmed so far, or {}...}, "complete": true|false}
"""


def diagnose_node(state: dict) -> dict:
    result = call_stage_llm(DIAGNOSE_SYSTEM, state.get("conversation_history", []))

    state.setdefault("financials", {})
    extracted = result.get("extracted", {}) or {}

    for key in ("income", "expenses", "loans_emis", "savings_investments"):
        if key in extracted:
            state["financials"][key] = extracted[key]
    if "dreams" in extracted:
        state["dreams"] = extracted["dreams"]

    _set_reply(state, result.get("reply", ""))

    if result.get("complete"):
        state["financials"]["net_worth"] = compute_net_worth(state["financials"])
        state["stage"] = "rewire"

    return state


REWIRE_SYSTEM_TEMPLATE = """You are the "Rewire" stage of a personal finance assistant.

Ask the user about a belief they hold about money that feels limiting. Once they \
share one, personalize the retrieved reframe below in your own words for their \
specific situation — do not invent an unrelated reframe.

Retrieved reframe to personalize: "{retrieved}"

After delivering one personalized reframe, set "complete" to true.

Respond with STRICT JSON ONLY, in this shape:
{{"reply": "<question or personalized reframe>", "extracted": {{"belief": "<str>", "reframe": "<str>"}} or {{}}, "complete": true|false}}
"""


def rewire_node(state: dict) -> dict:
    user_msg = _last_user_text(state)
    retrieved = retrieve_reframe(user_msg) if user_msg else ""
    system = REWIRE_SYSTEM_TEMPLATE.format(retrieved=retrieved)

    result = call_stage_llm(system, state.get("conversation_history", []))

    state.setdefault("beliefs", [])
    extracted = result.get("extracted", {}) or {}
    if extracted.get("belief"):
        state["beliefs"].append(
            {
                "belief": extracted["belief"],
                "reframe": extracted.get("reframe", retrieved),
            }
        )

    _set_reply(state, result.get("reply", ""))

    if result.get("complete"):
        state["stage"] = "execute"

    return state


EXECUTE_EXPLAIN_SYSTEM = (
    "Explain this budget breakdown to the user in plain, encouraging, "
    "jargon-free language. Keep it to 3-4 short sentences."
)


def execute_node(state: dict) -> dict:
    budget = generate_budget(state.get("financials", {}))
    state["budget"] = budget
    _set_reply(state, call_plain(EXECUTE_EXPLAIN_SYSTEM, f"Budget: {budget}"))
    state["stage"] = "allocate"
    return state


ALLOCATE_EXPLAIN_SYSTEM = (
    "Explain these goal-gap numbers in plain, jargon-free language. For each "
    "dream, say whether it's on track and, if not, how much more monthly "
    "saving is needed. Then suggest a rough split of the available monthly "
    "savings across an emergency fund, protection, and long-term growth. "
    "Keep it concise and encouraging."
)


def allocate_node(state: dict) -> dict:
    budget = state.get("budget", {})
    surplus = budget.get("surplus", 0)
    gaps = compute_goal_gaps(state.get("dreams", []), surplus)
    state["goal_gaps"] = gaps
    _set_reply(
        state,
        call_plain(
            ALLOCATE_EXPLAIN_SYSTEM,
            f"Goal gaps: {gaps}\nMonthly surplus available: {surplus}",
        ),
    )
    state["stage"] = "habits"
    return state


HABITS_SYSTEM = """You are the final stage of a personal finance assistant.

Based on the budget and goal gaps provided, generate 3 to 5 small, concrete, \
recurring money habits tailored to this user's situation (e.g. specific amounts, \
specific triggers like payday). Keep each habit to one short sentence.

Respond with STRICT JSON ONLY, in this shape:
{"reply": "<short message introducing the habits below>", "extracted": {"habits": ["<habit 1>", "<habit 2>", ...]}, "complete": true}
"""


def habits_node(state: dict) -> dict:
    context = f"Budget: {state.get('budget')}\nGoal gaps: {state.get('goal_gaps')}"
    result = call_stage_llm(HABITS_SYSTEM, [], extra_user=context)
    state["habits"] = (result.get("extracted", {}) or {}).get("habits", [])
    _set_reply(state, result.get("reply", ""))
    state["stage"] = "done"
    return state
