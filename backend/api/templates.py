"""
Templates API endpoints
"""
from fastapi import APIRouter
from typing import Dict, List
from industry_templates import get_industry_templates

router = APIRouter()


@router.get("/")
async def list_templates() -> Dict[str, Dict]:
    """
    List all available industry templates
    
    Returns:
        Dictionary of template names and their configurations
    """
    templates = get_industry_templates()
    
    return {
        name: {
            "name": template.name,
            "description": template.description,
            "weights": template.weights
        }
        for name, template in templates.items()
    }


@router.get("/{template_name}")
async def get_template(template_name: str) -> Dict:
    """
    Get specific template by name
    
    Args:
        template_name: Template name (e.g., "healthcare", "technology")
        
    Returns:
        Template configuration
    """
    templates = get_industry_templates()
    
    if template_name not in templates:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_name}' not found"
        )
    
    template = templates[template_name]
    
    return {
        "name": template.name,
        "description": template.description,
        "weights": template.weights
    }
