"""Document-related models."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field


class PageInfo(BaseModel):
    """Information about a single page in a document."""

    page_number: int = Field(..., ge=1, description="Page number (1-indexed)")
    text: str = Field(..., description="Extracted text from page")
    char_count: int = Field(..., ge=0, description="Number of characters")
    word_count: int = Field(..., ge=0, description="Number of words")
    has_images: bool = Field(default=False, description="Whether page contains images")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Page-specific metadata"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "page_number": 1,
                "text": "Introduction to machine learning...",
                "char_count": 2456,
                "word_count": 412,
                "has_images": True,
            }
        }


class ExtractionResult(BaseModel):
    """Result from document text extraction."""

    full_text: str = Field(..., description="Complete extracted text")
    page_count: int = Field(..., ge=0, description="Total number of pages")
    total_chars: int = Field(..., ge=0, description="Total character count")
    total_words: int = Field(..., ge=0, description="Total word count")
    pages: List[PageInfo] = Field(
        default_factory=list, description="Per-page information"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Extraction metadata"
    )
    extraction_method: Optional[str] = Field(
        default=None, description="Method used for extraction (pdfplumber, PyPDF2, etc.)"
    )
    quality_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Quality of extraction (0-1)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "full_text": "Complete document text...",
                "page_count": 10,
                "total_chars": 15000,
                "total_words": 2500,
                "extraction_method": "pdfplumber",
                "quality_score": 0.95,
            }
        }


class Document(BaseModel):
    """Source document (PDF, DOCX, TXT, URL, etc.)."""

    id: Optional[UUID] = Field(default=None, description="Unique identifier")
    title: str = Field(..., description="Document title")
    source_type: str = Field(
        ..., description="Type of source (pdf, docx, txt, url, etc.)"
    )
    file_path: Optional[str] = Field(default=None, description="Path to file if local")
    url: Optional[str] = Field(default=None, description="URL if web-based")
    full_text: Optional[str] = Field(default=None, description="Extracted full text")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Document metadata (author, year, etc.)"
    )
    uploaded_at: Optional[datetime] = Field(
        default=None, description="Upload timestamp"
    )
    processed_at: Optional[datetime] = Field(
        default=None, description="Processing completion timestamp"
    )
    extraction_result: Optional[ExtractionResult] = Field(
        default=None, description="Detailed extraction result"
    )

    class Config:
        json_encoders = {UUID: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "title": "Machine Learning Research Paper",
                "source_type": "pdf",
                "file_path": "/documents/ml_paper.pdf",
                "metadata": {
                    "author": "Smith et al.",
                    "year": 2023,
                    "journal": "Nature",
                },
            }
        }
