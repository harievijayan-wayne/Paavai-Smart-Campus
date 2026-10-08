import os
from typing import List, Dict, Any
from app.core.logging import logger


class DocumentLoader:
    """
    Extracts text and page metadata from supported document formats: PDF, DOCX, and TXT.
    """

    @staticmethod
    def extract_text(file_path: str, file_type: str) -> List[Dict[str, Any]]:
        """
        Extract text from file.
        Returns a list of page/segment dictionaries:
        [{"page": 1, "text": "..."}]
        """
        ext = file_type.upper().strip().lstrip(".")

        if ext == "PDF":
            return DocumentLoader._extract_pdf(file_path)
        elif ext in ["DOCX", "DOC"]:
            return DocumentLoader._extract_docx(file_path)
        elif ext == "TXT":
            return DocumentLoader._extract_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_type}. Supported: PDF, DOCX, TXT")

    @staticmethod
    def _extract_pdf(file_path: str) -> List[Dict[str, Any]]:
        pages_content = []
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            for idx, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                if text.strip():
                    pages_content.append({"page": idx, "text": text.strip()})
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {str(e)}")
            raise e
        return pages_content

    @staticmethod
    def _extract_docx(file_path: str) -> List[Dict[str, Any]]:
        pages_content = []
        try:
            import docx
            doc = docx.Document(file_path)
            full_text = []
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text.strip())
            
            # DOCX does not have native page boundaries; treat as single or section-based
            joined = "\n\n".join(full_text)
            if joined.strip():
                pages_content.append({"page": 1, "text": joined})
        except Exception as e:
            logger.error(f"Error reading DOCX {file_path}: {str(e)}")
            raise e
        return pages_content

    @staticmethod
    def _extract_txt(file_path: str) -> List[Dict[str, Any]]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            if text.strip():
                return [{"page": 1, "text": text.strip()}]
            return []
        except Exception as e:
            logger.error(f"Error reading TXT {file_path}: {str(e)}")
            raise e
