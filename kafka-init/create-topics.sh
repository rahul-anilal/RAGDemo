#!/bin/bash
set -e

# Wait for Kafka to be ready
cub kafka-ready -b localhost:9092 1 20

# Create topics
kafka-topics.sh --create --topic processing_status --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
kafka-topics.sh --create --topic transcript_analytics --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

echo "Kafka topics created."