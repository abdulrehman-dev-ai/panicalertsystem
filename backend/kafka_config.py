import asyncio
import json
import logging
from typing import Optional, Dict, Any, List
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class KafkaConfig:
    """Kafka configuration and connection management."""
    
    def __init__(self):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumers: Dict[str, AIOKafkaConsumer] = {}
        
        # Topic configurations
        self.topics = {
            "emergency_alerts": {
                "partitions": 3,
                "replication_factor": 1,
                "config": {
                    "retention.ms": "604800000",  # 7 days
                    "cleanup.policy": "delete"
                }
            },
            "location_updates": {
                "partitions": 5,
                "replication_factor": 1,
                "config": {
                    "retention.ms": "86400000",  # 1 day
                    "cleanup.policy": "delete"
                }
            },
            "geofence_events": {
                "partitions": 3,
                "replication_factor": 1,
                "config": {
                    "retention.ms": "259200000",  # 3 days
                    "cleanup.policy": "delete"
                }
            },
            "agent_updates": {
                "partitions": 2,
                "replication_factor": 1,
                "config": {
                    "retention.ms": "86400000",  # 1 day
                    "cleanup.policy": "delete"
                }
            },
            "notifications": {
                "partitions": 3,
                "replication_factor": 1,
                "config": {
                    "retention.ms": "172800000",  # 2 days
                    "cleanup.policy": "delete"
                }
            },
            "media_processing": {
                "partitions": 2,
                "replication_factor": 1,
                "config": {
                    "retention.ms": "86400000",  # 1 day
                    "cleanup.policy": "delete"
                }
            }
        }
    
    async def create_producer(self) -> AIOKafkaProducer:
        """Create and start Kafka producer."""
        try:
            producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=1,
                enable_idempotence=True,
                compression_type='gzip'
            )
            
            await producer.start()
            logger.info("Kafka producer started successfully")
            return producer
            
        except Exception as e:
            logger.error(f"Failed to create Kafka producer: {e}")
            raise
    
    async def create_consumer(self, topics: List[str], group_id: str) -> AIOKafkaConsumer:
        """Create and start Kafka consumer."""
        try:
            consumer = AIOKafkaConsumer(
                *topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')) if m else None,
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000
            )
            
            await consumer.start()
            logger.info(f"Kafka consumer started for topics: {topics}, group: {group_id}")
            return consumer
            
        except Exception as e:
            logger.error(f"Failed to create Kafka consumer: {e}")
            raise
    
    async def send_message(self, topic: str, message: Dict[Any, Any], key: Optional[str] = None) -> bool:
        """Send message to Kafka topic."""
        try:
            if not self.producer:
                logger.error("Kafka producer not initialized")
                return False
            
            # Add timestamp to message
            message['timestamp'] = datetime.utcnow().isoformat()
            
            # Send message
            await self.producer.send(topic, value=message, key=key)
            logger.debug(f"Message sent to topic '{topic}': {message}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to topic '{topic}': {e}")
            return False
    
    async def close_producer(self):
        """Close Kafka producer."""
        if self.producer:
            try:
                await self.producer.stop()
                logger.info("Kafka producer closed")
            except Exception as e:
                logger.error(f"Error closing Kafka producer: {e}")
    
    async def close_consumer(self, consumer: AIOKafkaConsumer):
        """Close Kafka consumer."""
        try:
            await consumer.stop()
            logger.info("Kafka consumer closed")
        except Exception as e:
            logger.error(f"Error closing Kafka consumer: {e}")
    
    async def close_all_consumers(self):
        """Close all Kafka consumers."""
        for consumer_name, consumer in self.consumers.items():
            try:
                await consumer.stop()
                logger.info(f"Kafka consumer '{consumer_name}' closed")
            except Exception as e:
                logger.error(f"Error closing Kafka consumer '{consumer_name}': {e}")
        
        self.consumers.clear()

# Global Kafka configuration instance
kafka_config = KafkaConfig()

# Convenience functions
async def init_kafka():
    """Initialize Kafka connections."""
    try:
        kafka_config.producer = await kafka_config.create_producer()
        logger.info("Kafka initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Kafka: {e}")
        raise

async def close_kafka():
    """Close all Kafka connections."""
    try:
        await kafka_config.close_producer()
        await kafka_config.close_all_consumers()
        logger.info("All Kafka connections closed")
    except Exception as e:
        logger.error(f"Error closing Kafka connections: {e}")

async def get_kafka_producer() -> Optional[AIOKafkaProducer]:
    """Get the global Kafka producer."""
    return kafka_config.producer

async def send_kafka_message(topic: str, message: Dict[Any, Any], key: Optional[str] = None) -> bool:
    """Send message to Kafka topic."""
    return await kafka_config.send_message(topic, message, key)

async def create_kafka_consumer(topics: List[str], group_id: str) -> AIOKafkaConsumer:
    """Create a new Kafka consumer."""
    consumer = await kafka_config.create_consumer(topics, group_id)
    kafka_config.consumers[group_id] = consumer
    return consumer

# Message schemas for different topics
class MessageSchemas:
    """Standard message schemas for Kafka topics."""
    
    @staticmethod
    def emergency_alert(alert_id: str, user_id: str, alert_type: str, location: Dict, severity: str, message: str) -> Dict:
        return {
            "alert_id": alert_id,
            "user_id": user_id,
            "alert_type": alert_type,
            "location": location,
            "severity": severity,
            "message": message,
            "created_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def location_update(user_id: str, latitude: float, longitude: float, accuracy: float, speed: Optional[float] = None) -> Dict:
        return {
            "user_id": user_id,
            "latitude": latitude,
            "longitude": longitude,
            "accuracy": accuracy,
            "speed": speed,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def geofence_event(user_id: str, geofence_id: str, event_type: str, location: Dict) -> Dict:
        return {
            "user_id": user_id,
            "geofence_id": geofence_id,
            "event_type": event_type,  # enter, exit, dwell
            "location": location,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def agent_update(agent_id: str, status: str, location: Dict, incident_id: Optional[str] = None) -> Dict:
        return {
            "agent_id": agent_id,
            "status": status,
            "location": location,
            "incident_id": incident_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def notification(user_id: str, notification_type: str, title: str, message: str, data: Optional[Dict] = None) -> Dict:
        return {
            "user_id": user_id,
            "notification_type": notification_type,
            "title": title,
            "message": message,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def media_processing(media_id: str, user_id: str, operation: str, status: str, file_path: str) -> Dict:
        return {
            "media_id": media_id,
            "user_id": user_id,
            "operation": operation,  # upload, process, delete
            "status": status,  # pending, processing, completed, failed
            "file_path": file_path,
            "timestamp": datetime.utcnow().isoformat()
        }