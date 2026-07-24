import re
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from fastapi import UploadFile
from pypdf import PdfReader

from app import config


class InvalidUploadError(ValueError):
    pass


class UploadTooLargeError(ValueError):
    pass


class PdfProcessingError(ValueError):
    pass


def _safe_filename(filename: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(filename).name)
    return sanitized or f"upload-{uuid4().hex}.pdf"


def _format_size(size_bytes: int) -> str:
    size_mb = size_bytes / (1024 * 1024)
    return f"{size_mb:.0f} MB" if size_mb.is_integer() else f"{size_mb:.1f} MB"


def delete_file(path: str | Path | None) -> None:
    if path:
        Path(path).unlink(missing_ok=True)


def extract_text_from_pdf_stream(stream: BinaryIO) -> str:
    try:
        stream.seek(0)
        reader = PdfReader(stream)
    except Exception as exc:
        raise PdfProcessingError("Could not read the uploaded PDF.") from exc

    try:
        text_parts = []
        for page in reader.pages:
            text_parts.append(page.extract_text() or "")
    except Exception as exc:
        raise PdfProcessingError("Could not extract text from the uploaded PDF.") from exc

    return "\n".join(text_parts)


def extract_text_from_pdf_path(pdf_path: str | Path) -> str:
    with Path(pdf_path).open("rb") as pdf_stream:
        return extract_text_from_pdf_stream(pdf_stream)


async def extract_text_from_pdf(file: UploadFile) -> str:
    await file.seek(0)
    return extract_text_from_pdf_stream(file.file)


async def save_upload_to_disk(
    file: UploadFile,
    destination_dir: str | Path | None = None,
    max_size_bytes: int | None = None,
) -> dict:
    filename = Path(file.filename or "").name
    if not filename or not filename.lower().endswith(".pdf"):
        raise InvalidUploadError("Only PDF files are supported.")

    destination = Path(destination_dir or config.UPLOAD_DIR)
    destination.mkdir(parents=True, exist_ok=True)

    limit = max_size_bytes if max_size_bytes is not None else config.MAX_UPLOAD_SIZE_BYTES
    stored_path = destination / f"{uuid4().hex}-{_safe_filename(filename)}"
    size_bytes = 0

    try:
        with stored_path.open("wb") as output_file:
            while True:
                chunk = await file.read(config.UPLOAD_CHUNK_SIZE_BYTES)
                if not chunk:
                    break
                size_bytes += len(chunk)
                if size_bytes > limit:
                    raise UploadTooLargeError(
                        f"Uploaded file exceeds the maximum allowed size of {_format_size(limit)}."
                    )
                output_file.write(chunk)
    except Exception:
        delete_file(stored_path)
        await file.close()
        raise

    await file.close()

    if size_bytes == 0:
        delete_file(stored_path)
        raise InvalidUploadError("Uploaded file is empty.")

    return {
        "filename": filename,
        "path": stored_path,
        "size_bytes": size_bytes,
    }
