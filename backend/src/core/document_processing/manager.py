"""
Document Manager - Integrates processing and storage
Handles the complete document lifecycle
"""
import tempfile
from typing import Dict, Any, Optional, List, Tuple
from .processor import DocumentProcessor
from .storage import DocumentStorage, document_storage
import yaml
from pathlib import Path


class DocumentManager:
    """Manages complete document workflow: upload -> process -> store -> retrieve"""
    
    def __init__(self):
        self.processor = DocumentProcessor()
        self.storage = document_storage
        self._load_agent_configs()
    
    def _load_agent_configs(self):
        """Load agent document access configurations"""
        self.agent_configs = {}
        agents_dir = Path("agent_store")

        for agent_folder in agents_dir.iterdir():
            if agent_folder.is_dir():
                config_file = agent_folder / "agent.yaml"
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        config = yaml.safe_load(f)
                        self.agent_configs[agent_folder.name] = config
    
    def can_agent_process_file(self, agent_id: str, file_extension: str, file_size_mb: float) -> Tuple[bool, str]:
        """Check if agent can process this file type"""
        config = self.agent_configs.get(agent_id, {})
        doc_access = config.get('document_access', {})
        
        if not doc_access.get('enabled', False):
            return False, f"Agent {agent_id} doesn't have document processing enabled"
        
        # Check file size
        max_size = doc_access.get('max_file_size_mb', 10)
        if file_size_mb > max_size:
            return False, f"File size ({file_size_mb:.1f}MB) exceeds limit ({max_size}MB)"
        
        # Check supported formats (remove dot from extension for comparison)
        supported_formats = doc_access.get('supported_formats', [])
        file_ext_no_dot = file_extension.lower().lstrip('.')
        if file_ext_no_dot not in [fmt.lower() for fmt in supported_formats]:
            return False, f"File type '{file_extension}' not supported. Supported: {', '.join(supported_formats)}"
        
        return True, "File can be processed"
    
    def process_and_store_document(self, 
                                 uploaded_file,
                                 group_id: str,
                                 agent_id: str,
                                 sender_type: str = "user",
                                 sender_id: Optional[str] = None) -> Dict[str, Any]:
        """Process uploaded file and store with metadata"""
        
        try:
            # Handle different types of file inputs from Gradio
            if isinstance(uploaded_file, str):
                # uploaded_file is a file path
                temp_path = uploaded_file
                file_name = Path(uploaded_file).name
                file_size_mb = Path(uploaded_file).stat().st_size / (1024 * 1024)
            else:
                # uploaded_file is a file-like object
                file_name = getattr(uploaded_file, 'name', 'unknown_file')
                file_size_mb = getattr(uploaded_file, 'size', 0) / (1024 * 1024) if hasattr(uploaded_file, 'size') else 0
                
                # Save to temporary file for processing
                with tempfile.NamedTemporaryFile(suffix=Path(file_name).suffix, delete=False) as temp_file:
                    if hasattr(uploaded_file, 'read'):
                        temp_file.write(uploaded_file.read())
                    else:
                        # If it's not a file object, try to read it as bytes
                        temp_file.write(uploaded_file)
                    temp_path = temp_file.name
            
            # Get file info
            file_extension = Path(file_name).suffix
            
            # Check agent permissions
            can_process, message = self.can_agent_process_file(agent_id, file_extension, file_size_mb)
            if not can_process:
                return {
                    'success': False,
                    'error': message,
                    'document_id': None
                }
            
            # Process document content
            agent_config = self.agent_configs.get(agent_id, {})
            ai_extraction = agent_config.get('document_access', {}).get('ai_extraction', {})
            
            extracted_content = ""
            content_summary = ""
            
            if ai_extraction.get('enabled', False):
                try:
                    # Use AI analysis for better content extraction
                    extracted_content = self.processor.process_file(
                        temp_path, 
                        file_extension, 
                        use_ai_analysis=True
                    )
                    if extracted_content and ai_extraction.get('generate_summary', False):
                        # The AI analysis already includes comprehensive analysis
                        # but we can generate a shorter summary if needed
                        content_summary = self._generate_summary(extracted_content, max_length=300)
                except Exception as e:
                    extracted_content = f"Error extracting content: {str(e)}"
            
            # Store document
            document_id = self.storage.store_document(
                file_path=temp_path,
                original_filename=file_name,
                group_id=group_id,
                agent_id=agent_id,
                sender_type=sender_type,
                sender_id=sender_id,
                extracted_content=extracted_content,
                content_summary=content_summary,
                metadata={
                    'file_size_mb': file_size_mb,
                    'processing_enabled': ai_extraction.get('enabled', False),
                    'upload_source': 'chat_interface'
                }
            )
            
            # Clean up temp file if it was created by us
            if not isinstance(uploaded_file, str):
                Path(temp_path).unlink()
            
            return {
                'success': True,
                'document_id': document_id,
                'extracted_content': extracted_content,
                'content_summary': content_summary,
                'message': f"Document '{file_name}' processed and stored successfully"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error processing document: {str(e)}",
                'document_id': None
            }
    
    def get_agent_document_context(self, agent_id: str, group_id: str, query: Optional[str] = None) -> str:
        """Get document context for agent conversation - includes full content for LLM processing"""
        
        if query:
            # Search for specific documents
            documents = self.storage.search_documents(agent_id, group_id, query)
        else:
            # Get recent documents
            documents = self.storage.get_recent_documents(agent_id, group_id, limit=5)
        
        if not documents:
            return "No documents found for this agent in the current group."
        
        context_parts = ["📄 **Available Documents with Full Content for Analysis:**\n"]
        
        for doc in documents:
            doc_info = [
                f"## 📄 **{doc['original_filename']}** (ID: {doc['id']})",
                f"**Type:** {doc['file_type']} | **Size:** {doc['file_size']/1024:.1f} KB | **Uploaded:** {doc['upload_timestamp'][:16]}"
            ]
            
            # Include full extracted content for LLM analysis
            if doc['extracted_content']:
                doc_info.append(f"\n**FULL DOCUMENT CONTENT:**")
                doc_info.append("```")
                doc_info.append(doc['extracted_content'])
                doc_info.append("```")
            
            # Include summary if available
            if doc['content_summary']:
                doc_info.append(f"\n**SUMMARY:** {doc['content_summary']}")
            
            # Include metadata
            if doc['metadata']:
                try:
                    import json
                    metadata = json.loads(doc['metadata']) if isinstance(doc['metadata'], str) else doc['metadata']
                    doc_info.append(f"\n**METADATA:** {metadata}")
                except:
                    pass
            
            context_parts.extend(doc_info)
            context_parts.append("\n" + "="*50 + "\n")  # Separator
        
        context_parts.append("\n**Instructions:** You can analyze, summarize, extract insights, answer questions, or perform any operations on the above document content. The full content is available for your processing.")
        
        return "\n".join(context_parts)
    
    def get_document_content(self, document_id: str, agent_id: str, group_id: str) -> Optional[str]:
        """Get full document content for agent use"""
        
        # Verify agent has access to this document
        document = self.storage.get_document_by_id(document_id)
        if not document:
            return None
        
        if document['agent_id'] != agent_id or document['group_id'] != group_id:
            return None
        
        # Log access
        self.storage.log_document_access(document_id, agent_id, group_id, 'view')
        
        return document['extracted_content']
    
    def _generate_summary(self, content: str, max_length: int = 200) -> str:
        """Generate a simple summary of the content"""
        # Simple summary - you can enhance this with LLM integration
        if len(content) <= max_length:
            return content
        
        sentences = content.split('. ')
        summary = ""
        for sentence in sentences:
            if len(summary + sentence) <= max_length - 3:
                summary += sentence + ". "
            else:
                break
        
        return summary.strip() + "..."
    
    def list_agent_documents(self, agent_id: str, group_id: str) -> List[Dict[str, Any]]:
        """List all documents for an agent"""
        return self.storage.get_agent_documents(agent_id, group_id)
    
    def get_recent_documents(self, agent_id: str, group_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent documents for an agent (wrapper for storage method)"""
        return self.storage.get_recent_documents(agent_id, group_id, limit)


# Global instance
document_manager = DocumentManager()
