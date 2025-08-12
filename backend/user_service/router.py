from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from shared.database import get_db_session
from auth_service.models import get_current_user, User
from .schemas import (
    UserProfileResponse,
    UserProfileUpdate,
    EmergencyContactCreate,
    EmergencyContactUpdate,
    EmergencyContactResponse,
    UserPreferencesUpdate,
    UserPreferencesResponse
)
from .models import EmergencyContact, UserPreferences
from shared.kafka_client import publish_user_event

router = APIRouter()

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user's profile information."""
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        phone_number=current_user.phone_number,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )

@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update current user's profile information."""
    try:
        # Update user fields
        if profile_data.first_name is not None:
            current_user.first_name = profile_data.first_name
        if profile_data.last_name is not None:
            current_user.last_name = profile_data.last_name
        if profile_data.phone_number is not None:
            current_user.phone_number = profile_data.phone_number
        
        await db.commit()
        await db.refresh(current_user)
        
        # Publish user update event
        await publish_user_event({
            "event_type": "user_profile_updated",
            "user_id": str(current_user.id),
            "updated_fields": profile_data.dict(exclude_unset=True)
        })
        
        return UserProfileResponse(
            id=current_user.id,
            email=current_user.email,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            phone_number=current_user.phone_number,
            is_active=current_user.is_active,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )

@router.get("/emergency-contacts", response_model=List[EmergencyContactResponse])
async def get_emergency_contacts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get user's emergency contacts."""
    try:
        result = await db.execute(
            select(EmergencyContact).where(EmergencyContact.user_id == current_user.id)
        )
        contacts = result.scalars().all()
        
        return [
            EmergencyContactResponse(
                id=contact.id,
                name=contact.name,
                phone_number=contact.phone_number,
                email=contact.email,
                relationship=contact.relationship,
                is_primary=contact.is_primary,
                created_at=contact.created_at
            )
            for contact in contacts
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve emergency contacts: {str(e)}"
        )

@router.post("/emergency-contacts", response_model=EmergencyContactResponse, status_code=status.HTTP_201_CREATED)
async def create_emergency_contact(
    contact_data: EmergencyContactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new emergency contact."""
    try:
        # Check if user already has 5 emergency contacts (limit)
        result = await db.execute(
            select(func.count(EmergencyContact.id)).where(
                EmergencyContact.user_id == current_user.id
            )
        )
        contact_count = result.scalar()
        
        if contact_count >= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum of 5 emergency contacts allowed"
            )
        
        # If this is marked as primary, unset other primary contacts
        if contact_data.is_primary:
            await db.execute(
                update(EmergencyContact)
                .where(EmergencyContact.user_id == current_user.id)
                .values(is_primary=False)
            )
        
        # Create new emergency contact
        new_contact = EmergencyContact(
            user_id=current_user.id,
            name=contact_data.name,
            phone_number=contact_data.phone_number,
            email=contact_data.email,
            relationship=contact_data.relationship,
            is_primary=contact_data.is_primary
        )
        
        db.add(new_contact)
        await db.commit()
        await db.refresh(new_contact)
        
        # Publish emergency contact created event
        await publish_user_event({
            "event_type": "emergency_contact_created",
            "user_id": str(current_user.id),
            "contact_id": str(new_contact.id),
            "contact_name": new_contact.name,
            "is_primary": new_contact.is_primary
        })
        
        return EmergencyContactResponse(
            id=new_contact.id,
            name=new_contact.name,
            phone_number=new_contact.phone_number,
            email=new_contact.email,
            relationship=new_contact.relationship,
            is_primary=new_contact.is_primary,
            created_at=new_contact.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create emergency contact: {str(e)}"
        )

@router.put("/emergency-contacts/{contact_id}", response_model=EmergencyContactResponse)
async def update_emergency_contact(
    contact_id: UUID,
    contact_data: EmergencyContactUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update an emergency contact."""
    try:
        # Get the contact
        result = await db.execute(
            select(EmergencyContact).where(
                EmergencyContact.id == contact_id,
                EmergencyContact.user_id == current_user.id
            )
        )
        contact = result.scalar_one_or_none()
        
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Emergency contact not found"
            )
        
        # If setting as primary, unset other primary contacts
        if contact_data.is_primary and not contact.is_primary:
            await db.execute(
                update(EmergencyContact)
                .where(
                    EmergencyContact.user_id == current_user.id,
                    EmergencyContact.id != contact_id
                )
                .values(is_primary=False)
            )
        
        # Update contact fields
        if contact_data.name is not None:
            contact.name = contact_data.name
        if contact_data.phone_number is not None:
            contact.phone_number = contact_data.phone_number
        if contact_data.email is not None:
            contact.email = contact_data.email
        if contact_data.relationship is not None:
            contact.relationship = contact_data.relationship
        if contact_data.is_primary is not None:
            contact.is_primary = contact_data.is_primary
        
        await db.commit()
        await db.refresh(contact)
        
        # Publish emergency contact updated event
        await publish_user_event({
            "event_type": "emergency_contact_updated",
            "user_id": str(current_user.id),
            "contact_id": str(contact.id),
            "updated_fields": contact_data.dict(exclude_unset=True)
        })
        
        return EmergencyContactResponse(
            id=contact.id,
            name=contact.name,
            phone_number=contact.phone_number,
            email=contact.email,
            relationship=contact.relationship,
            is_primary=contact.is_primary,
            created_at=contact.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update emergency contact: {str(e)}"
        )

