#!/bin/bash

# Kafka Topics Setup Script
# Run this script after Kafka is running to create necessary topics

KAFKA_CONTAINER="kafka"
KAFKA_BROKER="localhost:9092"

echo "Creating Kafka topics for Panic Alert System..."

# Alert-related topics
docker exec $KAFKA_CONTAINER kafka-topics --create --topic panic-alerts --bootstrap-server $KAFKA_BROKER --partitions 3 --replication-factor 1
docker exec $KAFKA_CONTAINER kafka-topics --create --topic alert-responses --bootstrap-server $KAFKA_BROKER --partitions 3 --replication-factor 1
docker exec $KAFKA_CONTAINER kafka-topics --create --topic alert-status-updates --bootstrap-server $KAFKA_BROKER --partitions 3 --replication-factor 1

# User and agent topics
docker exec $KAFKA_CONTAINER kafka-topics --create --topic user-events --bootstrap-server $KAFKA_BROKER --partitions 2 --replication-factor 1
docker exec $KAFKA_CONTAINER kafka-topics --create --topic agent-events --bootstrap-server $KAFKA_BROKER --partitions 2 --replication-factor 1

# Location and geofencing topics
docker exec $KAFKA_CONTAINER kafka-topics --create --topic location-updates --bootstrap-server $KAFKA_BROKER --partitions 3 --replication-factor 1
docker exec $KAFKA_CONTAINER kafka-topics --create --topic geofence-events --bootstrap-server $KAFKA_BROKER --partitions 2 --replication-factor 1

# Media and multimedia topics
docker exec $KAFKA_CONTAINER kafka-topics --create --topic media-uploads --bootstrap-server $KAFKA_BROKER --partitions 2 --replication-factor 1
docker exec $KAFKA_CONTAINER kafka-topics --create --topic media-processing --bootstrap-server $KAFKA_BROKER --partitions 2 --replication-factor 1

# Notification topics
docker exec $KAFKA_CONTAINER kafka-topics --create --topic push-notifications --bootstrap-server $KAFKA_BROKER --partitions 3 --replication-factor 1
docker exec $KAFKA_CONTAINER kafka-topics --create --topic sms-notifications --bootstrap-server $KAFKA_BROKER --partitions 2 --replication-factor 1
docker exec $KAFKA_CONTAINER kafka-topics --create --topic email-notifications --bootstrap-server $KAFKA_BROKER --partitions 2 --replication-factor 1

# System and audit topics
docker exec $KAFKA_CONTAINER kafka-topics --create --topic system-events --bootstrap-server $KAFKA_BROKER --partitions 2 --replication-factor 1
docker exec $KAFKA_CONTAINER kafka-topics --create --topic audit-logs --bootstrap-server $KAFKA_BROKER --partitions 2 --replication-factor 1

echo "Listing created topics:"
docker exec $KAFKA_CONTAINER kafka-topics --list --bootstrap-server $KAFKA_BROKER

echo "Kafka topics created successfully!"