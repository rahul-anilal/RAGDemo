import streamlit as st
import pandas as pd
from kafka_producer import TranscriptProducer
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
from monitor import StreamlitMonitoring

def get_conversational_chain():
    prompt_template = """
    Analyze the conversation thoroughly, considering each participant's input, and provide a comprehensive response. If specific details are not available, indicate "Information not found in the context." Avoid guessing or providing inaccurate information. If the required details are not in the meeting context, you may search the internet for factual information.\n\n

    Context:\n {context}?\n
    Question: \n{question}\n

    Detailed Answer:
    """
    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.6)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    return load_qa_chain(model, chain_type="stuff", prompt=prompt)

def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    docs = new_db.similarity_search(user_question)
    response = get_conversational_chain()(
        {"input_documents": docs, "question": user_question},
        return_only_outputs=True
    )
    return response["output_text"]

def render_analytics(analytics_summary):
    if not analytics_summary:
        st.sidebar.warning("No analytics data available yet")
        return
        
    st.sidebar.header("Analytics")
    
    # Display basic metrics
    col1, col2, col3 = st.sidebar.columns(3)
    with col1:
        st.metric("Total Transcripts", analytics_summary['total_transcripts'])
    with col2:
        st.metric("Total Words", analytics_summary['total_words'])
    with col3:
        st.metric("Avg Words/Transcript", f"{analytics_summary['average_words_per_transcript']:.0f}")
    
    # Display sentiment
    st.sidebar.metric("Overall Sentiment", f"{analytics_summary['overall_sentiment']:.2f}")
    
    # Display word frequency
    st.sidebar.subheader("Most Common Words")
    if analytics_summary['most_common_words']:
        word_freq_df = pd.DataFrame(
            analytics_summary['most_common_words'].items(),
            columns=['Word', 'Frequency']
        )
        st.sidebar.bar_chart(word_freq_df.set_index('Word'))
    else:
        st.sidebar.info("No word frequency data available")

def render_status_updates(monitoring, file_ids):
    st.sidebar.subheader("Processing Status")
    if not file_ids:
        st.sidebar.info("No files uploaded yet")
        return
        
    for filename, file_id in file_ids.items():
        status = monitoring.get_latest_status(file_id)
        if status:
            with st.sidebar.expander(f"File: {filename}", expanded=True):
                st.write(f"Status: {status.status}")
                if status.details:
                    for key, value in status.details.items():
                        st.write(f"{key.title()}: {value}")
                st.write(f"Last Updated: {status.timestamp}")
        else:
            st.sidebar.warning(f"No status updates for {filename}")

def main():
    st.set_page_config(
        page_title="MEETBOT",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialize session state
    for key in ['monitoring', 'file_ids', 'realtime_session_id', 'chat_history']:
        if key not in st.session_state:
            st.session_state[key] = None if key != 'chat_history' else []
    
    if not st.session_state.monitoring:
        st.session_state.monitoring = StreamlitMonitoring()
        st.session_state.monitoring.start_monitoring()
        st.session_state.file_ids = {}

    # Left Sidebar - File Upload and Realtime Input
    with st.sidebar:
        st.title("Input Sources")
        
        # File Upload Section
        st.header("Upload Transcripts")
        pdf_docs = st.file_uploader(
            "Upload Transcript Files",
            accept_multiple_files=True
        )
        
        if st.button("Submit & Process PDFs"):
            producer = TranscriptProducer()
            with st.spinner("Processing..."):
                for pdf in pdf_docs:
                    success, file_id = producer.send_transcript(pdf)
                    if success:
                        st.session_state.file_ids[pdf.name] = file_id
                        st.success(f"Successfully sent {pdf.name}")
                    else:
                        st.error(f"Failed to process {pdf.name}")

        # Realtime Transcription Section
        st.header("Realtime Transcription")
        realtime_text = st.text_area("Enter text for realtime processing")
        
        if st.button("Process Realtime Text") and realtime_text:
            producer = TranscriptProducer()
            with st.spinner("Processing..."):
                session_id = producer.send_realtime_chunk(
                    realtime_text,
                    st.session_state.realtime_session_id
                )
                if session_id:
                    st.session_state.realtime_session_id = session_id
                    st.success("Successfully processed")
                else:
                    st.error("Failed to process")

    # Main Content Area - Chat Interface
    st.title("LangBot - Personal Assistant 🤖")
    
    # Chat input at the bottom
    user_question = st.text_input("Ask a question about the PDF files and text you uploaded...")
    
    if user_question:
        response = user_input(user_question)
        st.session_state.chat_history.append({"question": user_question, "answer": response})

    # Display chat history
    for chat in reversed(st.session_state.chat_history):
        with st.container():
            st.markdown("**You:** " + chat["question"])
            st.markdown("**MeetBot:** " + chat["answer"])
            st.markdown("---")

    # Right Sidebar - Status and Analytics
    update_type = st.session_state.monitoring.poll_updates()
    render_status_updates(st.session_state.monitoring, st.session_state.file_ids)
    render_analytics(st.session_state.monitoring.get_analytics_summary())

if __name__ == "__main__":
    main()