@router.delete("/emergency-contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_emergency_contact(
    contact_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Delete an emergency contact."""
    try:
        # Get the contact
        result = await db.execute(
            select(EmergencyContact).where(
                EmergencyContact.id == contact_id,
                EmergencyContact.user_id == current_user.id
            )
        )
        contact = result.scalar_one_or_none()
        
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Emergency contact not found"
            )
        
        await db.delete(contact)
        await db.commit()
        
        # Publish emergency contact deleted event
        await publish_user_event({
            "event_type": "emergency_contact_deleted",
            "user_id": str(current_user.id),
            "contact_id": str(contact_id),
            "contact_name": contact.name
        })
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete emergency contact: {str(e)}"
        )

@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get user's preferences."""
    try:
        result = await db.execute(
            select(UserPreferences).where(UserPreferences.user_id == current_user.id)
        )
        preferences = result.scalar_one_or_none()
        
        if not preferences:
            # Create default preferences
            preferences = UserPreferences(
                user_id=current_user.id,
                silent_mode=False,
                auto_location_sharing=True,
                emergency_contacts_notification=True,
                push_notifications=True,
                sms_notifications=True,
                email_notifications=False
            )
            db.add(preferences)
            await db.commit()
            await db.refresh(preferences)
        
        return UserPreferencesResponse(
            silent_mode=preferences.silent_mode,
            auto_location_sharing=preferences.auto_location_sharing,
            emergency_contacts_notification=preferences.emergency_contacts_notification,
            push_notifications=preferences.push_notifications,
            sms_notifications=preferences.sms_notifications,
            email_notifications=preferences.email_notifications,
            updated_at=preferences.updated_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user preferences: {str(e)}"
        )

@router.put("/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    preferences_data: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update user's preferences."""
    try:
        result = await db.execute(
            select(UserPreferences).where(UserPreferences.user_id == current_user.id)
        )
        preferences = result.scalar_one_or_none()
        
        if not preferences:
            # Create new preferences
            preferences = UserPreferences(user_id=current_user.id)
            db.add(preferences)
        
        # Update preference fields
        if preferences_data.silent_mode is not None:
            preferences.silent_mode = preferences_data.silent_mode
        if preferences_data.auto_location_sharing is not None:
            preferences.auto_location_sharing = preferences_data.auto_location_sharing
        if preferences_data.emergency_contacts_notification is not None:
            preferences.emergency_contacts_notification = preferences_data.emergency_contacts_notification
        if preferences_data.push_notifications is not None:
            preferences.push_notifications = preferences_data.push_notifications
        if preferences_data.sms_notifications is not None:
            preferences.sms_notifications = preferences_data.sms_notifications
        if preferences_data.email_notifications is not None:
            preferences.email_notifications = preferences_data.email_notifications
        
        await db.commit()
        await db.refresh(preferences)
        
        # Publish user preferences updated event
        await publish_user_event({
            "event_type": "user_preferences_updated",
            "user_id": str(current_user.id),
            "updated_preferences": preferences_data.dict(exclude_unset=True)
        })
        
        return UserPreferencesResponse(
            silent_mode=preferences.silent_mode,
            auto_location_sharing=preferences.auto_location_sharing,
            emergency_contacts_notification=preferences.emergency_contacts_notification,
            push_notifications=preferences.push_notifications,
            sms_notifications=preferences.sms_notifications,
            email_notifications=preferences.email_notifications,
            updated_at=preferences.updated_at
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user preferences: {str(e)}"
        )

# Import required SQLAlchemy functions
from sqlalchemy import select, update, func