from confluent_kafka import Consumer, KafkaError
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
        self.topic = 'transcript_uploads'
        
    def process_transcript(self, file_content):
        file_obj = BytesIO(base64.b64decode(file_content))
        pdf_reader = PdfReader(file_obj)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
            
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=10000,
            chunk_overlap=1000
        )
        text_chunks = text_splitter.split_text(text)
        
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vector_store = FAISS.from_texts(text_chunks, embedding=embeddings, allow_dangerous_deserialization=True)
        vector_store.save_local("faiss_index")
        
    def start_consuming(self):
        print("Starting to consume messages...")
        
        # Subscribe to topic
        self.consumer.subscribe([self.topic])
        print(f"Subscribed to topic: {self.topic}")
        
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
                    file_data = json.loads(msg.value().decode('utf-8'))
                    print(f"Processing file: {file_data['filename']}")
                    self.process_transcript(file_data['content'])
                    print(f"Successfully processed file: {file_data['filename']}")
                except Exception as e:
                    print(f"Error processing message: {str(e)}")
                
                time.sleep(1)  # Add small delay to prevent CPU overuse
                    
        except KeyboardInterrupt:
            print("Shutting down consumer...")
        finally:
            self.consumer.close()
            print("Consumer closed")