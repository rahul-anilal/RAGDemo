import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
import random
import time
import subprocess

from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai

from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain

from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key = os.getenv("GOOGLE_API_KEY"))

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text+=page.extract_text()
    print(text)
    return text

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks):
    embeddings   = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embedding = embeddings)

def get_conversational_chain():
    prompt_template = """
    You are a helpful AI assistant, that helps the developer by generating regression test cases from natural language input. 
    Analyze the user input thoroughly, which consists of the details of the app's functionality as well as the request and response structures and/or API contracts. 
    Generate positive, negative, and edge test cases in accordance with the request structure, and their expected output according to the response structure. \n\n

    Context:\n {context}?\n
    Question: \n{question}\n

    Detailed Answer:
    """

    model  = ChatGoogleGenerativeAI(model = "gemini-2.0-flash", temperature = 0.6)
    prompt = PromptTemplate(template = prompt_template, input_variables = ["context", "question"])
    chain  = load_qa_chain(model, chain_type = "stuff", prompt = prompt)
    return chain

def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")

    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    docs   = new_db.similarity_search(user_question)

    chain  = get_conversational_chain()

    response = chain(
        {"input_documents":docs, "question": user_question}
        , return_only_outputs=True
    )
    
    print(response)
    st.write("Reply: ", response["output_text"])

def get_ques(question):
    embeddings   = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")

    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    docs   = new_db.similarity_search(question)

    chain  = get_conversational_chain()

    response = chain(
        {"input_documents":docs, "question": question}
        , return_only_outputs=True)
    
    #response = "1.What is discussed about gemini pro?\n2.What is the problem statement?\n3.What are the societal impacts?\n4.what is the general workflow\n5.What are the possible problems that were discussed?\n6.What are the possible advantages?"
    print(response)
    return response

@st.cache_data
def get_sidebar_text(): #does not require a prompt, AT runs.

    response = get_ques("Give a summary of the app's functionality. Do not include any conversational information such as 'Ok, here is the description of the functionality'. Make it clear and concise.")
    return response["output_text"]
    #return response

def gpt_pop_up():
    subprocess.Popen(["streamlit", "run", "query.py"])

def remove_non_empty_dir(directory): #to flush faiss_index before every run
    if os.path.exists(directory) and os.path.isdir(directory): 
        for root, dirs, files in os.walk(directory, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(directory)

def main():
    #remove_non_empty_dir('faiss_index') #flushing faiss_index

    st.set_page_config("RAGDemo")
    st.header("Generating test cases from natural language input")

    user_question = st.text_input("Please provide the functionality of the application to be tested, along with the request and response structure and/or API Contracts.")

    if user_question:
        user_input(user_question)

    with st.sidebar:
        st.title("Menu:")
        pdf_docs = st.file_uploader("Upload your Documentation and Click on the Submit & Process Button", accept_multiple_files=True)
        if st.button("Submit & Process"):
            with st.spinner("Processing..."):
                raw_text    = get_pdf_text(pdf_docs)
                text_chunks = get_text_chunks(raw_text)
                get_vector_store(text_chunks)
                sidebar_text = get_sidebar_text()
                st.sidebar.text(sidebar_text)
        #sidebar_text = get_sidebar_text()
        #st.sidebar.text(sidebar_text)
        if st.button("Ask your questions here"):
            gpt_pop_up()
if __name__ == "__main__":
    main()