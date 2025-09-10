"""
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
                sender_type TEXT NOT NULL,  -- 'user' or 'agent'
                sender_id TEXT,
                upload_timestamp TEXT NOT NULL,
                extracted_content TEXT,
                content_summary TEXT,
                is_processed BOOLEAN DEFAULT 0,
                metadata TEXT  -- JSON string for additional metadata
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
    
    def store_document(self, 
                      file_path: str, 
                      original_filename: str,
                      group_id: str, 
                      agent_id: str,
                      sender_type: str = "user",
                      sender_id: Optional[str] = None,
                      extracted_content: Optional[str] = None,
                      content_summary: Optional[str] = None,
                      metadata: Optional[Dict] = None) -> str:
        """Store document and return document ID"""
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = Path(original_filename).suffix
        unique_filename = f"{timestamp}_{agent_id}_{group_id}_{original_filename}"
        
        # Create agent-specific directory
        agent_dir = self.uploads_dir / group_id / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy file to permanent storage
        stored_path = agent_dir / unique_filename
        shutil.copy2(file_path, stored_path)
        
        # Store metadata in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO documents (
                filename, original_filename, file_path, file_size, file_type, extension,
                group_id, agent_id, sender_type, sender_id, upload_timestamp,
                extracted_content, content_summary, is_processed, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            unique_filename,
            original_filename,
            str(stored_path),
            stored_path.stat().st_size,
            self._get_file_type(file_ext),
            file_ext.lstrip('.'),
            group_id,
            agent_id,
            sender_type,
            sender_id,
            datetime.now().isoformat(),
            extracted_content,
            content_summary,
            1 if extracted_content else 0,
            json.dumps(metadata) if metadata else None
        ))
        
        document_id = cursor.lastrowid
        
        # Log access
        cursor.execute("""
            INSERT INTO document_access (document_id, agent_id, group_id, access_timestamp, access_type)
            VALUES (?, ?, ?, ?, ?)
        """, (document_id, agent_id, group_id, datetime.now().isoformat(), 'upload'))
        
        conn.commit()
        conn.close()
        
        return str(document_id)
    
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
                original_filename LIKE ? OR 
                extracted_content LIKE ? OR 
                content_summary LIKE ?
            )
            ORDER BY upload_timestamp DESC
        """, (agent_id, group_id, f"%{query}%", f"%{query}%", f"%{query}%"))
        
        columns = [description[0] for description in cursor.description]
        documents = []
        
        for row in cursor.fetchall():
            doc = dict(zip(columns, row))
            if doc['metadata']:
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
