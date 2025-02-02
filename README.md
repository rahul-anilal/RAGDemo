
# MeetBot  

Online meetings often lack effective question-and-answer dynamics, hampering professional engagement.
This project introduces an interactive conversational agent, using Large Language Models, to enhance real-time questioning and fosters a more interactive and productive virtual meeting environment for working professionals. The goal is to streamline information retrieval and elevate the quality of online professional interactions.


## Project Highlights

- LLM based question and answer system that will use following:
  - Google Gemini-Pro LLM
  - FAISS embeddings
  - Streamlit for UI
  - Langchain framework
  - FAISS LOCAL STORE as a vector store
  - Few/One shot learning
- In the UI, the meeting participant will ask their questions in natural language, and it will produce the answers accordingly.


## Installation

1. Clone this repository to your local machine using:

```bash
  git clone https://github.com/Skriller18/MeetBot.git
```
2. Navigate to the project directory:

```bash
  cd MeetBot
```
3. Create Environment:
```bash
  conda create -n "myenv" python=3.10.0
```

4. Install the required dependencies using pip:

```bash
  pip install -r requirements.txt
```
5. Install and setup Kafka

```bash
  wget https://downloads.apache.org/kafka/3.9.0/kafka-3.9.0-src.tgz
  tar -xzf kafka-3.9.0-src.tgz
  cd kafka-3.9.0-src.tgz

  bin/zookeeper-server-start.sh config/zookeeper.properties
  bin/kafka-server-start.sh config/server.properties
```

6. Acquire an api key through makersuite.google.com or Google AI studio and put it in a .env file:

```bash
  GOOGLE_API_KEY="your_api_key_here"
  LAXIS_API_KEY ="your_api_key_here"
```

7. Create Kafka topics and stream pipeline
```bash
  bin/kafka-topics.sh --delete --bootstrap-server localhost:9092 --topic realtime_transcripts --partitions 1 --replication-factor 1
  bin/kafka-topics.sh --delete --bootstrap-server localhost:9092 --topic processing_status --partitions 1 --replication-factor 1
  bin/kafka-topics.sh --delete --bootstrap-server localhost:9092 --topic transcript_analytics --partitions 1 --replication-factor 1
  bin/kafka-topics.sh --delete --bootstrap-server localhost:9092 --topic transcript_uploads --partitions 1 --replication-factor 1

  bin/kafka-topics.sh --list --bootstrap-server localhost:9092
```

## Usage

1. Run the Kafka Consumer client
```bash
python consumer_service.py
```

2. In a paralell terminal, Run the Streamlit app by executing:
```bash
streamlit run main.py
```

2. The web app will open in your browser where you can ask questions related to the meet:s

## Architecture
![Alt Text](architecture.jpg)


## Sample Output
![Alt Text](sample.jpg)

