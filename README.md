# AircraftMaintenancePlanner
AI-powered aircraft maintenance planning system - PDF analysis, risk assessment, task scheduling, resource allocation

## Large PDF MVP flow

- `POST /api/analyze-pdf` still works for compatibility, but now streams uploads to disk before processing instead of reading the whole PDF into memory.
- Maximum supported upload size is 250 MB. Oversized, empty, and non-PDF uploads return clear HTTP errors.
- `POST /api/analyze-pdf/jobs` creates a background analysis job for large PDFs and returns a `job_id`.
- `GET /api/analyze-pdf/jobs/{job_id}` returns job status.
- `GET /api/analyze-pdf/jobs/{job_id}/result` returns the finished analysis result.
- Runtime uploads and job result files are stored under `app/data/uploads/` and `app/data/results/` and are ignored by git.
