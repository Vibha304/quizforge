"""
Document parser for PDF (PyMuPDF) and DOCX (python-docx).
Supports heading extraction and text extraction.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import logging
import os

logger = logging.getLogger(__name__)


@dataclass
class Section:
    """Represents a section/heading in the document."""
    title: str
    level: int  # 1 = unit/chapter, 2 = section, 3 = subsection
    content: str  # text under this heading
    page_number: int = 0


@dataclass
class ParsedDocument:
    """Result of parsing a document."""
    raw_text: str
    sections: List[Section] = field(default_factory=list)
    page_count: int = 0
    is_scanned: bool = False
    error: Optional[str] = None

    @property
    def word_count(self) -> int:
        return len(self.raw_text.split())


def parse_document(file_path: str) -> ParsedDocument:
    """
    Parse a PDF or DOCX document.

    Args:
        file_path: Path to the file to parse.

    Returns:
        ParsedDocument with raw_text, sections, and metadata.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return _parse_pdf(file_path)
    elif ext in (".docx", ".doc"):
        return _parse_docx(file_path)
    else:
        return ParsedDocument(
            raw_text="",
            error=f"Unsupported file type: {ext}. Only PDF and DOCX are supported.",
        )


def _parse_pdf(file_path: str) -> ParsedDocument:
    """Parse a PDF file using PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(file_path)
        page_count = len(doc)
        all_text = []
        sections = []
        current_section: Optional[Section] = None
        current_content = []

        for page_num, page in enumerate(doc):
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if block.get("type") != 0:  # Only text blocks
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if not text:
                            continue
                        font_size = span.get("size", 12)
                        flags = span.get("flags", 0)
                        is_bold = bool(flags & 16)

                        # Detect headings by font size
                        level = _detect_heading_level(font_size, is_bold)
                        if level > 0:
                            # Save previous section
                            if current_section:
                                current_section.content = " ".join(current_content).strip()
                                sections.append(current_section)
                                current_content = []
                            current_section = Section(
                                title=text,
                                level=level,
                                content="",
                                page_number=page_num + 1,
                            )
                        else:
                            current_content.append(text)
                        all_text.append(text)

        # Save last section
        if current_section:
            current_section.content = " ".join(current_content).strip()
            sections.append(current_section)

        raw_text = "\n".join(all_text)

        # Detect scanned PDF (very little text per page)
        avg_chars_per_page = len(raw_text) / max(page_count, 1)
        is_scanned = avg_chars_per_page < 50

        if is_scanned:
            return ParsedDocument(
                raw_text=raw_text,
                sections=sections,
                page_count=page_count,
                is_scanned=True,
                error="This appears to be a scanned PDF. Text extraction may be incomplete. Consider using OCR.",
            )

        doc.close()
        return ParsedDocument(
            raw_text=raw_text,
            sections=sections,
            page_count=page_count,
        )
    except ImportError:
        return ParsedDocument(
            raw_text="",
            error="PyMuPDF (fitz) not installed. Run: pip install pymupdf",
        )
    except Exception as e:
        logger.error(f"PDF parsing error: {e}")
        return ParsedDocument(raw_text="", error=f"PDF parsing failed: {str(e)}")


def _parse_docx(file_path: str) -> ParsedDocument:
    """Parse a DOCX file using python-docx."""
    try:
        from docx import Document as DocxDocument

        doc = DocxDocument(file_path)
        all_text = []
        sections = []
        current_section: Optional[Section] = None
        current_content = []

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            style_name = para.style.name if para.style else ""
            level = _detect_heading_level_docx(style_name)

            if level > 0:
                if current_section:
                    current_section.content = " ".join(current_content).strip()
                    sections.append(current_section)
                    current_content = []
                current_section = Section(title=text, level=level, content="")
            else:
                current_content.append(text)
            all_text.append(text)

        if current_section:
            current_section.content = " ".join(current_content).strip()
            sections.append(current_section)

        raw_text = "\n".join(all_text)
        return ParsedDocument(
            raw_text=raw_text,
            sections=sections,
            page_count=len(doc.sections),
        )
    except ImportError:
        return ParsedDocument(
            raw_text="",
            error="python-docx not installed. Run: pip install python-docx",
        )
    except Exception as e:
        logger.error(f"DOCX parsing error: {e}")
        return ParsedDocument(raw_text="", error=f"DOCX parsing failed: {str(e)}")


def _detect_heading_level(font_size: float, is_bold: bool) -> int:
    """Determine heading level from font size."""
    if font_size >= 18:
        return 1  # Unit/Chapter heading
    elif font_size >= 14:
        return 2  # Section heading
    elif font_size >= 12 and is_bold:
        return 3  # Subsection heading
    return 0  # Body text


def _detect_heading_level_docx(style_name: str) -> int:
    """Determine heading level from DOCX style name."""
    if not style_name:
        return 0
    lower = style_name.lower()
    if "heading 1" in lower or "title" in lower:
        return 1
    elif "heading 2" in lower:
        return 2
    elif "heading 3" in lower or "heading 4" in lower:
        return 3
    return 0
