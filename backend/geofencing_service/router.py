from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from shared.database import get_db_session
from auth_service.models import get_current_user, User
from .schemas import (
    GeofenceCreate,
    GeofenceUpdate,
    GeofenceResponse,
    GeofenceListResponse,
    LocationUpdate,
    GeofenceEventResponse,
    GeofenceAnalyticsResponse
)
from .models import Geofence, GeofenceEvent, GeofenceType, EventType
from shared.kafka_client import publish_geofence_event
from shared.location import calculate_distance, get_location_info

router = APIRouter()

@router.post("/", response_model=GeofenceResponse, status_code=status.HTTP_201_CREATED)
async def create_geofence(
    geofence_data: GeofenceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new geofence (safe zone or restricted area)."""
    try:
        # Check if user already has maximum geofences (limit to 10)
        result = await db.execute(
            select(func.count(Geofence.id)).where(
                Geofence.user_id == current_user.id,
                Geofence.is_active == True
            )
        )
        geofence_count = result.scalar()
        
        if geofence_count >= 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum of 10 active geofences allowed"
            )
        
        # Get location information for the geofence center
        location_info = await get_location_info(
            geofence_data.latitude,
            geofence_data.longitude
        )
        
        # Create new geofence
        new_geofence = Geofence(
            user_id=current_user.id,
            name=geofence_data.name,
            description=geofence_data.description,
            geofence_type=geofence_data.geofence_type,
            latitude=geofence_data.latitude,
            longitude=geofence_data.longitude,
            radius_meters=geofence_data.radius_meters,
            is_active=geofence_data.is_active,
            notify_on_enter=geofence_data.notify_on_enter,
            notify_on_exit=geofence_data.notify_on_exit,
            metadata={
                'location_info': location_info,
                'created_via': 'api'
            }
        )
        
        db.add(new_geofence)
        await db.commit()
        await db.refresh(new_geofence)
        
        # Publish geofence created event
        await publish_geofence_event({
            "event_type": "geofence_created",
            "geofence_id": str(new_geofence.id),
            "user_id": str(current_user.id),
            "geofence_name": new_geofence.name,
            "geofence_type": new_geofence.geofence_type.value,
            "latitude": new_geofence.latitude,
            "longitude": new_geofence.longitude,
            "radius_meters": new_geofence.radius_meters,
            "is_active": new_geofence.is_active,
            "timestamp": new_geofence.created_at.isoformat()
        })
        
        return GeofenceResponse(
            id=new_geofence.id,
            name=new_geofence.name,
            description=new_geofence.description,
            geofence_type=new_geofence.geofence_type,
            latitude=new_geofence.latitude,
            longitude=new_geofence.longitude,
            radius_meters=new_geofence.radius_meters,
            is_active=new_geofence.is_active,
            notify_on_enter=new_geofence.notify_on_enter,
            notify_on_exit=new_geofence.notify_on_exit,
            created_at=new_geofence.created_at,
            updated_at=new_geofence.updated_at,
            metadata=new_geofence.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create geofence: {str(e)}"
        )

@router.get("/", response_model=GeofenceListResponse)
async def get_user_geofences(
    skip: int = 0,
    limit: int = 20,
    active_only: bool = True,
    geofence_type_filter: Optional[GeofenceType] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get user's geofences with pagination and filtering."""
    try:
        # Build query
        query = select(Geofence).where(Geofence.user_id == current_user.id)
        
        if active_only:
            query = query.where(Geofence.is_active == True)
        if geofence_type_filter:
            query = query.where(Geofence.geofence_type == geofence_type_filter)
        
        # Get total count
        count_query = select(func.count(Geofence.id)).where(Geofence.user_id == current_user.id)
        if active_only:
            count_query = count_query.where(Geofence.is_active == True)
        if geofence_type_filter:
            count_query = count_query.where(Geofence.geofence_type == geofence_type_filter)
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get geofences with pagination
        query = query.order_by(Geofence.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        geofences = result.scalars().all()
        
        geofence_responses = [
            GeofenceResponse(
                id=geofence.id,
                name=geofence.name,
                description=geofence.description,
                geofence_type=geofence.geofence_type,
                latitude=geofence.latitude,
                longitude=geofence.longitude,
                radius_meters=geofence.radius_meters,
                is_active=geofence.is_active,
                notify_on_enter=geofence.notify_on_enter,
                notify_on_exit=geofence.notify_on_exit,
                created_at=geofence.created_at,
                updated_at=geofence.updated_at,
                metadata=geofence.metadata
            )
            for geofence in geofences
        ]
        
        return GeofenceListResponse(
            geofences=geofence_responses,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve geofences: {str(e)}"
        )

@router.get("/{geofence_id}", response_model=GeofenceResponse)
async def get_geofence(
    geofence_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get a specific geofence by ID."""
    try:
        result = await db.execute(
            select(Geofence).where(
                Geofence.id == geofence_id,
                Geofence.user_id == current_user.id
            )
        )
        geofence = result.scalar_one_or_none()
        
        if not geofence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Geofence not found"
            )
        
        return GeofenceResponse(
            id=geofence.id,
            name=geofence.name,
            description=geofence.description,
            geofence_type=geofence.geofence_type,
            latitude=geofence.latitude,
            longitude=geofence.longitude,
            radius_meters=geofence.radius_meters,
            is_active=geofence.is_active,
            notify_on_enter=geofence.notify_on_enter,
            notify_on_exit=geofence.notify_on_exit,
            created_at=geofence.created_at,
            updated_at=geofence.updated_at,
            metadata=geofence.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve geofence: {str(e)}"
        )

@router.put("/{geofence_id}", response_model=GeofenceResponse)
async def update_geofence(
    geofence_id: UUID,
    geofence_data: GeofenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update a geofence."""
    try:
        result = await db.execute(
            select(Geofence).where(
                Geofence.id == geofence_id,
                Geofence.user_id == current_user.id
            )
        )
        geofence = result.scalar_one_or_none()
        
        if not geofence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Geofence not found"
            )
        
        # Update geofence fields
        if geofence_data.name is not None:
            geofence.name = geofence_data.name
        if geofence_data.description is not None:
            geofence.description = geofence_data.description
        if geofence_data.latitude is not None:
            geofence.latitude = geofence_data.latitude
        if geofence_data.longitude is not None:
            geofence.longitude = geofence_data.longitude
        if geofence_data.radius_meters is not None:
            geofence.radius_meters = geofence_data.radius_meters
        if geofence_data.is_active is not None:
            geofence.is_active = geofence_data.is_active
        if geofence_data.notify_on_enter is not None:
            geofence.notify_on_enter = geofence_data.notify_on_enter
        if geofence_data.notify_on_exit is not None:
            geofence.notify_on_exit = geofence_data.notify_on_exit
        
        await db.commit()
        await db.refresh(geofence)
        
        # Publish geofence updated event
        await publish_geofence_event({
            "event_type": "geofence_updated",
            "geofence_id": str(geofence.id),
            "user_id": str(current_user.id),
            "updated_fields": geofence_data.dict(exclude_unset=True),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return GeofenceResponse(
            id=geofence.id,
            name=geofence.name,
            description=geofence.description,
            geofence_type=geofence.geofence_type,
            latitude=geofence.latitude,
            longitude=geofence.longitude,
            radius_meters=geofence.radius_meters,
            is_active=geofence.is_active,
            notify_on_enter=geofence.notify_on_enter,
            notify_on_exit=geofence.notify_on_exit,
            created_at=geofence.created_at,
            updated_at=geofence.updated_at,
            metadata=geofence.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update geofence: {str(e)}"
        )

@router.delete("/{geofence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_geofence(
    geofence_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a geofence."""
    try:
        result = await db.execute(
            select(Geofence).where(
                Geofence.id == geofence_id,
                Geofence.user_id == current_user.id
            )
        )
        geofence = result.scalar_one_or_none()
        
        if not geofence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Geofence not found"
            )
        
        await db.delete(geofence)
        await db.commit()
        
        # Publish geofence deleted event
        await publish_geofence_event({
            "event_type": "geofence_deleted",
            "geofence_id": str(geofence_id),
            "user_id": str(current_user.id),
            "geofence_name": geofence.name,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete geofence: {str(e)}"
        )

@router.post("/location-update", status_code=status.HTTP_200_OK)
async def update_location(
    location_data: LocationUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update user location and check geofence events."""
    try:
        # Get all active geofences for the user
        result = await db.execute(
            select(Geofence).where(
                Geofence.user_id == current_user.id,
                Geofence.is_active == True
            )
        )
        geofences = result.scalars().all()
        
        # Check each geofence for entry/exit events
        for geofence in geofences:
            distance = calculate_distance(
                location_data.latitude,
                location_data.longitude,
                geofence.latitude,
                geofence.longitude
            )
            
            is_inside = distance <= geofence.radius_meters
            
            # Check for recent events to avoid duplicates
            recent_event_result = await db.execute(
                select(GeofenceEvent).where(
                    GeofenceEvent.geofence_id == geofence.id,
                    GeofenceEvent.user_id == current_user.id,
                    GeofenceEvent.created_at >= datetime.utcnow() - timedelta(minutes=5)
                ).order_by(GeofenceEvent.created_at.desc())
            )
            recent_event = recent_event_result.scalar_one_or_none()
            
            # Determine if we need to create an event
            should_create_event = False
            event_type = None
            
            if is_inside and geofence.notify_on_enter:
                if not recent_event or recent_event.event_type == EventType.EXIT:
                    should_create_event = True
                    event_type = EventType.ENTER
            elif not is_inside and geofence.notify_on_exit:
                if recent_event and recent_event.event_type == EventType.ENTER:
                    should_create_event = True
                    event_type = EventType.EXIT
            
            if should_create_event:
                # Create geofence event
                geofence_event = GeofenceEvent(
                    geofence_id=geofence.id,
                    user_id=current_user.id,
                    event_type=event_type,
                    latitude=location_data.latitude,
                    longitude=location_data.longitude,
                    distance_meters=distance,
                    metadata={
                        'location_accuracy': location_data.accuracy,
                        'device_info': location_data.device_info,
                        'geofence_name': geofence.name,
                        'geofence_type': geofence.geofence_type.value
                    }
                )
                
                db.add(geofence_event)
                
                # Publish geofence event
                await publish_geofence_event({
                    "event_type": f"geofence_{event_type.value}",
                    "geofence_id": str(geofence.id),
                    "geofence_name": geofence.name,
                    "geofence_type": geofence.geofence_type.value,
                    "user_id": str(current_user.id),
                    "user_name": f"{current_user.first_name} {current_user.last_name}",
                    "latitude": location_data.latitude,
                    "longitude": location_data.longitude,
                    "distance_meters": distance,
                    "timestamp": datetime.utcnow().isoformat(),
                    "priority": "MEDIUM" if geofence.geofence_type == GeofenceType.SAFE_ZONE else "HIGH"
                })
        
        await db.commit()
        
        return {"message": "Location updated successfully"}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update location: {str(e)}"
        )

@router.get("/events", response_model=List[GeofenceEventResponse])
async def get_geofence_events(
    skip: int = 0,
    limit: int = 50,
    geofence_id: Optional[UUID] = None,
    event_type_filter: Optional[EventType] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get user's geofence events with pagination and filtering."""
    try:
        # Build query
        query = select(GeofenceEvent).where(GeofenceEvent.user_id == current_user.id)
        
        if geofence_id:
            query = query.where(GeofenceEvent.geofence_id == geofence_id)
        if event_type_filter:
            query = query.where(GeofenceEvent.event_type == event_type_filter)
        
        # Get events with pagination
        query = query.order_by(GeofenceEvent.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        events = result.scalars().all()
        
        return [
            GeofenceEventResponse(
                id=event.id,
                geofence_id=event.geofence_id,
                event_type=event.event_type,
                latitude=event.latitude,
                longitude=event.longitude,
                distance_meters=event.distance_meters,
                created_at=event.created_at,
                metadata=event.metadata
            )
            for event in events
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve geofence events: {str(e)}"
        )

@router.get("/analytics/summary", response_model=GeofenceAnalyticsResponse)
async def get_geofence_analytics(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get user's geofence analytics and statistics."""
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get total geofences
        total_geofences_result = await db.execute(
            select(func.count(Geofence.id)).where(
                Geofence.user_id == current_user.id
            )
        )
        total_geofences = total_geofences_result.scalar()
        
        # Get active geofences
        active_geofences_result = await db.execute(
            select(func.count(Geofence.id)).where(
                Geofence.user_id == current_user.id,
                Geofence.is_active == True
            )
        )
        active_geofences = active_geofences_result.scalar()
        
        # Get total events in period
        total_events_result = await db.execute(
            select(func.count(GeofenceEvent.id)).where(
                GeofenceEvent.user_id == current_user.id,
                GeofenceEvent.created_at >= start_date
            )
        )
        total_events = total_events_result.scalar()
        
        # Get enter events
        enter_events_result = await db.execute(
            select(func.count(GeofenceEvent.id)).where(
                GeofenceEvent.user_id == current_user.id,
                GeofenceEvent.event_type == EventType.ENTER,
                GeofenceEvent.created_at >= start_date
            )
        )
        enter_events = enter_events_result.scalar()
        
        # Get exit events
        exit_events_result = await db.execute(
            select(func.count(GeofenceEvent.id)).where(
                GeofenceEvent.user_id == current_user.id,
                GeofenceEvent.event_type == EventType.EXIT,
                GeofenceEvent.created_at >= start_date
            )
        )
        exit_events = exit_events_result.scalar()
        
        return GeofenceAnalyticsResponse(
            period_days=days,
            total_geofences=total_geofences,
            active_geofences=active_geofences,
            total_events=total_events,
            enter_events=enter_events,
            exit_events=exit_events,
            start_date=start_date,
            end_date=end_date
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve geofence analytics: {str(e)}"
        )

# Import required SQLAlchemy functions and datetime
from sqlalchemy import select, func
from datetime import timedelta