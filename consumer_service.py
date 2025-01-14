from kafka_consumer import TranscriptConsumer

def run_consumer_service():
    consumer = TranscriptConsumer()
    consumer.start_consuming()

if __name__ == "__main__":
    run_consumer_service()