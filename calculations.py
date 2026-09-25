"""
All financial math lives here, in plain Python — never delegated to the LLM.
The model explains these numbers to the user; it never computes them.
"""

TERM_YEARS = {"short": 1.5, "medium": 5, "long": 10}


def compute_net_worth(financials: dict) -> float:
    savings = financials.get("savings_investments", 0) or 0
    loans = financials.get("loans_emis", 0) or 0
    return round(savings - loans, 2)


def compute_required_monthly_saving(cost: float, years: float, annual_return: float = 0.08) -> float:
    """
    Required monthly saving to reach `cost` in `years`, assuming `annual_return`
    is earned on the growing balance (future value of an ordinary annuity, solved
    for the payment). Falls back to a flat division if years <= 0.
    """
    if years <= 0:
        return round(cost, 2)

    months = years * 12
    monthly_return = annual_return / 12

    if monthly_return == 0:
        return round(cost / months, 2)

    payment = cost * monthly_return / ((1 + monthly_return) ** months - 1)
    return round(payment, 2)


def compute_goal_gaps(dreams: list, monthly_surplus: float) -> list:
    gaps = []
    for dream in dreams:
        term = dream.get("term", "medium")
        years = TERM_YEARS.get(term, 5)
        cost = dream.get("cost", 0) or 0
        required = compute_required_monthly_saving(cost, years)
        gap = max(round(required - monthly_surplus, 2), 0)
        gaps.append(
            {
                "dream": dream.get("description", "Unnamed dream"),
                "term": term,
                "cost": cost,
                "required_monthly_saving": required,
                "gap": gap,
                "on_track": gap <= 0,
            }
        )
    return gaps


def generate_budget(financials: dict) -> dict:
    income = financials.get("income", 0) or 0
    expenses = financials.get("expenses", 0) or 0
    surplus = round(income - expenses, 2)
    return {
        "income": income,
        "expenses": expenses,
        "surplus": surplus,
        "needs": round(income * 0.5, 2),
        "wants": round(income * 0.3, 2),
        "savings": round(income * 0.2, 2),
    }
