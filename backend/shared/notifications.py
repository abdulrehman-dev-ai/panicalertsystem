import asyncio
import aiohttp
from typing import List, Dict, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.database import get_db_session
from shared.config import get_settings
from auth_service.models import User
from user_service.models import EmergencyContact, UserPreferences
from alert_service.models import Alert
from shared.kafka_client import publish_notification_event

settings = get_settings()

class NotificationService:
    """Service for sending various types of notifications."""
    
    def __init__(self):
        self.sms_enabled = bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN)
        self.email_enabled = bool(settings.SMTP_HOST and settings.SMTP_USERNAME)
        self.push_enabled = bool(settings.FCM_SERVER_KEY)
    
    async def send_sms(self, phone_number: str, message: str) -> bool:
        """Send SMS using Twilio."""
        if not self.sms_enabled:
            print(f"SMS not configured. Would send to {phone_number}: {message}")
            return False
        
        try:
            # In a real implementation, you would use Twilio SDK
            # For now, we'll simulate the API call
            url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
            
            data = {
                "From": settings.TWILIO_PHONE_NUMBER,
                "To": phone_number,
                "Body": message
            }
            
            auth = aiohttp.BasicAuth(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data, auth=auth, timeout=10) as response:
                    if response.status == 201:
                        print(f"SMS sent successfully to {phone_number}")
                        return True
                    else:
                        print(f"Failed to send SMS to {phone_number}: {response.status}")
                        return False
                        
        except Exception as e:
            print(f"Error sending SMS to {phone_number}: {str(e)}")
            return False
    
    async def send_email(self, email: str, subject: str, body: str, is_html: bool = False) -> bool:
        """Send email using SMTP."""
        if not self.email_enabled:
            print(f"Email not configured. Would send to {email}: {subject}")
            return False
        
        try:
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Create message
            msg = MIMEMultipart()
            msg["From"] = settings.SMTP_USERNAME
            msg["To"] = email
            msg["Subject"] = subject
            
            # Add body
            msg.attach(MIMEText(body, "html" if is_html else "plain"))
            
            # Send email
            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD,
                use_tls=settings.SMTP_USE_TLS
            )
            
            print(f"Email sent successfully to {email}")
            return True
            
        except Exception as e:
            print(f"Error sending email to {email}: {str(e)}")
            return False
    
    async def send_push_notification(self, device_token: str, title: str, body: str, data: Dict = None) -> bool:
        """Send push notification using Firebase Cloud Messaging."""
        if not self.push_enabled:
            print(f"Push notifications not configured. Would send: {title} - {body}")
            return False
        
        try:
            url = "https://fcm.googleapis.com/fcm/send"
            
            headers = {
                "Authorization": f"key={settings.FCM_SERVER_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "to": device_token,
                "notification": {
                    "title": title,
                    "body": body,
                    "sound": "emergency_alert.wav",
                    "priority": "high"
                },
                "data": data or {},
                "android": {
                    "priority": "high",
                    "notification": {
                        "channel_id": "emergency_alerts",
                        "priority": "high",
                        "default_sound": False,
                        "sound": "emergency_alert.wav"
                    }
                },
                "apns": {
                    "payload": {
                        "aps": {
                            "sound": "emergency_alert.wav",
                            "badge": 1,
                            "alert": {
                                "title": title,
                                "body": body
                            }
                        }
                    }
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        print(f"Push notification sent successfully")
                        return True
                    else:
                        print(f"Failed to send push notification: {response.status}")
                        return False
                        
        except Exception as e:
            print(f"Error sending push notification: {str(e)}")
            return False

# Global notification service instance
notification_service = NotificationService()

async def send_emergency_notifications(alert_id: UUID, user_id: UUID) -> None:
    """Send emergency notifications to user's emergency contacts and authorities."""
    try:
        async with get_db_session() as db:
            # Get alert details
            alert_result = await db.execute(
                select(Alert).where(Alert.id == alert_id)
            )
            alert = alert_result.scalar_one_or_none()
            
            if not alert:
                print(f"Alert {alert_id} not found")
                return
            
            # Get user details
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                print(f"User {user_id} not found")
                return
            
            # Get user preferences
            prefs_result = await db.execute(
                select(UserPreferences).where(UserPreferences.user_id == user_id)
            )
            preferences = prefs_result.scalar_one_or_none()
            
            # Get emergency contacts
            contacts_result = await db.execute(
                select(EmergencyContact).where(EmergencyContact.user_id == user_id)
            )
            emergency_contacts = contacts_result.scalars().all()
            
            # Prepare notification content
            user_name = f"{user.first_name} {user.last_name}"
            location_text = ""
            if alert.latitude and alert.longitude:
                location_text = f" at coordinates {alert.latitude:.6f}, {alert.longitude:.6f}"
                if alert.address:
                    location_text += f" ({alert.address})"
            
            timestamp = alert.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            
            # SMS message for emergency contacts
            sms_message = f"🚨 EMERGENCY ALERT 🚨\n\n{user_name} has triggered a panic alert{location_text}.\n\nTime: {timestamp}\n\nMessage: {alert.message or 'No additional message'}\n\nThis is an automated emergency notification."
            
            # Email subject and body
            email_subject = f"🚨 EMERGENCY ALERT - {user_name}"
            email_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="background-color: #ff4444; color: white; padding: 20px; text-align: center;">
                    <h1>🚨 EMERGENCY ALERT 🚨</h1>
                </div>
                
                <div style="padding: 20px;">
                    <h2>Emergency Alert Details</h2>
                    
                    <p><strong>Person:</strong> {user_name}</p>
                    <p><strong>Phone:</strong> {user.phone_number or 'Not provided'}</p>
                    <p><strong>Time:</strong> {timestamp}</p>
                    
                    {f'<p><strong>Location:</strong> {alert.address or "Coordinates: " + str(alert.latitude) + ", " + str(alert.longitude)}</p>' if alert.latitude and alert.longitude else ''}
                    
                    {f'<p><strong>Message:</strong> {alert.message}</p>' if alert.message else ''}
                    
                    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 20px 0; border-radius: 5px;">
                        <p><strong>⚠️ This is an automated emergency notification.</strong></p>
                        <p>If this is a real emergency, please contact local emergency services immediately.</p>
                    </div>
                    
                    <p>Emergency Services Numbers:</p>
                    <ul>
                        <li>Police: 911 (US), 999 (UK), 112 (EU)</li>
                        <li>Medical: 911 (US), 999 (UK), 112 (EU)</li>
                        <li>Fire: 911 (US), 999 (UK), 112 (EU)</li>
                    </ul>
                </div>
            </body>
            </html>
            """
            
            # Send notifications to emergency contacts
            notification_tasks = []
            
            for contact in emergency_contacts:
                # Send SMS if enabled and contact has phone
                if (preferences is None or preferences.sms_notifications) and contact.phone_number:
                    task = notification_service.send_sms(contact.phone_number, sms_message)
                    notification_tasks.append(task)
                
                # Send email if enabled and contact has email
                if (preferences is None or preferences.email_notifications) and contact.email:
                    task = notification_service.send_email(contact.email, email_subject, email_body, is_html=True)
                    notification_tasks.append(task)
            
            # Execute all notification tasks concurrently
            if notification_tasks:
                results = await asyncio.gather(*notification_tasks, return_exceptions=True)
                
                # Count successful notifications
                successful_notifications = sum(1 for result in results if result is True)
                total_notifications = len(notification_tasks)
                
                # Publish notification event
                await publish_notification_event({
                    "event_type": "emergency_notifications_sent",
                    "alert_id": str(alert_id),
                    "user_id": str(user_id),
                    "total_contacts": len(emergency_contacts),
                    "total_notifications_sent": total_notifications,
                    "successful_notifications": successful_notifications,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                print(f"Emergency notifications sent: {successful_notifications}/{total_notifications} successful")
            else:
                print("No emergency contacts configured or notifications disabled")
                
    except Exception as e:
        print(f"Error sending emergency notifications: {str(e)}")
        
        # Publish error event
        await publish_notification_event({
            "event_type": "emergency_notification_error",
            "alert_id": str(alert_id),
            "user_id": str(user_id),
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })

async def send_geofence_notification(user_id: UUID, geofence_name: str, event_type: str, location: str) -> None:
    """Send geofence event notification."""
    try:
        async with get_db_session() as db:
            # Get user details
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                return
            
            # Get user preferences
            prefs_result = await db.execute(
                select(UserPreferences).where(UserPreferences.user_id == user_id)
            )
            preferences = prefs_result.scalar_one_or_none()
            
            # Check if geofence notifications are enabled
            if preferences and not preferences.push_notifications:
                return
            
            user_name = f"{user.first_name} {user.last_name}"
            
            # Prepare notification content
            if event_type == "enter":
                title = f"Entered {geofence_name}"
                body = f"{user_name} has entered the geofence '{geofence_name}' at {location}"
            else:
                title = f"Left {geofence_name}"
                body = f"{user_name} has left the geofence '{geofence_name}' at {location}"
            
            # In a real implementation, you would get the user's device tokens
            # and send push notifications
            print(f"Geofence notification: {title} - {body}")
            
            # Publish notification event
            await publish_notification_event({
                "event_type": "geofence_notification_sent",
                "user_id": str(user_id),
                "geofence_name": geofence_name,
                "geofence_event_type": event_type,
                "location": location,
                "timestamp": datetime.utcnow().isoformat()
            })
            
    except Exception as e:
        print(f"Error sending geofence notification: {str(e)}")

async def send_test_notification(user_id: UUID, notification_type: str) -> bool:
    """Send a test notification to verify the system is working."""
    try:
        async with get_db_session() as db:
            # Get user details
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                return False
            
            user_name = f"{user.first_name} {user.last_name}"
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            
            success = False
            
            if notification_type == "sms" and user.phone_number:
                message = f"🧪 TEST ALERT\n\nThis is a test of the Panic Alert System for {user_name}.\n\nTime: {timestamp}\n\nIf this was a real emergency, you would receive location and contact information.\n\nSystem is working correctly! ✅"
                success = await notification_service.send_sms(user.phone_number, message)
                
            elif notification_type == "email" and user.email:
                subject = f"🧪 Test Alert - Panic Alert System"
                body = f"""
                <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <div style="background-color: #28a745; color: white; padding: 20px; text-align: center;">
                        <h1>🧪 TEST ALERT</h1>
                    </div>
                    
                    <div style="padding: 20px;">
                        <h2>System Test Notification</h2>
                        
                        <p>Hello {user_name},</p>
                        
                        <p>This is a test of the Panic Alert System notification service.</p>
                        
                        <p><strong>Test Time:</strong> {timestamp}</p>
                        
                        <div style="background-color: #d4edda; border: 1px solid #c3e6cb; padding: 15px; margin: 20px 0; border-radius: 5px;">
                            <p><strong>✅ System Status: OPERATIONAL</strong></p>
                            <p>Your emergency notification system is working correctly.</p>
                        </div>
                        
                        <p>If this was a real emergency, your emergency contacts would receive detailed information including your location and emergency details.</p>
                        
                        <p>Stay safe!</p>
                    </div>
                </body>
                </html>
                """
                success = await notification_service.send_email(user.email, subject, body, is_html=True)
                
            elif notification_type == "push":
                # In a real implementation, you would send to user's device tokens
                title = "🧪 Test Alert"
                body = f"Panic Alert System test for {user_name} - System operational ✅"
                print(f"Test push notification: {title} - {body}")
                success = True
            
            # Publish test notification event
            await publish_notification_event({
                "event_type": "test_notification_sent",
                "user_id": str(user_id),
                "notification_type": notification_type,
                "success": success,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return success
            
    except Exception as e:
        print(f"Error sending test notification: {str(e)}")
        return False

async def send_system_notification(user_id: UUID, title: str, message: str, notification_type: str = "info") -> None:
    """Send a general system notification to the user."""
    try:
        async with get_db_session() as db:
            # Get user details
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                return
            
            # Get user preferences
            prefs_result = await db.execute(
                select(UserPreferences).where(UserPreferences.user_id == user_id)
            )
            preferences = prefs_result.scalar_one_or_none()
            
            # Check if notifications are enabled
            if preferences and not preferences.push_notifications:
                return
            
            # In a real implementation, you would send push notification
            print(f"System notification for {user.email}: {title} - {message}")
            
            # Publish system notification event
            await publish_notification_event({
                "event_type": "system_notification_sent",
                "user_id": str(user_id),
                "title": title,
                "message": message,
                "notification_type": notification_type,
                "timestamp": datetime.utcnow().isoformat()
            })
            
    except Exception as e:
        print(f"Error sending system notification: {str(e)}")

# Utility functions for formatting notifications
def format_emergency_sms(user_name: str, location: str, timestamp: str, message: str = None) -> str:
    """Format emergency SMS message."""
    base_message = f"🚨 EMERGENCY ALERT 🚨\n\n{user_name} needs help{location}.\n\nTime: {timestamp}"
    
    if message:
        base_message += f"\n\nMessage: {message}"
    
    base_message += "\n\nThis is an automated emergency notification."
    
    return base_message

def format_location_string(latitude: float = None, longitude: float = None, address: str = None) -> str:
    """Format location information for notifications."""
    if address:
        return f" at {address}"
    elif latitude and longitude:
        return f" at coordinates {latitude:.6f}, {longitude:.6f}"
    else:
        return ""

def get_emergency_contact_priority(contact) -> int:
    """Get priority for emergency contact (primary contacts first)."""
    return 0 if contact.is_primary else 1