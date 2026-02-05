"""
Avionté API integration endpoints
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any, AsyncGenerator
import uuid
import json
import hashlib
from datetime import datetime, timezone

from backend.database.connection import get_db
from backend.middleware.auth import get_current_user_id
from backend.services.avionte import AvionteClient
from backend.services.avionte.sync import AvionteSyncService
from backend.services.avionte.exceptions import AvionteException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/avionte", tags=["avionte"])


async def get_avionte_client() -> AsyncGenerator[AvionteClient, None]:
    """
    Get Avionté API client instance with proper lifecycle management.
    
    This dependency ensures the client is properly closed after the request completes,
    preventing connection pool exhaustion.
    """
    client = AvionteClient()
    try:
        yield client
    finally:
        await client.close()


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
    client = None
    try:
        client = AvionteClient()
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
    finally:
        if client:
            await client.close()


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
    client = None
    try:
        client = AvionteClient()
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
    finally:
        if client:
            await client.close()


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
    client = None
    try:
        client = AvionteClient()
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
    finally:
        if client:
            await client.close()


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
    request: Dict[str, Any] = Body(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Batch sync candidates or jobs to Avionté
    
    Args:
        request: Request body with sync_type, candidate_ids/job_ids, and force_update
        user_id: Current user ID
        db: Database session
        
    Returns:
        Batch sync results
    """
    client = None
    try:
        sync_type = request.get("sync_type")
        candidate_ids = request.get("candidate_ids")
        job_ids = request.get("job_ids")
        force_update = request.get("force_update", False)
        
        if not sync_type:
            raise HTTPException(status_code=400, detail="sync_type is required")
        
        client = AvionteClient()
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
    finally:
        if client:
            await client.close()


@router.post("/job/query")
async def query_avionte_jobs(
    request: Dict[str, Any] = Body({}),
    client: AvionteClient = Depends(get_avionte_client)
):
    """
    Query jobs from Avionté
    
    Args:
        request: Request body with filters, page, pageSize
        client: Avionté client
        
    Returns:
        Query results with pagination
    """
    try:
        from backend.services.avionte.jobs import AvionteJobsAPI
        jobs_api = AvionteJobsAPI(client)
        filters = request.get("filters", {})
        page = request.get("page", 1)
        page_size = request.get("page_size", request.get("pageSize", 50))
        jobs_data = await jobs_api.query_jobs(
            filters=filters,
            page=page,
            page_size=page_size
        )
        return jobs_data
    except AvionteException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Avionté API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to query jobs from Avionté: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@router.get("/job/{job_id}/applicants")
async def get_job_applicants(
    job_id: str,
    client: AvionteClient = Depends(get_avionte_client)
):
    """
    Get all web applicants for a specific Avionté job
    
    Args:
        job_id: Avionté job ID
        client: Avionté client
        
    Returns:
        List of web applicants
    """
    try:
        from backend.services.avionte.web_applicants import AvionteWebApplicantsAPI
        applicants_api = AvionteWebApplicantsAPI(client)
        applicants = await applicants_api.get_web_applicants_for_job(job_id)
        return {
            "job_id": job_id,
            "applicants": applicants,
            "count": len(applicants)
        }
    except AvionteException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Avionté API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to get applicants for job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@router.post("/job/{job_id}/applicants/import")
