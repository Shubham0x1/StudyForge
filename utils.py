import re
import io
import pypdf
from docx import Document


def clean_text(text: str) -> str:
    """
    Cleans extracted or transcribed text.
    """
    if not text:
        return ""

    # remove extra whitespace
    text = re.sub(r"\s+", " ", text)

    # remove common filler words
    text = re.sub(r"\b(um|uh|hmm|erm)\b", "", text, flags=re.IGNORECASE)

    return text.strip()


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from PDF bytes.
    """
    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    text = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text.append(page_text)

    return clean_text(" ".join(text))


def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extract text from DOCX bytes.
    """
    doc = Document(io.BytesIO(file_bytes))
    text = [para.text for para in doc.paragraphs if para.text.strip()]
    return clean_text(" ".join(text))
