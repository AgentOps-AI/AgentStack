import os
import json
from typing import List, Optional, Dict, Any
from pathlib import Path
from hyperspell import Hyperspell

# Get environment variables
HYPERSPELL_API_KEY = os.getenv('HYPERSPELL_API_KEY')
default_user_id = os.getenv('HYPERSPELL_USER_ID')


def hyperspell_search(query: str, sources: Optional[str] = None, answer: bool = False, user_id: Optional[str] = None) -> str:
    """
    Search across your HyperSpell knowledge base (documents, integrations like Notion, Gmail, etc.).
    
    Args:
        query: The search query to find relevant information
        sources: Comma-separated list of sources to search (e.g., "collections,notion,gmail"). 
                If None, searches all available sources.
        answer: If True, returns a direct answer to the query instead of just documents
        user_id: Optional user ID to use for this request. Defaults to HYPERSPELL_USER_ID env var.
    
    Returns:
        JSON string containing search results or answer
    """
    try:
        # Create client for this request
        client = Hyperspell(api_key=HYPERSPELL_API_KEY, user_id=user_id or default_user_id)
        # Parse sources if provided
        sources_list = sources.split(',') if sources else None
        
        # Build options based on sources
        options = {}
        if sources_list and 'collections' in sources_list:
            options['collections'] = {}
        
        response = client.query.search(
            query=query,
            sources=sources_list or ["collections"],
            answer=answer,
            options=options
        )
        
        if answer:
            return json.dumps({
                "answer": response.answer,
                "sources_used": [doc.source for doc in response.documents],
                "document_count": len(response.documents)
            })
        else:
                         return json.dumps({
                 "documents": [
                     {
                         "title": getattr(doc, 'filename', getattr(doc, 'title', 'No title')),
                         "content": getattr(doc, 'summary', 'No content available')[:500] + "..." if len(getattr(doc, 'summary', '')) > 500 else getattr(doc, 'summary', 'No content available'),
                         "source": doc.source,
                         "score": getattr(doc, 'score', 0),
                         "resource_id": doc.resource_id,
                         "content_type": getattr(doc, 'content_type', None)
                     }
                     for doc in response.documents
                 ],
                 "total_results": len(response.documents)
             })
            
    except Exception as e:
        return json.dumps({"error": f"Error searching HyperSpell: {str(e)}"})


def hyperspell_add_document(text: str, title: Optional[str] = None, collection: Optional[str] = None, user_id: Optional[str] = None) -> str:
    """
    Add a text document to your HyperSpell knowledge base.
    
    Args:
        text: The full text content to add
        title: Optional title for the document
        collection: Optional collection name to organize the document
        user_id: Optional user ID to use for this request. Defaults to HYPERSPELL_USER_ID env var.
    
    Returns:
        JSON string with the document ID and status
    """
    try:
        # Create client for this request
        client = Hyperspell(api_key=HYPERSPELL_API_KEY, user_id=user_id or default_user_id)
        response = client.documents.add(
            text=text,
            title=title,
            collection=collection
        )
        
        return json.dumps({
            "document_id": response.id,
            "resource_id": response.resource_id,
            "status": response.status,
            "collection": collection
        })
        
    except Exception as e:
        return json.dumps({"error": f"Error adding document to HyperSpell: {str(e)}"})


def hyperspell_upload_file(file_path: str, collection: Optional[str] = None, user_id: Optional[str] = None) -> str:
    """
    Upload a file (PDF, Word doc, spreadsheet, etc.) to your HyperSpell knowledge base.
    
    Args:
        file_path: Path to the file to upload
        collection: Optional collection name to organize the document
        user_id: Optional user ID to use for this request. Defaults to HYPERSPELL_USER_ID env var.
    
    Returns:
        JSON string with the document ID and status
    """
    try:
        # Create client for this request
        client = Hyperspell(api_key=HYPERSPELL_API_KEY, user_id=user_id or default_user_id)
        # Convert to Path object for proper MIME type detection
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            return json.dumps({"error": f"File not found: {file_path}"})
            
        response = client.documents.upload(
            file=file_path_obj,  # Use Path object directly
            collection=collection
        )
        
        return json.dumps({
            "document_id": response.id,
            "resource_id": response.resource_id,
            "status": response.status,
            "filename": file_path_obj.name,
            "collection": collection
        })
        
    except Exception as e:
        return json.dumps({"error": f"Error uploading file to HyperSpell: {str(e)}"})