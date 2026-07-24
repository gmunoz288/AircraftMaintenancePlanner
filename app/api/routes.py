from fastapi import APIRouter, UploadFile, File
from app.services.pdf_service import extract_text_from_pdf
from app.services.task_extraction_service import extract_tasks_from_text
from app.services.risk_service import score_task_risk
from app.services.scheduler_service import build_daily_plan, build_gantt

router = APIRouter()

@router.post("/analyze-pdf")
async def analyze_pdf(file: UploadFile = File(...)):
    text = await extract_text_from_pdf(file)
    tasks = extract_tasks_from_text(text)

    enriched = []
    for t in tasks:
        t["risk_score"] = score_task_risk(t)
        enriched.append(t)

    plan = build_daily_plan(enriched)
    gantt = build_gantt(plan)

    return {
        "filename": file.filename,
        "tasks_detected": len(enriched),
        "tasks": enriched,
        "daily_plan": plan,
        "gantt": gantt,
    }
