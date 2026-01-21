"""
Avionté API integration endpoints
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
import uuid
from datetime import datetime, timezone

from backend.database.connection import get_db
from backend.middleware.auth import get_current_user_id
from backend.services.avionte import AvionteClient
from backend.services.avionte.sync import AvionteSyncService
from backend.services.avionte.exceptions import AvionteException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/avionte", tags=["avionte"])


def get_avionte_client() -> AvionteClient:
    """Get Avionté API client instance"""
    return AvionteClient()


@router.get("/health")
async def health_check(client: AvionteClient = Depends(get_avionte_client)):
    """
    Check Avionté API health
    
    Returns:
        Health status
    """
    try:
        is_healthy = await client.health_check()
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "avionte_configured": client.auth.is_configured()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "avionte_configured": client.auth.is_configured()
        }


@router.post("/sync/candidate/{candidate_id}")
async def sync_candidate_to_avionte(
    candidate_id: str,
    force_update: bool = False,
    background_tasks: BackgroundTasks = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Sync a candidate to Avionté
    
    Args:
        candidate_id: Internal candidate ID
        force_update: Force update even if already synced
        background_tasks: Background tasks
        user_id: Current user ID
        db: Database session
        
    Returns:
        Sync result
    """
    try:
        client = get_avionte_client()
        sync_service = AvionteSyncService(client, db)
        
        result = await sync_service.sync_candidate_to_avionte(
            candidate_id,
            user_id,
            force_update
        )
        
        return {
            "success": True,
            "candidate_id": candidate_id,
            "avionte_talent_id": result.get("avionte_talent_id"),
            "action": result.get("action")
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AvionteException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Avionté API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to sync candidate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@router.post("/sync/job/{job_id}")
async def sync_job_to_avionte(
    job_id: str,
    force_update: bool = False,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Sync a job to Avionté
    
    Args:
        job_id: Internal job ID
        force_update: Force update even if already synced
        user_id: Current user ID
        db: Database session
        
    Returns:
        Sync result
    """
    try:
        client = get_avionte_client()
        sync_service = AvionteSyncService(client, db)
        
        result = await sync_service.sync_job_to_avionte(
            job_id,
            user_id,
            force_update
        )
        
        return {
            "success": True,
            "job_id": job_id,
            "avionte_job_id": result.get("avionte_job_id"),
            "action": result.get("action")
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AvionteException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Avionté API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to sync job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@router.get("/talent/{talent_id}")
async def get_talent_from_avionte(
    talent_id: str,
    client: AvionteClient = Depends(get_avionte_client)
):
    """
    Get a talent from Avionté
    
    Args:
        talent_id: Avionté talent ID
        client: Avionté client
        
    Returns:
        Talent data
    """
    try:
        from backend.services.avionte.talent import AvionteTalentAPI
        talent_api = AvionteTalentAPI(client)
        talent = await talent_api.get_talent(talent_id)
        return talent
    except AvionteException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Avionté API error: {str(e)}"
        )


@router.post("/sync/from-avionte/talent/{talent_id}")
async def sync_talent_from_avionte(
    talent_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Sync a talent from Avionté to internal system
    
    Args:
        talent_id: Avionté talent ID
        user_id: Current user ID
        db: Database session
        
    Returns:
        Sync result
    """
    try:
        client = get_avionte_client()
        sync_service = AvionteSyncService(client, db)
        
        result = await sync_service.sync_from_avionte_talent(talent_id, user_id)
        
        return {
            "success": True,
            "talent_id": talent_id,
            "candidate_id": result.get("candidate_id"),
            "action": result.get("action")
        }
    except AvionteException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Avionté API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to sync talent from Avionté: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@router.post("/talent/query")
async def query_talents(
    request: Dict[str, Any],
    client: AvionteClient = Depends(get_avionte_client)
):
    """
    Query talents from Avionté
    
    Request Body:
        filters: Optional filter criteria (e.g., {"firstName": "John"})
        page: Page number (default: 1)
        page_size: Items per page (default: 50)
        
    Returns:
        Query results with pagination
    """
    try:
        from backend.services.avionte.talent import AvionteTalentAPI
        talent_api = AvionteTalentAPI(client)
        filters = request.get("filters")
        page = request.get("page", 1)
        page_size = request.get("page_size", 50)
        
        results = await talent_api.query_talents(
            filters=filters,
            page=page,
            page_size=page_size
        )
        return results
    except AvionteException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Avionté API error: {str(e)}"
        )


@router.get("/talent/{talent_id}/documents")
async def get_talent_documents(
    talent_id: str,
    client: AvionteClient = Depends(get_avionte_client)
):
    """
    Get documents (resumes) for a talent from Avionté
    
    Args:
        talent_id: Avionté talent ID
        client: Avionté client
        
    Returns:
        List of documents
    """
    try:
        from backend.services.avionte.talent import AvionteTalentAPI
        talent_api = AvionteTalentAPI(client)
        documents = await talent_api.get_documents(talent_id)
        return {"documents": documents}
    except AvionteException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Avionté API error: {str(e)}"
        )


