# kafka_producer.py
from confluent_kafka import Producer
import json
import base64
import os
import uuid

class TranscriptProducer:
    def __init__(self, bootstrap_servers='localhost:9092'):
        self.producer = Producer({
            'bootstrap.servers': bootstrap_servers,
            'client.id': 'transcript-producer',
            'socket.timeout.ms': 10000,
            'request.timeout.ms': 20000
        })
        self.topics = {
            'pdf': 'transcript_uploads',
            'realtime': 'realtime_transcripts'
        }

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
                self.topics['pdf'],
                value=json.dumps(file_data).encode('utf-8'),
                callback=self.delivery_report
            )
            self.producer.flush()
            return True
        except Exception as e:
            print(f"Error sending to Kafka: {str(e)}")
            return False
            
    def send_realtime_chunk(self, text_chunk, session_id=None):
        try:
            if session_id is None:
                session_id = str(uuid.uuid4())
                
            chunk_data = {
                'session_id': session_id,
                'text_chunk': text_chunk
            }
            
            self.producer.produce(
                self.topics['realtime'],
                value=json.dumps(chunk_data).encode('utf-8'),
                callback=self.delivery_report
            )
            self.producer.flush()
            return session_id
        except Exception as e:
            print(f"Error sending realtime chunk to Kafka: {str(e)}")
            return None