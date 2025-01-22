# kafka_consumer.py
from confluent_kafka import Consumer, KafkaError
from monitor import MonitoringProducer, TranscriptAnalytics
import json
import base64
from io import BytesIO
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
import google.generativeai as genai
import os
from dotenv import load_dotenv
import time

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class TranscriptConsumer:
    def __init__(self, bootstrap_servers='localhost:9092'):
        self.consumer = Consumer({
            'bootstrap.servers': bootstrap_servers,
            'group.id': 'transcript-processing-group',
            'auto.offset.reset': 'earliest',
            'socket.timeout.ms': 10000,
            'session.timeout.ms': 60000,
            'request.timeout.ms': 30000
        })
        self.topics = ['transcript_uploads', 'realtime_transcripts']
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=10000,
            chunk_overlap=1000
        )
        self.monitoring = MonitoringProducer(bootstrap_servers)
        self.analytics = TranscriptAnalytics()
        
    def load_or_create_vectorstore(self):
        try:
            return FAISS.load_local("faiss_index", self.embeddings, allow_dangerous_deserialization=True)
        except:
            return None
            
    def process_pdf_transcript(self, file_content, file_id):
        try:
            self.monitoring.send_status_update(
                file_id=file_id,
                status="PROCESSING",
                details={"stage": "text_extraction"}
            )
            
            # Extract text from PDF
            text = self.extract_text(file_content)
            
            # Perform analytics
            analytics_data = self.analytics.analyze_transcript(text)
            self.monitoring.send_analytics(analytics_data)
            
            self.monitoring.send_status_update(
                file_id=file_id,
                status="PROCESSING",
                details={"stage": "generating_embeddings"}
            )
            
            # Generate embeddings and update vector store
            text_chunks = self.text_splitter.split_text(text)
            vector_store = self.load_or_create_vectorstore()
            
            if vector_store is None:
                vector_store = FAISS.from_texts(text_chunks, embedding=self.embeddings)
            else:
                vector_store.add_texts(text_chunks)
                
            vector_store.save_local("faiss_index")
            
            self.monitoring.send_status_update(
                file_id=file_id,
                status="COMPLETED",
                details={"analytics": analytics_data}
            )
            
        except Exception as e:
            self.monitoring.send_status_update(
                file_id=file_id,
                status="FAILED",
                details={"error": str(e)}
            )
            raise e
        
    def process_realtime_transcript(self, text_chunk, session_id):
        text_chunks = self.text_splitter.split_text(text_chunk)
        vector_store = self.load_or_create_vectorstore()
        
        if vector_store is None:
            vector_store = FAISS.from_texts(text_chunks, embedding=self.embeddings)
        else:
            vector_store.add_texts(text_chunks)
            
        vector_store.save_local("faiss_index")
        print(f"Updated vector store with new text chunk from session {session_id}")
        
    def start_consuming(self):
        print("Starting to consume messages...")
        self.consumer.subscribe(self.topics)
        print(f"Subscribed to topics: {self.topics}")
        
        try:
            while True:
                msg = self.consumer.poll(1.0)
                
                if msg is None:
                    continue
                    
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        print("Reached end of partition")
                        continue
                    else:
                        print(f"Error: {msg.error()}")
                        break

                try:
                    print("Received message, processing...")
                    data = json.loads(msg.value().decode('utf-8'))
                    
                    if msg.topic() == 'transcript_uploads':
                        print(f"Processing PDF file: {data['filename']}")
                        self.process_pdf_transcript(data['content'], data['file_id'])
                        print(f"Successfully processed file: {data['filename']}")
                    else:  # realtime_transcripts topic
                        print(f"Processing realtime transcript chunk for session: {data['session_id']}")
                        self.process_realtime_transcript(data['text_chunk'], data['session_id'])
                        
                except Exception as e:
                    print(f"Error processing message: {str(e)}")
                
                time.sleep(1)  # Add small delay to prevent CPU overuse
                    
        except KeyboardInterrupt:
            print("Shutting down consumer...")
        finally:
            self.consumer.close()
            print("Consumer closed")