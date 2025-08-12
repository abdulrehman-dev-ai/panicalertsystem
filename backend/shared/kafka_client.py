from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from kafka import KafkaProducer, KafkaConsumer
import json
import asyncio
from typing import Dict, Any, Optional, Callable, List
import logging
from datetime import datetime
import uuid

from .config import settings

logger = logging.getLogger(__name__)

# Global Kafka clients
producer: Optional[AIOKafkaProducer] = None
consumers: Dict[str, AIOKafkaConsumer] = {}

class KafkaMessage:
    """Kafka message wrapper with metadata."""
    
    def __init__(self, data: Dict[Any, Any], message_type: str = "event"):
        self.id = str(uuid.uuid4())
        self.timestamp = datetime.utcnow().isoformat()
        self.message_type = message_type
        self.data = data
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "message_type": self.message_type,
            "data": self.data
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())

class KafkaClient:
    """Kafka client wrapper for producing and consuming messages."""
    
    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumers: Dict[str, AIOKafkaConsumer] = {}
        self.running_consumers: Dict[str, asyncio.Task] = {}
    
    async def start_producer(self):
        """Start Kafka producer."""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                compression_type='gzip',
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=1
            )
            await self.producer.start()
            logger.info("Kafka producer started successfully")
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            raise
    
    async def stop_producer(self):
        """Stop Kafka producer."""
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")
    
    async def publish_message(
        self, 
        topic: str, 
        message: Dict[str, Any], 
        key: Optional[str] = None,
        message_type: str = "event"
    ) -> bool:
        """Publish a message to Kafka topic."""
        if not self.producer:
            logger.error("Kafka producer not initialized")
            return False
        
        try:
            kafka_message = KafkaMessage(message, message_type)
            
            await self.producer.send_and_wait(
                topic=topic,
                value=kafka_message.to_dict(),
                key=key
            )
            
            logger.info(f"Message published to topic '{topic}': {kafka_message.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish message to topic '{topic}': {e}")
            return False
    
    async def create_consumer(
        self, 
        topics: List[str], 
        group_id: str,
        handler: Callable[[Dict[str, Any]], None]
    ) -> str:
        """Create and start a Kafka consumer."""
        consumer_id = f"{group_id}_{uuid.uuid4().hex[:8]}"
        
        try:
            consumer = AIOKafkaConsumer(
                *topics,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=group_id,
                auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                enable_auto_commit=True,
                auto_commit_interval_ms=1000
            )
            
            await consumer.start()
            self.consumers[consumer_id] = consumer
            
            # Start consumer task
            task = asyncio.create_task(
                self._consume_messages(consumer, handler, consumer_id)
            )
            self.running_consumers[consumer_id] = task
            
            logger.info(f"Consumer '{consumer_id}' started for topics: {topics}")
            return consumer_id
            
        except Exception as e:
            logger.error(f"Failed to create consumer for topics {topics}: {e}")
            raise
    
    async def _consume_messages(
        self, 
        consumer: AIOKafkaConsumer, 
        handler: Callable[[Dict[str, Any]], None],
        consumer_id: str
    ):
        """Internal method to consume messages."""
        try:
            async for message in consumer:
                try:
                    await handler(message.value)
                except Exception as e:
                    logger.error(f"Error handling message in consumer '{consumer_id}': {e}")
        except Exception as e:
            logger.error(f"Consumer '{consumer_id}' error: {e}")
        finally:
            logger.info(f"Consumer '{consumer_id}' stopped")
    
    async def stop_consumer(self, consumer_id: str):
        """Stop a specific consumer."""
        if consumer_id in self.running_consumers:
            self.running_consumers[consumer_id].cancel()
            del self.running_consumers[consumer_id]
        
        if consumer_id in self.consumers:
            await self.consumers[consumer_id].stop()
            del self.consumers[consumer_id]
            logger.info(f"Consumer '{consumer_id}' stopped")
    
    async def stop_all_consumers(self):
        """Stop all consumers."""
        for consumer_id in list(self.consumers.keys()):
            await self.stop_consumer(consumer_id)
        logger.info("All consumers stopped")

