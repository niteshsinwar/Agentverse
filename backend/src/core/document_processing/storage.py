f"""
Document Storage and Retrieval System
Manages document uploads, storage, and agent access tracking
"""
import os
import json
import sqlite3
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import shutil


class DocumentStorage:
    """Manages document storage and metadata tracking"""
    
    def __init__(self, base_dir: str = "documents"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.uploads_dir = self.base_dir / "uploads"
        self.uploads_dir.mkdir(exist_ok=True)
        
        # Initialize SQLite database for metadata
        self.db_path = self.base_dir / "document_metadata.db"
        self._init_database()
    
    def _init_database(self):
        """Initialize document metadata database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                file_type TEXT,
                extension TEXT,
                group_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                sender_type TEXT NOT NULL,
                sender_id TEXT,
                upload_timestamp TEXT NOT NULL,
                extracted_content TEXT,
                content_summary TEXT,
                is_processed BOOLEAN DEFAULT 0,
                metadata TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_access (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                agent_id TEXT NOT NULL,
                group_id TEXT NOT NULL,
                access_timestamp TEXT NOT NULL,
                access_type TEXT NOT NULL,  -- 'upload', 'view', 'mention'
                FOREIGN KEY (document_id) REFERENCES documents (id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def store_document_metadata(
        self,
        document_id: str,
        filename: str,
        file_type: str,
        file_size: int,
        group_id: str,
        agent_id: str,
        modality: str,
        total_chunks: int,
        sender_type: str = "user",
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Store lightweight document metadata in SQLite (for UI)

        Args:
            document_id: Unique document identifier (used as file_path for now)
            filename: Original filename
            file_type: File extension
            file_size: File size in bytes
            group_id: Group ID
            agent_id: Target agent ID
            modality: "text", "structured", or "image"
            total_chunks: Number of chunks stored in vector DB
            sender_type: "user" or "agent"
            metadata: Additional metadata (JSON)

        Returns:
            document_id
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        upload_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metadata_json = json.dumps(metadata) if metadata else None

        # Map to existing schema
        cursor.execute("""
            INSERT INTO documents (
                filename, original_filename, file_path, file_size,
                file_type, extension, group_id, agent_id, 
                sender_type, sender_id, upload_timestamp, 
                extracted_content, content_summary, is_processed, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            filename,           # filename
            filename,           # original_filename
            document_id,        # file_path (using document_id as path)
            file_size,          # file_size
            file_type,          # file_type
            file_type,          # extension
            group_id,           # group_id
            agent_id,           # agent_id
            sender_type,        # sender_type
            None,               # sender_id
            upload_timestamp,   # upload_timestamp
            f"Modality: {modality}, Chunks: {total_chunks}",  # extracted_content
            None,               # content_summary
            1,                  # is_processed (set to 1 since we processed it)
            metadata_json       # metadata
        ))

        conn.commit()
        conn.close()

        return document_id
    
    def get_agent_documents(self, agent_id: str, group_id: str) -> List[Dict[str, Any]]:
        """Get all documents accessible to an agent in a specific group"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM documents 
            WHERE agent_id = ? AND group_id = ?
            ORDER BY upload_timestamp DESC
        """, (agent_id, group_id))
        
        columns = [description[0] for description in cursor.description]
        documents = []
        
        for row in cursor.fetchall():
            doc = dict(zip(columns, row))
            # Parse metadata JSON
            if doc['metadata']:
                doc['metadata'] = json.loads(doc['metadata'])
            documents.append(doc)
        
        conn.close()
        return documents
    
    def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [description[0] for description in cursor.description]
            doc = dict(zip(columns, row))
            if doc['metadata']:
                doc['metadata'] = json.loads(doc['metadata'])
            conn.close()
            return doc
        
        conn.close()
        return None
    
    def search_documents(self, agent_id: str, group_id: str, query: str) -> List[Dict[str, Any]]:
        """Search documents by content or filename"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM documents 
            WHERE agent_id = ? AND group_id = ? 
            AND (
                filename LIKE ? OR 
                original_filename LIKE ? OR 
                extracted_content LIKE ? OR 
                content_summary LIKE ?
            )
            ORDER BY upload_timestamp DESC
        """, (agent_id, group_id, f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))

        columns = [description[0] for description in cursor.description]
        documents = []
        
        for row in cursor.fetchall():
            doc = dict(zip(columns, row))
            if doc.get('metadata'):
                doc['metadata'] = json.loads(doc['metadata'])
            documents.append(doc)
        
        conn.close()
        return documents
    
    def log_document_access(self, document_id: str, agent_id: str, group_id: str, access_type: str):
        """Log when an agent accesses a document"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO document_access (document_id, agent_id, group_id, access_timestamp, access_type)
            VALUES (?, ?, ?, ?, ?)
        """, (document_id, agent_id, group_id, datetime.now().isoformat(), access_type))
        
        conn.commit()
        conn.close()
    
    def get_recent_documents(self, agent_id: str, group_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent documents for an agent"""
        documents = self.get_agent_documents(agent_id, group_id)
        return documents[:limit]
    
    def _get_file_type(self, extension: str) -> str:
        """Get human-readable file type"""
        ext = extension.lower().lstrip('.')
        type_map = {
            'pdf': 'PDF Document',
            'docx': 'Word Document',
            'pptx': 'PowerPoint Presentation',
            'csv': 'CSV Data',
            'txt': 'Text File',
            'jpg': 'JPEG Image',
            'jpeg': 'JPEG Image',
            'png': 'PNG Image',
            'gif': 'GIF Image'
        }
        return type_map.get(ext, f'{ext.upper()} File')


# Global instance
document_storage = DocumentStorage()
