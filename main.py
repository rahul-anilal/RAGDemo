# main.py
import streamlit as st
from kafka_producer import TranscriptProducer
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain

def get_conversational_chain():
    prompt_template = """
    Analyze the conversation thoroughly, considering each participant's input, and provide a comprehensive response. If specific details are not available, indicate "Information not found in the context." Avoid guessing or providing inaccurate information. If the required details are not in the meeting context, you may search the internet for factual information.\n\n

    Context:\n {context}?\n
    Question: \n{question}\n

    Detailed Answer:
    """

    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.6)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    docs = new_db.similarity_search(user_question)
    chain = get_conversational_chain()
    
    response = chain(
        {"input_documents": docs, "question": user_question},
        return_only_outputs=True
    )
    st.write("Reply: ", response["output_text"])

def main():
    st.set_page_config("MEETBOT")
    st.header("MeetBot - A Solution to ask your questions regarding a Meeting🤖")

    if 'realtime_session_id' not in st.session_state:
        st.session_state.realtime_session_id = None

    user_question = st.text_input("Ask a Question from the Transcript Files")
    if user_question:
        user_input(user_question)

    with st.sidebar:
        st.title("Menu:")
        
        st.subheader("Upload Transcripts")
        pdf_docs = st.file_uploader(
            "Upload your Transcript Files and Click on the Submit & Process Button",
            accept_multiple_files=True
        )
        
        if st.button("Submit & Process PDFs"):
            producer = TranscriptProducer()
            with st.spinner("Processing..."):
                for pdf in pdf_docs:
                    if producer.send_transcript(pdf):
                        st.success(f"Successfully sent {pdf.name} for processing")
                    else:
                        st.error(f"Failed to process {pdf.name}")
        
        # Realtime transcription section
        st.subheader("Realtime Transcription")
        realtime_text = st.text_area("Enter text chunk for realtime processing")
        
        if st.button("Process Realtime Text"):
            if realtime_text:
                producer = TranscriptProducer()
                with st.spinner("Processing realtime text..."):
                    session_id = producer.send_realtime_chunk(
                        realtime_text,
                        st.session_state.realtime_session_id
                    )
                    
                    if session_id:
                        st.session_state.realtime_session_id = session_id
                        st.success("Successfully processed realtime text chunk")
                    else:
                        st.error("Failed to process realtime text chunk")

if __name__ == "__main__":
    main()