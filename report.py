import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


def report_file_path(user_id: str) -> str:
    return os.path.join(REPORTS_DIR, f"{user_id}_summary.pdf")


def generate_report(user_id: str, state: dict) -> str:
    path = report_file_path(user_id)
    doc = SimpleDocTemplate(path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Your Money Clarity Report", styles["Title"]))
    story.append(Spacer(1, 16))

    # --- Current reality -----------------------------------------------
    financials = state.get("financials", {})
    story.append(Paragraph("Your Current Reality", styles["Heading2"]))
    for label, key in [
        ("Monthly income", "income"),
        ("Monthly expenses", "expenses"),
        ("Loans & EMIs", "loans_emis"),
        ("Savings & investments", "savings_investments"),
        ("Net worth", "net_worth"),
    ]:
        story.append(Paragraph(f"{label}: {financials.get(key, 'N/A')}", styles["Normal"]))
    story.append(Spacer(1, 12))

    # --- Dreams & gaps ----------------------------------------------------
    story.append(Paragraph("Your Dreams & Goal Gaps", styles["Heading2"]))
    gaps = state.get("goal_gaps", [])
    if gaps:
        data = [["Dream", "Required monthly saving", "Gap", "On track?"]]
        for g in gaps:
            data.append(
                [
                    g.get("dream", ""),
                    str(g.get("required_monthly_saving", "")),
                    str(g.get("gap", "")),
                    "Yes" if g.get("on_track") else "No",
                ]
            )
        table = Table(data, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        story.append(table)
    else:
        story.append(Paragraph("No dreams recorded yet.", styles["Normal"]))
    story.append(Spacer(1, 12))

    # --- Budget -------------------------------------------------------
    story.append(Paragraph("Your Budget", styles["Heading2"]))
    budget = state.get("budget", {})
    for label, key in [
        ("Income", "income"),
        ("Expenses", "expenses"),
        ("Surplus", "surplus"),
        ("Needs (50%)", "needs"),
        ("Wants (30%)", "wants"),
        ("Savings (20%)", "savings"),
    ]:
        story.append(Paragraph(f"{label}: {budget.get(key, 'N/A')}", styles["Normal"]))
    story.append(Spacer(1, 12))

    # --- Money beliefs --------------------------------------------------
    beliefs = state.get("beliefs", [])
    if beliefs:
        story.append(Paragraph("Money Mindset", styles["Heading2"]))
        for b in beliefs:
            story.append(Paragraph(f"Belief: {b.get('belief', '')}", styles["Normal"]))
            story.append(Paragraph(f"Reframe: {b.get('reframe', '')}", styles["Normal"]))
            story.append(Spacer(1, 6))

    # --- Habits -------------------------------------------------------
    story.append(Paragraph("Your Money Habits", styles["Heading2"]))
    habits = state.get("habits", [])
    if habits:
        for h in habits:
            story.append(Paragraph(f"\u2022 {h}", styles["Normal"]))
    else:
        story.append(Paragraph("No habits generated yet.", styles["Normal"]))

    doc.build(story)
    return path