@router.get("/talent/{talent_id}/document/{document_id}/download")
async def download_talent_document(
    talent_id: str,
    document_id: str,
    client: AvionteClient = Depends(get_avionte_client)
):
    """
    Download a document (resume) from Avionté
    
    Args:
        talent_id: Avionté talent ID
        document_id: Document ID
        client: Avionté client
        
    Returns:
        Document file content
    """
    try:
        from backend.services.avionte.talent import AvionteTalentAPI
        from fastapi.responses import Response
        import base64
        
        talent_api = AvionteTalentAPI(client)
        
        # Get document details first
        documents = await talent_api.get_documents(talent_id)
        document = next((d for d in documents if d.get("documentId") == document_id), None)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Download document - Avionté API may return file data or URL
        # Check if document has URL or we need to fetch it
        if document.get("url"):
            # If URL provided, fetch it
            import httpx
            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(document["url"])
                content = response.content
        else:
            # Try to get document data directly from API
            # Note: This endpoint may need to be adjusted based on actual Avionté API
            endpoint = f"/v2/talent/{talent_id}/document/{document_id}/download"
            try:
                response_data = await client.get(endpoint)
                # If base64 encoded
                if isinstance(response_data, dict) and "fileData" in response_data:
                    content = base64.b64decode(response_data["fileData"])
                elif isinstance(response_data, bytes):
                    content = response_data
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Unable to retrieve document content"
                    )
            except Exception as e:
                logger.error(f"Failed to download document: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to download document: {str(e)}"
                )
        
        # Determine content type
        file_name = document.get("fileName", "document")
        if file_name.endswith(".pdf"):
            media_type = "application/pdf"
        elif file_name.endswith(".docx") or file_name.endswith(".doc"):
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif file_name.endswith(".txt"):
            media_type = "text/plain"
        else:
            media_type = "application/octet-stream"
        
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{file_name}"'}
        )
    except HTTPException:
        raise
    except AvionteException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Avionté API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to download document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@router.post("/sync/batch")
async def batch_sync(
    sync_type: str,  # "candidates" or "jobs"
    candidate_ids: Optional[list] = None,
    job_ids: Optional[list] = None,
    force_update: bool = False,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Batch sync candidates or jobs to Avionté
    
    Args:
        sync_type: Type of sync ("candidates" or "jobs")
        candidate_ids: List of candidate IDs (if sync_type is "candidates")
        job_ids: List of job IDs (if sync_type is "jobs")
        force_update: Force update even if already synced
        user_id: Current user ID
        db: Database session
        
    Returns:
        Batch sync results
    """
    try:
        client = get_avionte_client()
        sync_service = AvionteSyncService(client, db)
        
        results = []
        errors = []
        
        if sync_type == "candidates":
            if not candidate_ids:
                raise HTTPException(status_code=400, detail="candidate_ids required for candidates sync")
            
            for candidate_id in candidate_ids:
                try:
                    result = await sync_service.sync_candidate_to_avionte(
                        candidate_id,
                        user_id,
                        force_update
                    )
                    results.append({
                        "candidate_id": candidate_id,
                        "success": True,
                        "avionte_talent_id": result.get("avionte_talent_id"),
                        "action": result.get("action")
                    })
                except Exception as e:
                    errors.append({
                        "candidate_id": candidate_id,
                        "error": str(e)
                    })
        
        elif sync_type == "jobs":
            if not job_ids:
                raise HTTPException(status_code=400, detail="job_ids required for jobs sync")
            
            for job_id in job_ids:
                try:
                    result = await sync_service.sync_job_to_avionte(
                        job_id,
                        user_id,
                        force_update
                    )
                    results.append({
                        "job_id": job_id,
                        "success": True,
                        "avionte_job_id": result.get("avionte_job_id"),
                        "action": result.get("action")
                    })
                except Exception as e:
                    errors.append({
                        "job_id": job_id,
                        "error": str(e)
                    })
        else:
            raise HTTPException(status_code=400, detail="sync_type must be 'candidates' or 'jobs'")
        
        return {
            "success": len(errors) == 0,
            "total": len(results) + len(errors),
            "succeeded": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch sync failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
