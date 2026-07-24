"""Tests for PDF text extraction helper."""
import asyncio
import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import UploadFile


def run(coro):
    """Helper to run async functions in tests without pytest-asyncio."""
    return asyncio.new_event_loop().run_until_complete(coro)


def test_extract_text_returns_string():
    """extract_text_from_pdf should return a non-empty string for a valid PDF."""
    from app.services.pdf_service import extract_text_from_pdf

    mock_file = UploadFile(filename="workpackage.pdf", file=io.BytesIO(b"%PDF-1.4 fake"))

    with patch("app.services.pdf_service.PdfReader") as MockReader:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Inspect engine bearings"
        MockReader.return_value.pages = [mock_page]

        result = run(extract_text_from_pdf(mock_file))

    assert isinstance(result, str)
    assert "Inspect engine bearings" in result


def test_extract_text_joins_pages():
    """Multiple pages should be joined with newlines."""
    from app.services.pdf_service import extract_text_from_pdf

    mock_file = UploadFile(filename="workpackage.pdf", file=io.BytesIO(b"%PDF-1.4 fake"))

    with patch("app.services.pdf_service.PdfReader") as MockReader:
        page1 = MagicMock()
        page1.extract_text.return_value = "Page 1 content"
        page2 = MagicMock()
        page2.extract_text.return_value = "Page 2 content"
        MockReader.return_value.pages = [page1, page2]

        result = run(extract_text_from_pdf(mock_file))

    assert "Page 1 content" in result
    assert "Page 2 content" in result


def test_extract_text_handles_empty_pages():
    """Pages returning None should be treated as empty strings."""
    from app.services.pdf_service import extract_text_from_pdf

    mock_file = UploadFile(filename="workpackage.pdf", file=io.BytesIO(b"%PDF-1.4 fake"))

    with patch("app.services.pdf_service.PdfReader") as MockReader:
        page = MagicMock()
        page.extract_text.return_value = None
        MockReader.return_value.pages = [page]

        result = run(extract_text_from_pdf(mock_file))

    assert result == ""


def test_extract_text_from_pdf_path_uses_file_path(tmp_path):
    """File-path extraction should use the same PdfReader-based flow."""
    from app.services.pdf_service import extract_text_from_pdf_path

    pdf_path = tmp_path / "workpackage.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    with patch("app.services.pdf_service.PdfReader") as MockReader:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Path based extraction"
        MockReader.return_value.pages = [mock_page]

        result = extract_text_from_pdf_path(pdf_path)

    assert result == "Path based extraction"


def test_save_upload_to_disk_rejects_oversized_file(tmp_path):
    """Large uploads should be rejected without leaving partial files behind."""
    from app.services.pdf_service import UploadTooLargeError, save_upload_to_disk

    upload = UploadFile(filename="large.pdf", file=io.BytesIO(b"%PDF-1.4 too large"))

    with pytest.raises(UploadTooLargeError):
        run(save_upload_to_disk(upload, destination_dir=tmp_path, max_size_bytes=8))

    assert list(Path(tmp_path).iterdir()) == []
