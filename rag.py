"""
Stand-in retrieval for the Rewire stage.

This uses simple keyword overlap over a small hardcoded corpus so the project
runs with zero extra infrastructure. Swap `retrieve_reframe` for a real vector
store (Chroma, pgvector, etc.) once you have a larger content library —
the rest of the app doesn't need to change.
"""

MINDSET_CORPUS = [
    {
        "belief": "I will never be good with money",
        "reframe": (
            "Financial skill is learned, not innate. Every time you track a "
            "number or close a gap, you're building that skill — you're not "
            "failing to have a talent you were supposed to be born with."
        ),
    },
    {
        "belief": "Money is the root of stress and conflict in my life",
        "reframe": (
            "Money itself usually isn't the source of the stress — an unclear "
            "system is. A concrete plan turns money from a source of anxiety "
            "into something you can actually see and control."
        ),
    },
    {
        "belief": "I do not earn enough to save or invest",
        "reframe": (
            "Saving is a habit of proportion, not a fixed amount. Even a small, "
            "consistent percentage compounds into real progress — the habit "
            "matters more right now than the size of it."
        ),
    },
    {
        "belief": "Talking about money is shameful or impolite",
        "reframe": (
            "Avoiding the topic doesn't protect you from financial stress — it "
            "just delays clarity. Naming your numbers plainly is the first "
            "step to changing them."
        ),
    },
    {
        "belief": "I am behind compared to where I should be at my age",
        "reframe": (
            "Comparing your timeline to an imagined 'should' ignores your own "
            "starting point. The only useful comparison is where you are today "
            "versus where you were six months ago."
        ),
    },
    {
        "belief": "Debt means I have failed",
        "reframe": (
            "Debt is a financial tool that went unmanaged, not a verdict on "
            "your character. The task now is a payoff plan, not self-punishment."
        ),
    },
]


def retrieve_reframe(user_text: str) -> str:
    """Return the corpus entry whose belief shares the most words with user_text."""
    user_words = set(user_text.lower().split())
    best_score = -1
    best_entry = MINDSET_CORPUS[0]

    for entry in MINDSET_CORPUS:
        entry_words = set(entry["belief"].lower().split())
        score = len(user_words & entry_words)
        if score > best_score:
            best_score = score
            best_entry = entry

    return best_entry["reframe"]
