from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from shared.database import get_db_session
from auth_service.models import get_current_user, User
from .schemas import (
    AlertCreate,
    AlertResponse,
    AlertUpdate,
    AlertStatusUpdate,
    AlertListResponse,
    AlertAnalyticsResponse
)
from .models import Alert, AlertStatus, AlertType
from shared.kafka_client import publish_alert_event
from shared.location import get_location_info
from shared.notifications import send_emergency_notifications

router = APIRouter()

@router.post("/panic", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_panic_alert(
    alert_data: AlertCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new panic alert - the core emergency function."""
    try:
        # Get location information if coordinates provided
        location_info = None
        if alert_data.latitude and alert_data.longitude:
            location_info = await get_location_info(
                alert_data.latitude, 
                alert_data.longitude
            )
        
        # Create the alert
        new_alert = Alert(
            user_id=current_user.id,
            alert_type=AlertType.PANIC,
            status=AlertStatus.ACTIVE,
            latitude=alert_data.latitude,
            longitude=alert_data.longitude,
            address=location_info.get('address') if location_info else None,
            message=alert_data.message,
            metadata={
                'device_info': alert_data.device_info,
                'location_accuracy': alert_data.location_accuracy,
                'battery_level': alert_data.battery_level,
                'network_type': alert_data.network_type,
                'location_info': location_info
            }
        )
        
        db.add(new_alert)
        await db.commit()
        await db.refresh(new_alert)
        
        # Publish high-priority alert event to Kafka
        alert_event = {
            "event_type": "panic_alert_created",
            "alert_id": str(new_alert.id),
            "user_id": str(current_user.id),
            "user_name": f"{current_user.first_name} {current_user.last_name}",
            "user_phone": current_user.phone_number,
            "latitude": new_alert.latitude,
            "longitude": new_alert.longitude,
            "address": new_alert.address,
            "message": new_alert.message,
            "timestamp": new_alert.created_at.isoformat(),
            "priority": "HIGH",
            "metadata": new_alert.metadata
        }
        
        await publish_alert_event(alert_event, priority="high")
        
        # Send emergency notifications in background
        background_tasks.add_task(
            send_emergency_notifications,
            alert_id=new_alert.id,
            user_id=current_user.id
        )
        
        return AlertResponse(
            id=new_alert.id,
            alert_type=new_alert.alert_type,
            status=new_alert.status,
            latitude=new_alert.latitude,
            longitude=new_alert.longitude,
            address=new_alert.address,
            message=new_alert.message,
            created_at=new_alert.created_at,
            updated_at=new_alert.updated_at,
            resolved_at=new_alert.resolved_at,
            metadata=new_alert.metadata
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create panic alert: {str(e)}"
        )

@router.post("/test", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_test_alert(
    alert_data: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a test alert for system verification."""
    try:
        # Get location information if coordinates provided
        location_info = None
        if alert_data.latitude and alert_data.longitude:
            location_info = await get_location_info(
                alert_data.latitude, 
                alert_data.longitude
            )
        
        # Create the test alert
        new_alert = Alert(
            user_id=current_user.id,
            alert_type=AlertType.TEST,
            status=AlertStatus.RESOLVED,  # Test alerts are immediately resolved
            latitude=alert_data.latitude,
            longitude=alert_data.longitude,
            address=location_info.get('address') if location_info else None,
            message=alert_data.message or "Test alert",
            resolved_at=datetime.utcnow(),
            metadata={
                'device_info': alert_data.device_info,
                'location_accuracy': alert_data.location_accuracy,
                'battery_level': alert_data.battery_level,
                'network_type': alert_data.network_type,
                'location_info': location_info,
                'test_alert': True
            }
        )
        
        db.add(new_alert)
        await db.commit()
        await db.refresh(new_alert)
        
        # Publish test alert event
        await publish_alert_event({
            "event_type": "test_alert_created",
            "alert_id": str(new_alert.id),
            "user_id": str(current_user.id),
            "timestamp": new_alert.created_at.isoformat(),
            "priority": "LOW"
        })
        
        return AlertResponse(
            id=new_alert.id,
            alert_type=new_alert.alert_type,
            status=new_alert.status,
            latitude=new_alert.latitude,
            longitude=new_alert.longitude,
            address=new_alert.address,
            message=new_alert.message,
            created_at=new_alert.created_at,
            updated_at=new_alert.updated_at,
            resolved_at=new_alert.resolved_at,
            metadata=new_alert.metadata
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create test alert: {str(e)}"
        )

@router.get("/", response_model=AlertListResponse)
async def get_user_alerts(
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[AlertStatus] = None,
    alert_type_filter: Optional[AlertType] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get user's alerts with pagination and filtering."""
    try:
        # Build query
        query = select(Alert).where(Alert.user_id == current_user.id)
        
        if status_filter:
            query = query.where(Alert.status == status_filter)
        if alert_type_filter:
            query = query.where(Alert.alert_type == alert_type_filter)
        
        # Get total count
        count_query = select(func.count(Alert.id)).where(Alert.user_id == current_user.id)
        if status_filter:
            count_query = count_query.where(Alert.status == status_filter)
        if alert_type_filter:
            count_query = count_query.where(Alert.alert_type == alert_type_filter)
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get alerts with pagination
        query = query.order_by(Alert.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        alerts = result.scalars().all()
        
        alert_responses = [
            AlertResponse(
                id=alert.id,
                alert_type=alert.alert_type,
                status=alert.status,
                latitude=alert.latitude,
                longitude=alert.longitude,
                address=alert.address,
                message=alert.message,
                created_at=alert.created_at,
                updated_at=alert.updated_at,
                resolved_at=alert.resolved_at,
                metadata=alert.metadata
            )
            for alert in alerts
        ]
        
        return AlertListResponse(
            alerts=alert_responses,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve alerts: {str(e)}"
        )

@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get a specific alert by ID."""
    try:
        result = await db.execute(
            select(Alert).where(
                Alert.id == alert_id,
                Alert.user_id == current_user.id
            )
        )
        alert = result.scalar_one_or_none()
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        return AlertResponse(
            id=alert.id,
            alert_type=alert.alert_type,
            status=alert.status,
            latitude=alert.latitude,
            longitude=alert.longitude,
            address=alert.address,
            message=alert.message,
            created_at=alert.created_at,
            updated_at=alert.updated_at,
            resolved_at=alert.resolved_at,
            metadata=alert.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve alert: {str(e)}"
        )

@router.put("/{alert_id}/status", response_model=AlertResponse)
async def update_alert_status(
    alert_id: UUID,
    status_data: AlertStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update alert status (resolve, cancel, etc.)."""
    try:
        result = await db.execute(
            select(Alert).where(
                Alert.id == alert_id,
                Alert.user_id == current_user.id
            )
        )
        alert = result.scalar_one_or_none()
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        # Update alert status
        old_status = alert.status
        alert.status = status_data.status
        
        if status_data.status in [AlertStatus.RESOLVED, AlertStatus.CANCELLED]:
            alert.resolved_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(alert)
        
        # Publish alert status update event
        await publish_alert_event({
            "event_type": "alert_status_updated",
            "alert_id": str(alert.id),
            "user_id": str(current_user.id),
            "old_status": old_status.value,
            "new_status": alert.status.value,
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return AlertResponse(
            id=alert.id,
            alert_type=alert.alert_type,
            status=alert.status,
            latitude=alert.latitude,
            longitude=alert.longitude,
            address=alert.address,
            message=alert.message,
            created_at=alert.created_at,
            updated_at=alert.updated_at,
            resolved_at=alert.resolved_at,
            metadata=alert.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update alert status: {str(e)}"
        )

@router.get("/analytics/summary", response_model=AlertAnalyticsResponse)
async def get_alert_analytics(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get user's alert analytics and statistics."""
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get total alerts in period
        total_result = await db.execute(
            select(func.count(Alert.id)).where(
                Alert.user_id == current_user.id,
                Alert.created_at >= start_date
            )
        )
        total_alerts = total_result.scalar()
        
        # Get panic alerts count
        panic_result = await db.execute(
            select(func.count(Alert.id)).where(
                Alert.user_id == current_user.id,
                Alert.alert_type == AlertType.PANIC,
                Alert.created_at >= start_date
            )
        )
        panic_alerts = panic_result.scalar()
        
        # Get test alerts count
        test_result = await db.execute(
            select(func.count(Alert.id)).where(
                Alert.user_id == current_user.id,
                Alert.alert_type == AlertType.TEST,
                Alert.created_at >= start_date
            )
        )
        test_alerts = test_result.scalar()
        
        # Get resolved alerts count
        resolved_result = await db.execute(
            select(func.count(Alert.id)).where(
                Alert.user_id == current_user.id,
                Alert.status == AlertStatus.RESOLVED,
                Alert.created_at >= start_date
            )
        )
        resolved_alerts = resolved_result.scalar()
        
        # Get active alerts count
        active_result = await db.execute(
            select(func.count(Alert.id)).where(
                Alert.user_id == current_user.id,
                Alert.status == AlertStatus.ACTIVE
            )
        )
        active_alerts = active_result.scalar()
        
        # Calculate average response time for resolved alerts
        avg_response_result = await db.execute(
            select(func.avg(
                func.extract('epoch', Alert.resolved_at) - 
                func.extract('epoch', Alert.created_at)
            )).where(
                Alert.user_id == current_user.id,
                Alert.status == AlertStatus.RESOLVED,
                Alert.resolved_at.isnot(None),
                Alert.created_at >= start_date
            )
        )
        avg_response_time = avg_response_result.scalar() or 0
        
        return AlertAnalyticsResponse(
            period_days=days,
            total_alerts=total_alerts,
            panic_alerts=panic_alerts,
            test_alerts=test_alerts,
            resolved_alerts=resolved_alerts,
            active_alerts=active_alerts,
            avg_response_time_seconds=int(avg_response_time),
            start_date=start_date,
            end_date=end_date
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve alert analytics: {str(e)}"
        )

# Import required SQLAlchemy functions
from sqlalchemy import select, func