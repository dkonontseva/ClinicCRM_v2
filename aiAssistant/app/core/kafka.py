import asyncio
import os
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
REQUEST_TOPIC = os.getenv("REQUEST_TOPIC")
RESPONSE_TOPIC = os.getenv("RESPONSE_TOPIC")
CONFIRMATION_TOPIC = os.getenv("CONFIRMATION_TOPIC")
ERROR_TOPIC = os.getenv("ERROR_TOPIC")

async def ensure_topics_exist():
    """Ensure all required Kafka topics exist"""
    admin_client = AIOKafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    try:
        await admin_client.start()
        
        # Get existing topics
        existing_topics = await admin_client.list_topics()
        
        # Define required topics
        required_topics = [
            REQUEST_TOPIC,
            RESPONSE_TOPIC,
            CONFIRMATION_TOPIC,
            ERROR_TOPIC
        ]
        
        # Create topics that don't exist
        topics_to_create = [
            NewTopic(name=topic, num_partitions=1, replication_factor=1)
            for topic in required_topics
            if topic not in existing_topics
        ]
        
        if topics_to_create:
            print(f"Creating Kafka topics: {[t.name for t in topics_to_create]}")
            await admin_client.create_topics(topics_to_create)
            print("Topics created successfully")
        else:
            print("All required Kafka topics already exist")
            
    except Exception as e:
        print(f"Error ensuring Kafka topics exist: {e}")
        raise
    finally:
        await admin_client.close()

async def wait_for_kafka(max_retries: int = 20, retry_delay: int = 5):
    """Wait for Kafka to be ready"""
    for i in range(max_retries):
        try:
            consumer = AIOKafkaConsumer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=f"health_check_{i}",
                auto_offset_reset="earliest",
                enable_auto_commit=False
            )
            await consumer.start()
            topics = await consumer.topics()
            print(f"Available topics: {topics}")
            await consumer.stop()
            print("Successfully connected to Kafka")
            return True
        except Exception as e:
            print(f"Attempt {i+1}/{max_retries} failed: {e}")
            if i < max_retries - 1:
                await asyncio.sleep(retry_delay)
    return False 