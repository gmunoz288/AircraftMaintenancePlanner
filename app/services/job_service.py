import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4

from app import config
from app.services.analysis_service import analyze_pdf_file
from app.services.pdf_service import delete_file

_JOBS: dict[str, dict] = {}
_JOB_LOCK = Lock()


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _serialize_job(job: dict) -> dict:
    return {
        "job_id": job["job_id"],
        "filename": job["filename"],
        "size_bytes": job["size_bytes"],
        "status": job["status"],
        "error": job["error"],
        "created_at": job["created_at"],
        "updated_at": job["updated_at"],
        "completed_at": job["completed_at"],
        "result_available": Path(job["result_path"]).exists(),
    }


def create_job(filename: str, upload_path: str | Path, size_bytes: int) -> dict:
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    job_id = uuid4().hex
    now = _timestamp()
    job = {
        "job_id": job_id,
        "filename": filename,
        "size_bytes": size_bytes,
        "status": "queued",
        "error": None,
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
        "upload_path": str(upload_path),
        "result_path": str(config.RESULTS_DIR / f"{job_id}.json"),
    }

    with _JOB_LOCK:
        _JOBS[job_id] = job

    return _serialize_job(job)


def get_job(job_id: str) -> dict | None:
    with _JOB_LOCK:
        job = _JOBS.get(job_id)
        return _serialize_job(job) if job else None


def get_job_result(job_id: str) -> dict | None:
    with _JOB_LOCK:
        job = _JOBS.get(job_id)
        if not job:
            return None
        result_path = Path(job["result_path"])

    if not result_path.exists():
        return None

    return json.loads(result_path.read_text(encoding="utf-8"))


def process_job(job_id: str) -> None:
    with _JOB_LOCK:
        job = _JOBS.get(job_id)
        if not job:
            return
        job["status"] = "processing"
        job["updated_at"] = _timestamp()
        upload_path = Path(job["upload_path"])
        result_path = Path(job["result_path"])
        filename = job["filename"]

    try:
        result = analyze_pdf_file(filename, upload_path)
        result_path.write_text(json.dumps(result), encoding="utf-8")
        with _JOB_LOCK:
            job = _JOBS.get(job_id)
            if job:
                job["status"] = "completed"
                job["error"] = None
                job["updated_at"] = _timestamp()
                job["completed_at"] = job["updated_at"]
    except Exception as exc:
        with _JOB_LOCK:
            job = _JOBS.get(job_id)
            if job:
                job["status"] = "failed"
                job["error"] = str(exc) or "PDF analysis failed."
                job["updated_at"] = _timestamp()
                job["completed_at"] = job["updated_at"]
    finally:
        delete_file(upload_path)
