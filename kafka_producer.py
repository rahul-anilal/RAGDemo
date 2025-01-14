from confluent_kafka import Producer
import json
import base64
import os

class TranscriptProducer:
    def __init__(self, bootstrap_servers='localhost:9092'):
        self.producer = Producer({
            'bootstrap.servers': bootstrap_servers,
            'client.id': 'transcript-producer',
            'socket.timeout.ms': 10000,
            'request.timeout.ms': 20000
        })
        self.topic = 'transcript_uploads'

    def delivery_report(self, err, msg):
        if err is not None:
            print(f'Message delivery failed: {err}')
        else:
            print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

    def send_transcript(self, file_obj):
        try:
            file_content = base64.b64encode(file_obj.read()).decode('utf-8')
            file_data = {
                'filename': file_obj.name,
                'content': file_content
            }
            
            self.producer.produce(
                self.topic,
                value=json.dumps(file_data).encode('utf-8'),
                callback=self.delivery_report
            )
            self.producer.flush()
            return True
        except Exception as e:
            print(f"Error sending to Kafka: {str(e)}")
            return False
