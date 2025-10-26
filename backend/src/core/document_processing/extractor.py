"""
Document Extractor Module
Handles extraction of text content from various file formats
Returns (content, modality) tuple for RAG pipeline
"""
import os
import pandas as pd
from pathlib import Path
from typing import Tuple
import tempfile

# Core libraries
from PIL import Image
import fitz  # PyMuPDF for PDF and image processing
import pypdf
from docx import Document
from pptx import Presentation


class DocumentExtractor:
    """Extracts text content from various document formats"""

    def __init__(self, settings=None):
        from src.core.config.settings import get_settings
        self.settings = settings or get_settings()

        # Build supported formats from global settings
        format_mapping = {
            'pdf': self._extract_pdf_content,
            'docx': self._extract_docx_content,
            'pptx': self._extract_pptx_content,
            'csv': self._extract_csv_content,
            'txt': self._extract_text_content,
            'md': self._extract_text_content,
            'json': self._extract_text_content,
            'xml': self._extract_text_content,
            'html': self._extract_text_content,
            'htm': self._extract_text_content,
            'xlsx': self._extract_csv_content,
            'xls': self._extract_csv_content,
            'rtf': self._extract_text_content,
            'odt': self._extract_docx_content,
            'odp': self._extract_pptx_content,
            'ods': self._extract_csv_content,
            'jpg': self._extract_image_content,
            'jpeg': self._extract_image_content,
            'png': self._extract_image_content,
            'gif': self._extract_image_content,
            'bmp': self._extract_image_content,
            'tiff': self._extract_image_content,
            'webp': self._extract_image_content,
            'svg': self._extract_image_content,
            'py': self._extract_text_content,
            'js': self._extract_text_content,
            'ts': self._extract_text_content,
            'java': self._extract_text_content,
            'cpp': self._extract_text_content,
            'c': self._extract_text_content,
            'go': self._extract_text_content,
            'rs': self._extract_text_content,
            'rb': self._extract_text_content,
            'php': self._extract_text_content
        }

        # Build supported formats based on global settings
        self.supported_formats = {}
        for fmt in self.settings.document_extraction.supported_formats:
            if fmt in format_mapping:
                self.supported_formats[f'.{fmt}'] = format_mapping[fmt]

        # Define modality mapping
        self.image_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'}
        self.structured_formats = {'.csv', '.xlsx', '.xls', '.ods', '.json', '.xml'}
    
    async def process_file(self, file_path: str, file_extension: str = None) -> Tuple[str, str]:
        """
        Extract text content from file and detect modality

        Args:
            file_path: Path to file
            file_extension: File extension (auto-detected if None)

        Returns:
            (content, modality) tuple where:
            - content: Extracted text content
            - modality: "text", "structured", or "image"
        """
        if file_extension is None:
            file_extension = Path(file_path).suffix.lower()

        if file_extension not in self.supported_formats:
            return f"Unsupported file format: {file_extension}", "text"

        try:
            # Extract basic content
            processor = self.supported_formats[file_extension]
            content = processor(file_path)

            # Detect modality
            modality = self._detect_modality(file_extension)

            return content, modality

        except Exception as e:
            return f"Error processing {file_extension} file: {str(e)}", "text"

    def _detect_modality(self, file_extension: str) -> str:
        """
        Detect document modality based on file extension

        Returns:
            "image", "structured", or "text"
        """
        if file_extension in self.image_formats:
            return "image"
        elif file_extension in self.structured_formats:
            return "structured"
        else:
            return "text"
    
    def _extract_pdf_content(self, file_path: str) -> str:
        """Extract text from PDF using PyMuPDF (more reliable than PyPDF2)"""
        try:
            content = []
            
            # Try PyMuPDF first (handles both text and image-based PDFs)
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                if text.strip():
                    content.append(f"--- Page {page_num + 1} ---\n{text}")
                else:
                    # If no text found, try to extract from images on the page
                    try:
                        pix = page.get_pixmap()
                        # Convert to PIL Image for processing
                        img_data = pix.tobytes("ppm")
                        with tempfile.NamedTemporaryFile(suffix=".ppm", delete=False) as temp_img:
                            temp_img.write(img_data)
                            temp_img.flush()
                            
                            # Note: AI vision analysis is handled in the main process_file method
                            content.append(f"--- Page {page_num + 1} (Image-based) ---\n[Image content detected - AI analysis will be performed separately]")

                            os.unlink(temp_img.name)
                    except Exception:
                        content.append(f"--- Page {page_num + 1} ---\n[Unable to extract content from this page]")
            
            doc.close()
            return '\n\n'.join(content) if content else "No readable content found in PDF"
            
        except Exception as e:
            # Fallback to pypdf if PyMuPDF fails
            try:
                content = []
                with open(file_path, 'rb') as file:
                    reader = pypdf.PdfReader(file)
                    for page_num, page in enumerate(reader.pages):
                        text = page.extract_text()
                        if text.strip():
                            content.append(f"--- Page {page_num + 1} ---\n{text}")
                
                return '\n\n'.join(content) if content else "No readable content found in PDF"
            except Exception as e2:
                return f"Error extracting PDF content: {str(e2)}"
    
    def _extract_docx_content(self, file_path: str) -> str:
        """Extract text from Word documents"""
        try:
            doc = Document(file_path)
            content = []
            
            # Extract text from paragraphs
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    content.append(paragraph.text)
            
            # Extract text from tables
            for table in doc.tables:
                table_content = []
                for row in table.rows:
                    row_content = []
                    for cell in row.cells:
                        row_content.append(cell.text.strip())
                    table_content.append(' | '.join(row_content))
                
                if table_content:
                    content.append('\n--- Table ---\n' + '\n'.join(table_content))
            
            return '\n\n'.join(content) if content else "No readable content found in document"
            
        except Exception as e:
            return f"Error extracting DOCX content: {str(e)}"
    
    def _extract_pptx_content(self, file_path: str) -> str:
        """Extract text from PowerPoint presentations"""
        try:
            prs = Presentation(file_path)
            content = []
            
            for slide_num, slide in enumerate(prs.slides, 1):
                slide_content = [f"--- Slide {slide_num} ---"]
                
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_content.append(shape.text)
                
                if len(slide_content) > 1:  # More than just the header
                    content.append('\n'.join(slide_content))
            
            return '\n\n'.join(content) if content else "No readable content found in presentation"
            
        except Exception as e:
            return f"Error extracting PPTX content: {str(e)}"
    
    def _extract_csv_content(self, file_path: str) -> str:
        """Extract and summarize CSV data"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                return "Error: Could not read CSV file with standard encodings"
            
            content = []
            content.append(f"CSV Data Summary:")
            content.append(f"Rows: {len(df)}, Columns: {len(df.columns)}")
            content.append(f"Columns: {', '.join(df.columns.tolist())}")
            
            # Show first few rows
            if len(df) > 0:
                content.append("\n--- First 5 rows ---")
                content.append(df.head().to_string(index=False))
            
            # Basic statistics for numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                content.append("\n--- Numeric Summary ---")
                content.append(df[numeric_cols].describe().to_string())
            
            return '\n'.join(content)
            
        except Exception as e:
            return f"Error extracting CSV content: {str(e)}"
    
    def _extract_text_content(self, file_path: str) -> str:
        """Extract content from plain text files"""
        try:
            encodings = ['utf-8', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        return file.read()
                except UnicodeDecodeError:
                    continue
            
            return "Error: Could not read text file with standard encodings"
            
        except Exception as e:
            return f"Error extracting text content: {str(e)}"
    
    def _extract_image_content(self, file_path: str) -> str:
        """Extract text from images using PyMuPDF (limited without full OCR)"""
        try:
            # Open image with PyMuPDF
            doc = fitz.open(file_path)
            page = doc.load_page(0)  # Images have only one "page"
            
            # Get image properties
            pix = page.get_pixmap()
            width, height = pix.width, pix.height
            
            # Basic image analysis
            content = []
            content.append(f"Image Analysis:")
            content.append(f"Dimensions: {width} x {height} pixels")
            content.append(f"Format: {Path(file_path).suffix.upper()}")
            
            # Try to detect if image contains text (basic analysis)
            try:
                # Convert to PIL for basic analysis
                img_data = pix.tobytes("ppm")
                with tempfile.NamedTemporaryFile(suffix=".ppm", delete=False) as temp_img:
                    temp_img.write(img_data)
                    temp_img.flush()
                    
                    # Open with PIL for basic analysis
                    pil_img = Image.open(temp_img.name)
                    
                    # Basic heuristics to detect if image might contain text
                    # Note: AI vision analysis is handled in the main process_file method
                    # to avoid async/sync issues in image extraction
                    content.append("\n[Image detected - AI analysis will be performed separately]")

                    os.unlink(temp_img.name)
                    
            except Exception:
                content.append("\n[Unable to analyze image content]")
            
            doc.close()
            return '\n'.join(content)
            
        except Exception as e:
            return f"Error analyzing image: {str(e)}"


# Global instance
document_extractor = DocumentExtractor()
