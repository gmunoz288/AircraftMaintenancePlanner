import io
from pypdf import PdfReader
from fastapi import UploadFile

async def extract_text_from_pdf(file: UploadFile) -> str:
    content = await file.read()
    reader = PdfReader(io.BytesIO(content))
    text_parts = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)