async def import_job_applicants(
    job_id: str,
    request: Dict[str, Any] = Body({}),
    client_id: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    client: AvionteClient = Depends(get_avionte_client)
):
    """
    Batch import resumes from web applicants for a job
    
    Args:
        job_id: Avionté job ID
        request: Request body with optional applicant_ids filter
        client_id: Optional client ID for progress updates
        user_id: Current user ID
        db: Database session
        client: Avionté client
        
    Returns:
        Import summary with candidate IDs
    """
    try:
        import base64
        from backend.services.avionte.web_applicants import AvionteWebApplicantsAPI
        from backend.services.avionte.talent import AvionteTalentAPI
        from backend.services.resume_service import parse_resume_file_async
        from backend.api.resumes import check_duplicate_resume
        from storage import save_bytes
        from sqlalchemy import text
        
        if not client_id:
            client_id = str(uuid.uuid4())
        
        applicants_api = AvionteWebApplicantsAPI(client)
        talent_api = AvionteTalentAPI(client)
        
        # Get all applicants for the job
        all_applicants = await applicants_api.get_web_applicants_for_job(job_id)
        
        # Filter by applicant_ids if provided
        applicant_ids = request.get("applicant_ids")
        if applicant_ids:
            all_applicants = [a for a in all_applicants if a.get("webApplicantId") in applicant_ids or a.get("applicantId") in applicant_ids]
        
        if not all_applicants:
            return {
                "success": True,
                "imported": 0,
                "failed": 0,
                "candidate_ids": [],
                "errors": [],
                "message": "No applicants found for this job"
            }
        
        imported = 0
        failed = 0
        candidate_ids = []
        errors = []
        created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        # Process each applicant
        for applicant in all_applicants:
            try:
                talent_id = applicant.get("talentId")
                if not talent_id:
                    errors.append({
                        "applicant_id": applicant.get("webApplicantId") or applicant.get("applicantId"),
                        "error": "No talent ID found for applicant"
                    })
                    failed += 1
                    continue
                
                # Get documents for this talent
                documents = await talent_api.get_documents(talent_id)
                if not documents:
                    errors.append({
                        "applicant_id": applicant.get("webApplicantId") or applicant.get("applicantId"),
                        "talent_id": talent_id,
                        "error": "No documents found for applicant"
                    })
                    failed += 1
                    continue
                
                # Find resume documents (prioritize resume types)
                resume_docs = [d for d in documents if d.get("documentType", "").lower() in ["resume", "cv", "curriculum vitae"] or 
                              "resume" in d.get("fileName", "").lower() or "cv" in d.get("fileName", "").lower()]
                if not resume_docs:
                    # If no resume-type documents, use first document
                    resume_docs = documents[:1]
                
                # Download and process the first resume document
                resume_doc = resume_docs[0]
                document_id = resume_doc.get("documentId")
                
                if not document_id:
                    errors.append({
                        "applicant_id": applicant.get("webApplicantId") or applicant.get("applicantId"),
                        "talent_id": talent_id,
                        "error": "Document ID not found"
                    })
                    failed += 1
                    continue
                
                # Download document - use the existing download endpoint logic
                # Try to get document via download endpoint
                endpoint = f"/v2/talent/{talent_id}/document/{document_id}"
                doc_response = await client.get(endpoint)
                
                # Handle different response formats
                file_data = None
                file_name = resume_doc.get("fileName", "resume.pdf")
                
                if isinstance(doc_response, dict):
                    if "fileData" in doc_response:
                        file_data = base64.b64decode(doc_response["fileData"])
                    elif "content" in doc_response:
                        file_data = doc_response["content"]
                        if isinstance(file_data, str):
                            file_data = base64.b64decode(file_data)
                elif isinstance(doc_response, bytes):
                    file_data = doc_response
                
                # If still no data, try download endpoint
                if not file_data:
                    download_endpoint = f"/v2/talent/{talent_id}/document/{document_id}/download"
                    try:
                        download_response = await client.get(download_endpoint)
                        if isinstance(download_response, dict) and "fileData" in download_response:
                            file_data = base64.b64decode(download_response["fileData"])
                        elif isinstance(download_response, bytes):
                            file_data = download_response
                    except:
                        pass
                
                if not file_data:
                    raise ValueError("Could not retrieve document content")
                
                # Check for duplicates
                file_hash = hashlib.sha256(file_data).hexdigest()
                duplicate = await check_duplicate_resume(file_hash, user_id, db)
                if duplicate:
                    candidate_ids.append(duplicate["candidate_id"])
                    imported += 1
                    continue
                
                # Parse resume
                parsed_data = await parse_resume_file_async(file_data, file_name, client_id)
                
                # Save resume file
                stored_path, _ = save_bytes(file_data, file_name)
                
                # Create candidate record
                candidate_id = str(uuid.uuid4())
                applicant_name = (applicant.get("firstName", "") + " " + applicant.get("lastName", "")).strip()
                await db.execute(
                    text("""
                        INSERT INTO candidates (id, user_id, name, email, phone, resume_path, parsed_data, created_at, updated_at)
                        VALUES (:id, :user_id, :name, :email, :phone, :resume_path, :parsed_data, :created_at, :updated_at)
                    """),
                    {
                        "id": candidate_id,
                        "user_id": user_id,
                        "name": parsed_data.get("name") or applicant_name or "Unknown",
                        "email": parsed_data.get("email") or applicant.get("email", ""),
                        "phone": parsed_data.get("phone") or applicant.get("phone", ""),
                        "resume_path": stored_path,
                        "parsed_data": json.dumps(parsed_data),
                        "created_at": created_at,
                        "updated_at": created_at
                    }
                )
                
                candidate_ids.append(candidate_id)
                imported += 1
                    
            except Exception as e:
                logger.error(f"Failed to import applicant: {str(e)}")
                applicant_id = applicant.get("webApplicantId") or applicant.get("applicantId")
                talent_id = applicant.get("talentId")
                error_entry = {
                    "applicant_id": applicant_id,
                    "error": str(e)
                }
                if talent_id:
                    error_entry["talent_id"] = talent_id
                errors.append(error_entry)
                failed += 1
        
        # Commit all successful inserts
        try:
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to commit transaction: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save candidates to database: {str(e)}"
            )
        
        return {
            "success": failed == 0,
            "imported": imported,
            "failed": failed,
            "candidate_ids": candidate_ids,
            "errors": errors
        }
        
    except AvionteException as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Avionté API error: {str(e)}"
        )
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to import applicants for job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
