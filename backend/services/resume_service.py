"""
Async resume parsing service
Refactored from resume_parser.py for FastAPI
"""
import os
import tempfile
import aiofiles
from typing import Dict, Any, List
from ai_resume_parser import AIResumeParser
from backend.websocket.progress import send_progress_update

async def parse_resume_file_async(
    file_content: bytes,
    filename: str,
    client_id: str = "default"
) -> Dict[str, Any]:
    """
    Parse resume file asynchronously with progress updates
    
    Args:
        file_content: File content as bytes
        filename: Original filename
        client_id: Client ID for WebSocket progress updates
        
    Returns:
        Parsed resume data dictionary
    """
    await send_progress_update(client_id, "reading_resume", 0.1, message=f"Reading resume: {filename}...")
    
    temp_dir = tempfile.mkdtemp()
    safe_filename = os.path.basename(filename) or "resume.pdf"
    temp_path = os.path.join(temp_dir, safe_filename)
    
    try:
        async with aiofiles.open(temp_path, 'wb') as f:
            await f.write(file_content)
        
        await send_progress_update(client_id, "ai_extraction", 0.5, message="Extracting candidate information with AI...")
        
        # Use existing AIResumeParser
        parser = AIResumeParser()
        result = parser.parse(temp_path)
        
        await send_progress_update(client_id, "complete", 1.0, message=f"Resume parsing complete: {filename}")
        
        return result
    finally:
        # Cleanup temp file
        try:
            os.remove(temp_path)
            os.rmdir(temp_dir)
        except OSError:
            pass


async def parse_multiple_resumes_async(
    files: List[tuple[bytes, str]],
    client_id: str = "default"
) -> List[Dict[str, Any]]:
    """
    Parse multiple resume files asynchronously
    
    Args:
        files: List of (file_content, filename) tuples
        client_id: Client ID for WebSocket progress updates
        
    Returns:
        List of parsed resume data dictionaries
    """
    results = []
    total = len(files)
    
    for i, (file_content, filename) in enumerate(files):
        await send_progress_update(
            client_id,
            "parsing_resume",
            (i + 0.5) / total,
            current=i + 1,
            total=total,
            message=f"Parsing resume {i + 1} of {total}: {filename}"
        )
        
        result = await parse_resume_file_async(file_content, filename, client_id)
        results.append(result)
    
    await send_progress_update(client_id, "all_complete", 1.0, message=f"All {total} resumes parsed successfully")
    
    return results

