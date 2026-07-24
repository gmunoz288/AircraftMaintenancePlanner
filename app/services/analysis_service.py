from pathlib import Path

from app.services.enrichment_service import enrich_tasks
from app.services.pdf_service import PdfProcessingError, extract_text_from_pdf_path
from app.services.risk_service import score_task_risk
from app.services.scheduler_service import build_daily_plan, build_gantt
from app.services.task_extraction_service import extract_tasks_from_text


def analyze_pdf_file(filename: str, pdf_path: str | Path) -> dict:
    text = extract_text_from_pdf_path(pdf_path)
    if not text.strip():
        raise PdfProcessingError("Could not extract text from the uploaded PDF.")

    tasks = extract_tasks_from_text(text)
    tasks = enrich_tasks(tasks)

    for task in tasks:
        task["risk_score"] = score_task_risk(task)

    plan = build_daily_plan(tasks)
    gantt = build_gantt(plan)

    return {
        "filename": filename,
        "tasks_detected": len(tasks),
        "tasks": tasks,
        "daily_plan": plan,
        "gantt": gantt,
    }