# Global Kafka client instance
kafka_client = KafkaClient()

# Convenience functions for common operations
async def init_kafka():
    """Initialize Kafka connections."""
    global kafka_client
    await kafka_client.start_producer()
    logger.info("Kafka initialized successfully")

async def close_kafka():
    """Close Kafka connections."""
    global kafka_client
    await kafka_client.stop_all_consumers()
    await kafka_client.stop_producer()
    logger.info("Kafka connections closed")

# Message publishing functions
async def publish_alert_event(alert_data: Dict[str, Any], alert_id: str):
    """Publish alert event to Kafka."""
    return await kafka_client.publish_message(
        topic=settings.KAFKA_TOPICS["PANIC_ALERTS"],
        message=alert_data,
        key=alert_id,
        message_type="alert_event"
    )

async def publish_location_update(location_data: Dict[str, Any], user_id: str):
    """Publish location update to Kafka."""
    return await kafka_client.publish_message(
        topic=settings.KAFKA_TOPICS["LOCATION_UPDATES"],
        message=location_data,
        key=user_id,
        message_type="location_update"
    )

async def publish_media_upload(media_data: Dict[str, Any], alert_id: str):
    """Publish media upload event to Kafka."""
    return await kafka_client.publish_message(
        topic=settings.KAFKA_TOPICS["MEDIA_UPLOADS"],
        message=media_data,
        key=alert_id,
        message_type="media_upload"
    )

async def publish_notification(notification_data: Dict[str, Any], user_id: str, notification_type: str = "push"):
    """Publish notification to appropriate Kafka topic."""
    topic_map = {
        "push": settings.KAFKA_TOPICS["PUSH_NOTIFICATIONS"],
        "sms": settings.KAFKA_TOPICS["SMS_NOTIFICATIONS"],
        "email": settings.KAFKA_TOPICS["EMAIL_NOTIFICATIONS"]
    }
    
    topic = topic_map.get(notification_type, settings.KAFKA_TOPICS["PUSH_NOTIFICATIONS"])
    
    return await kafka_client.publish_message(
        topic=topic,
        message=notification_data,
        key=user_id,
        message_type=f"{notification_type}_notification"
    )

async def publish_system_event(event_data: Dict[str, Any], event_id: str = None):
    """Publish system event to Kafka."""
    return await kafka_client.publish_message(
        topic=settings.KAFKA_TOPICS["SYSTEM_EVENTS"],
        message=event_data,
        key=event_id or str(uuid.uuid4()),
        message_type="system_event"
    )

# Consumer setup functions
async def setup_alert_consumer(handler: Callable[[Dict[str, Any]], None]):
    """Set up consumer for alert events."""
    return await kafka_client.create_consumer(
        topics=[settings.KAFKA_TOPICS["PANIC_ALERTS"]],
        group_id="alert-processor",
        handler=handler
    )

async def setup_notification_consumer(handler: Callable[[Dict[str, Any]], None]):
    """Set up consumer for notification events."""
    return await kafka_client.create_consumer(
        topics=[
            settings.KAFKA_TOPICS["PUSH_NOTIFICATIONS"],
            settings.KAFKA_TOPICS["SMS_NOTIFICATIONS"],
            settings.KAFKA_TOPICS["EMAIL_NOTIFICATIONS"]
        ],
        group_id="notification-processor",
        handler=handler
    )

async def setup_media_consumer(handler: Callable[[Dict[str, Any]], None]):
    """Set up consumer for media processing events."""
    return await kafka_client.create_consumer(
        topics=[settings.KAFKA_TOPICS["MEDIA_UPLOADS"]],
        group_id="media-processor",
        handler=handler
    )