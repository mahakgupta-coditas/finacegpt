from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.services.chunker import chunk_paragraphs
from app.services.embeddings import store_document_with_embeddings
import fitz  # PyMuPDF
from docx import Document as DocxDocument
import csv
import io

def process_uploaded_document(file: UploadFile, db: Session):
    filename = file.filename.lower()

    if not (filename.endswith(".txt") or filename.endswith(".pdf") or filename.endswith(".docx") or filename.endswith(".csv")):
        raise ValueError("Only .txt, .pdf, .docx, and .csv files are supported.")

    # Read file content
    content = file.file.read()

    if filename.endswith(".txt"):
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("Unable to decode .txt file. Ensure it is UTF-8 encoded.")

    elif filename.endswith(".pdf"):
        try:
            with fitz.open(stream=content, filetype="pdf") as doc:
                text = "\n".join([page.get_text() for page in doc])
        except Exception as e:
            raise RuntimeError(f"Failed to read PDF: {str(e)}")

    elif filename.endswith(".docx"):
        try:
            doc = DocxDocument(io.BytesIO(content))
            text = "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            raise RuntimeError(f"Failed to read DOCX: {str(e)}")

    elif filename.endswith(".csv"):
        try:
            decoded = content.decode("utf-8")
            reader = csv.reader(io.StringIO(decoded))
            text = "\n".join([", ".join(row) for row in reader])
        except Exception as e:
            raise RuntimeError(f"Failed to read CSV: {str(e)}")

    # Process and store
    chunks = chunk_paragraphs(text)
    document = store_document_with_embeddings(db, file.filename, chunks)
    return document
