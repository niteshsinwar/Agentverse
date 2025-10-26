"""
Document Chunking Module
Intelligent chunking with overlap and token awareness
"""
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    Language
)
from typing import List, Dict, Any
import tiktoken


class DocumentChunker:
    """Chunks documents intelligently for RAG retrieval"""

    # Code language mapping
    CODE_LANGUAGES = {
        'py': Language.PYTHON,
        'js': Language.JS,
        'ts': Language.TS,
        'java': Language.JAVA,
        'cpp': Language.CPP,
        'c': Language.C,
        'go': Language.GO,
        'rs': Language.RUST,
        'rb': Language.RUBY,
        'php': Language.PHP,
    }

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        model_name: str = "gpt-4"
    ):
        """
        Initialize chunker

        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap to preserve context
            model_name: For token counting
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except:
            self.encoding = tiktoken.get_encoding("cl100k_base")

        # General text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=self._token_length,
            separators=["\n\n", "\n", ". ", ", ", " ", ""]
        )

    def _token_length(self, text: str) -> int:
        """Count tokens instead of characters"""
        return len(self.encoding.encode(text))

    def chunk_text(self, text: str, file_type: str = "text") -> List[Dict[str, Any]]:
        """
        Chunk text with metadata

        Args:
            text: Extracted text content
            file_type: File extension (for code-aware chunking)

        Returns:
            List of chunk dicts with metadata
        """
        # Use code-aware splitter for code files
        if file_type in self.CODE_LANGUAGES:
            try:
                splitter = RecursiveCharacterTextSplitter.from_language(
                    language=self.CODE_LANGUAGES[file_type],
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap
                )
                chunks = splitter.split_text(text)
            except Exception as e:
                print(f"⚠️ Code-aware chunking failed for {file_type}: {e}, using default")
                chunks = self.text_splitter.split_text(text)
        else:
            chunks = self.text_splitter.split_text(text)

        # Add metadata to each chunk
        chunk_dicts = []
        for i, chunk in enumerate(chunks):
            chunk_dicts.append({
                "text": chunk,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "token_count": self._token_length(chunk)
            })

        return chunk_dicts

    def chunk_image_description(self, description: str) -> List[Dict[str, Any]]:
        """
        Chunk image description (usually small, may not need splitting)

        Args:
            description: Vision model description of image

        Returns:
            List with single chunk (images rarely need splitting)
        """
        # Images typically produce short descriptions, store as single chunk
        token_count = self._token_length(description)

        if token_count > self.chunk_size:
            # Rare case: very detailed image analysis
            chunks = self.text_splitter.split_text(description)
            return [
                {
                    "text": chunk,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "token_count": self._token_length(chunk)
                }
                for i, chunk in enumerate(chunks)
            ]
        else:
            # Common case: single chunk
            return [{
                "text": description,
                "chunk_index": 0,
                "total_chunks": 1,
                "token_count": token_count
            }]


# Global instance
document_chunker = DocumentChunker()
