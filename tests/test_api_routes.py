"""Integration tests for the /api/analyze-pdf endpoint."""
import io
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SAMPLE_PDF_TEXT = (
    "Work Package: Heavy Maintenance Visit\n"
    "Task 1: Inspect engine fan blades for wear and damage ATA 72\n"
    "Task 2: Replace landing gear actuator seals\n"
    "Task 3: Check avionics ILS receiver functionality\n"
    "Task 4: Lubricate flight control hinges and bearings\n"
)


def _make_fake_pdf_bytes() -> bytes:
    return b"%PDF-1.4 fake content"


def _patch_pdf_extraction(text: str):
    """Context manager that patches PdfReader to return controlled text."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = text
    mock_reader = MagicMock()
    mock_reader.pages = [mock_page]
    return patch("app.services.pdf_service.PdfReader", return_value=mock_reader)


class TestAnalyzePdfEndpoint:
    def test_valid_pdf_returns_200(self):
        with _patch_pdf_extraction(SAMPLE_PDF_TEXT):
            response = client.post(
                "/api/analyze-pdf",
                files={"file": ("workpackage.pdf", _make_fake_pdf_bytes(), "application/pdf")},
            )
        assert response.status_code == 200

    def test_response_has_required_keys(self):
        with _patch_pdf_extraction(SAMPLE_PDF_TEXT):
            response = client.post(
                "/api/analyze-pdf",
                files={"file": ("workpackage.pdf", _make_fake_pdf_bytes(), "application/pdf")},
            )
        data = response.json()
        assert "filename" in data
        assert "tasks_detected" in data
        assert "tasks" in data
        assert "daily_plan" in data
        assert "gantt" in data

    def test_tasks_are_enriched(self):
        with _patch_pdf_extraction(SAMPLE_PDF_TEXT):
            response = client.post(
                "/api/analyze-pdf",
                files={"file": ("workpackage.pdf", _make_fake_pdf_bytes(), "application/pdf")},
            )
        data = response.json()
        for task in data["tasks"]:
            assert "task_key" in task
            assert "risk_score" in task
            assert "manhours" in task
            assert "historical_avg_manhours" in task

    def test_tasks_detected_count_matches(self):
        with _patch_pdf_extraction(SAMPLE_PDF_TEXT):
            response = client.post(
                "/api/analyze-pdf",
                files={"file": ("workpackage.pdf", _make_fake_pdf_bytes(), "application/pdf")},
            )
        data = response.json()
        assert data["tasks_detected"] == len(data["tasks"])

    def test_gantt_entries_have_start_end_day(self):
        with _patch_pdf_extraction(SAMPLE_PDF_TEXT):
            response = client.post(
                "/api/analyze-pdf",
                files={"file": ("workpackage.pdf", _make_fake_pdf_bytes(), "application/pdf")},
            )
        data = response.json()
        for entry in data["gantt"]:
            assert "start_day" in entry
            assert "end_day" in entry
            assert entry["end_day"] >= entry["start_day"]

    def test_non_pdf_returns_400(self):
        response = client.post(
            "/api/analyze-pdf",
            files={"file": ("document.txt", b"some text", "text/plain")},
        )
        assert response.status_code == 400

    def test_empty_pdf_text_returns_422(self):
        with _patch_pdf_extraction(""):
            response = client.post(
                "/api/analyze-pdf",
                files={"file": ("empty.pdf", _make_fake_pdf_bytes(), "application/pdf")},
            )
        assert response.status_code == 422

    def test_filename_in_response(self):
        with _patch_pdf_extraction(SAMPLE_PDF_TEXT):
            response = client.post(
                "/api/analyze-pdf",
                files={"file": ("my_workpackage.pdf", _make_fake_pdf_bytes(), "application/pdf")},
            )
        data = response.json()
        assert data["filename"] == "my_workpackage.pdf"
