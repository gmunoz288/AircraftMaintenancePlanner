from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.services.analysis_service import analyze_pdf_file
from app.services.job_service import create_job, get_job, get_job_result, process_job
from app.services.pdf_service import (
    InvalidUploadError,
    PdfProcessingError,
    UploadTooLargeError,
    delete_file,
    save_upload_to_disk,
)

router = APIRouter()


def _upload_exception(exc: Exception) -> HTTPException:
    if isinstance(exc, InvalidUploadError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, UploadTooLargeError):
        return HTTPException(status_code=413, detail=str(exc))
    if isinstance(exc, PdfProcessingError):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(status_code=500, detail="Unexpected PDF processing error.")


@router.post("/analyze-pdf")
async def analyze_pdf(file: UploadFile = File(...)):
    stored_upload = None

    try:
        stored_upload = await save_upload_to_disk(file)
        return analyze_pdf_file(stored_upload["filename"], stored_upload["path"])
    except (InvalidUploadError, UploadTooLargeError, PdfProcessingError) as exc:
        raise _upload_exception(exc) from exc
    finally:
        if stored_upload:
            delete_file(stored_upload["path"])


@router.post("/analyze-pdf/jobs", status_code=202)
async def create_pdf_analysis_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    try:
        stored_upload = await save_upload_to_disk(file)
        job = create_job(
            filename=stored_upload["filename"],
            upload_path=stored_upload["path"],
            size_bytes=stored_upload["size_bytes"],
        )
        background_tasks.add_task(process_job, job["job_id"])
        return job
    except (InvalidUploadError, UploadTooLargeError, PdfProcessingError) as exc:
        raise _upload_exception(exc) from exc


@router.get("/analyze-pdf/jobs/{job_id}")
def get_pdf_analysis_job(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


@router.get("/analyze-pdf/jobs/{job_id}/result")
def get_pdf_analysis_job_result(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job["status"] in {"queued", "processing"}:
        return JSONResponse(
            status_code=202,
            content={
                "job_id": job_id,
                "status": job["status"],
                "detail": "PDF analysis is still running.",
            },
        )
    if job["status"] == "failed":
        raise HTTPException(status_code=409, detail=job["error"] or "PDF analysis failed.")

    result = get_job_result(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Job result not found.")
    return result
