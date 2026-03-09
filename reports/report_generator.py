from io import BytesIO
from typing import Dict

from fpdf import FPDF


def _safe_text(text: str, chunk: int = 30) -> str:
    cleaned = str(text).replace("\n", " ").replace("\r", " ")
    words = []
    for token in cleaned.split(" "):
        if len(token) > chunk:
            parts = [token[i : i + chunk] for i in range(0, len(token), chunk)]
            words.append(" ".join(parts))
        else:
            words.append(token)
    return " ".join(words)


def build_weekly_pdf_report(username: str, metrics: Dict[str, str], summary_lines: Dict[str, str]) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, _safe_text("Weekly Circadian Health Report"), ln=True)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, _safe_text(f"User: {username}"), ln=True)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Key Metrics", ln=True)
    pdf.set_font("Helvetica", "", 11)
    for k, v in metrics.items():
        pdf.multi_cell(max(20, pdf.epw), 7, _safe_text(f"- {k}: {v}"))

    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Summary", ln=True)
    pdf.set_font("Helvetica", "", 11)
    for k, v in summary_lines.items():
        pdf.multi_cell(max(20, pdf.epw), 7, _safe_text(f"{k}: {v}"))

    out = pdf.output(dest="S")
    buff = BytesIO()
    if isinstance(out, str):
        buff.write(out.encode("latin-1", errors="replace"))
    else:
        buff.write(bytes(out))
    return buff.getvalue()
