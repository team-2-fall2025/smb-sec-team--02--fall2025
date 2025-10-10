from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from ..services.osint.otx_client import OTXClient, OTXAPIError
from ..services.scheduler import scheduler_service
from ..db.models import IntelEvent
from ..database import db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/detect", tags=["detect"])

# Initialize OTX client
otx_client = OTXClient()


@router.get("/health")
async def detect_health():
    """Health check for detect module"""
    try:
        otx_health = otx_client.health_check()
        return {
            "status": "healthy",
            "module": "detect",
            "otx_client": otx_health,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Detect health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Detect module unhealthy: {str(e)}")


@router.post("/intel/ip/{ip_address}")
async def check_ip_reputation(ip_address: str) -> IntelEvent:
    """
    Check IP address reputation using OTX.
    
    Args:
        ip_address: IP address to check
        
    Returns:
        IntelEvent with reputation data
    """
    try:
        logger.info(f"Checking IP reputation for {ip_address}")
        intel_event = otx_client.get_ip_reputation(ip_address)
        
        # Store in database
        event_dict = intel_event.dict(by_alias=True)
        event_dict['_id'] = event_dict.pop('id')
        await db.intel_events.insert_one(event_dict)
        
        return intel_event
        
    except OTXAPIError as e:
        logger.error(f"OTX API error for IP {ip_address}: {e}")
        raise HTTPException(status_code=502, detail=f"OTX API error: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to check IP reputation for {ip_address}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/intel/domain/{domain}")
async def check_domain_reputation(domain: str) -> IntelEvent:
    """
    Check domain reputation using OTX.
    
    Args:
        domain: Domain to check
        
    Returns:
        IntelEvent with reputation data
    """
    try:
        logger.info(f"Checking domain reputation for {domain}")
        intel_event = otx_client.get_domain_reputation(domain)
        
        # Store in database
        event_dict = intel_event.dict(by_alias=True)
        event_dict['_id'] = event_dict.pop('id')
        await db.intel_events.insert_one(event_dict)
        
        return intel_event
        
    except OTXAPIError as e:
        logger.error(f"OTX API error for domain {domain}: {e}")
        raise HTTPException(status_code=502, detail=f"OTX API error: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to check domain reputation for {domain}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/intel/hash/{file_hash}")
async def check_file_hash_reputation(file_hash: str) -> IntelEvent:
    """
    Check file hash reputation using OTX.
    
    Args:
        file_hash: File hash (MD5, SHA1, or SHA256) to check
        
    Returns:
        IntelEvent with reputation data
    """
    try:
        logger.info(f"Checking file hash reputation for {file_hash}")
        intel_event = otx_client.get_file_hash_reputation(file_hash)
        
        # Store in database
        event_dict = intel_event.dict(by_alias=True)
        event_dict['_id'] = event_dict.pop('id')
        await db.intel_events.insert_one(event_dict)
        
        return intel_event
        
    except OTXAPIError as e:
        logger.error(f"OTX API error for hash {file_hash}: {e}")
        raise HTTPException(status_code=502, detail=f"OTX API error: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to check file hash reputation for {file_hash}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/intel/events")
async def get_intel_events(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    source: Optional[str] = None,
    severity: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get intelligence events from database.
    
    Args:
        limit: Maximum number of events to return
        offset: Number of events to skip
        source: Filter by source (e.g., 'otx')
        severity: Filter by severity (low, medium, high, critical)
        
    Returns:
        Dictionary with events and metadata
    """
    try:
        # Build query filter
        query_filter = {}
        if source:
            query_filter['source'] = source
        if severity:
            query_filter['severity'] = severity
        
        # Get total count
        total_count = await db.intel_events.count_documents(query_filter)
        
        # Get events with pagination
        cursor = db.intel_events.find(query_filter).sort('created_at', -1).skip(offset).limit(limit)
        events = []
        
        async for event in cursor:
            event['_id'] = str(event['_id'])  # Convert ObjectId to string
            events.append(event)
        
        return {
            "events": events,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(events) < total_count
        }
        
    except Exception as e:
        logger.error(f"Failed to get intel events: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/scheduler/status")
async def get_scheduler_status() -> Dict[str, Any]:
    """
    Get scheduler status and job information.
    
    Returns:
        Dictionary with scheduler status
    """
    try:
        return await scheduler_service.get_scheduler_status()
    except Exception as e:
        logger.error(f"Failed to get scheduler status: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/scheduler/trigger")
async def trigger_manual_collection() -> Dict[str, Any]:
    """
    Manually trigger intelligence collection.
    
    Returns:
        Dictionary with collection results
    """
    try:
        return await scheduler_service.trigger_manual_collection()
    except Exception as e:
        logger.error(f"Failed to trigger manual collection: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

