"""
Async job parsing service
Refactored from ai_job_parser.py for FastAPI
"""
import os
import tempfile
import aiofiles
from pathlib import Path
from typing import Dict, Any
from ai_job_parser import AIJobParser
from backend.websocket.progress import send_progress_update

async def parse_job_file_async(
    file_content: bytes,
    filename: str,
    client_id: str = "default"
) -> Dict[str, Any]:
    """
    Parse job description file asynchronously with progress updates
    
    Args:
        file_content: File content as bytes
        filename: Original filename
        client_id: Client ID for WebSocket progress updates
        
    Returns:
        Parsed job data dictionary
    """
    # Save to temp file
    await send_progress_update(client_id, "reading_file", 0.1, message="Reading job description file...")
    
    temp_dir = tempfile.mkdtemp()
    safe_filename = os.path.basename(filename) or "job_description.txt"
    temp_path = os.path.join(temp_dir, safe_filename)
    
    try:
        async with aiofiles.open(temp_path, 'wb') as f:
            await f.write(file_content)
        
        await send_progress_update(client_id, "ai_extraction", 0.3, message="Extracting job details with AI...")
        
        # Use existing AIJobParser (synchronous, but we're in async context)
        parser = AIJobParser()
        result = parser.parse(temp_path)
        
        await send_progress_update(client_id, "complete", 1.0, message="Job parsing complete!")
        
        return result
    finally:
        # Cleanup temp file
        try:
            os.remove(temp_path)
            os.rmdir(temp_dir)
        except OSError:
            pass

