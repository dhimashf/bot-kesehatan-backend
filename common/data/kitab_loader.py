# src/data/kitab_loader.py
import os
import fitz  # PyMuPDF
import logging
import re
from typing import List

logger = logging.getLogger(__name__)

class KitabLoader:
    def __init__(self):
        self.paragraphs: List[str] = []

    def load_pdf(self, file_path: str) -> List[str]:
        """Load a single .pdf file and return cleaned paragraphs (for psychology/health context)"""
        try:
            abs_path = os.path.abspath(file_path)
            if not os.path.exists(abs_path):
                logger.error(f"File {abs_path} not found")
                return []

            doc = fitz.open(abs_path)
            paragraphs = []
            for page in doc:
                text = page.get_text()
                for line in text.split('\n'):
                    cleaned = self.clean_text(line)
                    if cleaned:
                        paragraphs.append(cleaned)
            logger.info(f"Loaded {len(paragraphs)} paragraphs from {file_path}")
            self.paragraphs = paragraphs
            return paragraphs
        except Exception as e:
            logger.exception(f"Error loading {file_path}: {e}")
            return []

    def clean_text(self, text: str) -> str:
        """Normalize whitespace and trim"""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text).strip()

# singleton
kitab_loader = KitabLoader()
