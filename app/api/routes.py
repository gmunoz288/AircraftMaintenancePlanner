from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.enrichment_service import enrich_tasks
from app.services.pdf_service import extract_text_from_pdf
from app.services.risk_service import score_task_risk
from app.services.scheduler_service import build_daily_plan, build_gantt
from app.services.task_extraction_service import extract_tasks_from_text

router = APIRouter()


@router.post("/analyze-pdf")
async def analyze_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    text = await extract_text_from_pdf(file)
    if not text.strip():
        raise HTTPException(status_code=422, detail="Could not extract text from the uploaded PDF.")

    # 1. Extract raw tasks from PDF text
    tasks = extract_tasks_from_text(text)

    # 2. Enrich with historical data (manhours, resources, risk_factor)
    tasks = enrich_tasks(tasks)

    # 3. Score risk using enriched task data
    for task in tasks:
        task["risk_score"] = score_task_risk(task)

    # 4. Build daily plan and Gantt
    plan = build_daily_plan(tasks)
    gantt = build_gantt(plan)

    return {
        "filename": file.filename,
        "tasks_detected": len(tasks),
        "tasks": tasks,
        "daily_plan": plan,
        "gantt": gantt,
    }
