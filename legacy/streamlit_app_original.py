# streamlit_app.py

import streamlit as st
import os
from langchain_community.document_loaders import TextLoader, PyPDFLoader, CSVLoader, JSONLoader
# Corrected imports for OllamaEmbeddings and OllamaLLM
from langchain_community.llms import Ollama as OllamaLLM # Renamed to avoid confusion, but works as before
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter # Corrected: 'Character' appears once
from langchain.chains import RetrievalQA
from langchain_ollama import OllamaEmbeddings # Updated import path for OllamaEmbeddings

# --- Configuration ---
DATA_DIR = "data"
CHROMA_DB_DIR = "./chroma_db"
OLLAMA_LLM_MODEL = "llama3" # The LLM model pulled via Ollama
OLLAMA_EMBEDDING_MODEL = "nomic-embed-text" # The embedding model pulled via Ollama

# --- Functions ---

# Added llm_model_name as a parameter to the function definition
@st.cache_resource
def load_and_process_documents(data_dir, embedding_model_name, db_dir, llm_model_name):
    """
    Loads documents from various formats, splits them, and initializes/loads the ChromaDB vector store.
    Uses st.cache_resource to avoid re-processing on every Streamlit rerun.
    """
    documents = []
    if not os.path.exists(data_dir) or not os.listdir(data_dir):
        st.error(f"Data directory '{data_dir}' not found or is empty. Please create it and add your documents.")
        return None, None

    for filename in os.listdir(data_dir):
        filepath = os.path.join(data_dir, filename)
        if filename.endswith(".txt"):
            st.info(f"Loading text file: {filename}")
            loader = TextLoader(filepath)
            documents.extend(loader.load())
        elif filename.endswith(".pdf"):
            st.info(f"Loading PDF file: {filename}")
            loader = PyPDFLoader(filepath)
            documents.extend(loader.load())
        elif filename.endswith(".csv"):
            st.info(f"Loading CSV file: {filename}")
            # CSVLoader can take csv_args for delimiter or source_column for metadata
            loader = CSVLoader(file_path=filepath)
            documents.extend(loader.load())
        elif filename.endswith(".json"):
            st.info(f"Loading JSON file: {filename}")
            # For JSON structure: [{"id": 1, "text": "..."}]
            # We extract the 'text' field from each object in the root array.
            loader = JSONLoader(
                file_path=filepath,
                jq_schema='.[].text', # Extracts the 'text' value from each object in the root array
                text_content=True # Indicates that the extracted content is the text itself
            )
            documents.extend(loader.load())
        else:
            st.warning(f"Skipping unsupported file type: {filename}")

    if not documents:
        st.error(f"No usable documents found in '{data_dir}'. Please check file types.")
        return None, None

    # Using RecursiveCharacterTextSplitter for robust splitting
    text_splitter = RecursiveCharacterTextSplitter( # Corrected class name here
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    texts = text_splitter.split_documents(documents)

    embeddings = OllamaEmbeddings(model=embedding_model_name)

    # Check if ChromaDB exists and has data, or create a new one
    if os.path.exists(db_dir) and os.listdir(db_dir):
        st.info(f"Loading existing ChromaDB from {db_dir}")
        vector_store = Chroma(persist_directory=db_dir, embedding_function=embeddings)
    else:
        st.info(f"Creating new ChromaDB at {db_dir}. This may take a while...")
        vector_store = Chroma.from_documents(
            documents=texts,
            embedding=embeddings,
            persist_directory=db_dir
        )
        # Removed vector_store.persist() as it's often handled implicitly now
        st.success("ChromaDB created and persisted.")

    # Now llm_model_name is available here because it's passed as a parameter
    llm = OllamaLLM(model=llm_model_name)
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )
    return qa_chain, vector_store # Return vector_store for potential display/debugging

# --- Streamlit UI ---
st.set_page_config(page_title="Offline Agentic RAG with Ollama", layout="wide")

st.title("📚 Offline Agentic RAG with Ollama (Streamlit UI)")
st.markdown("Ask questions based on your local documents (TXT, PDF, CSV, JSON supported)!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Load and process documents, and set up the RAG chain (cached for performance)
with st.spinner("Initializing RAG system (loading models and vector store)..."):
    try:
        # Passed OLLAMA_LLM_MODEL as the fourth argument
        rag_chain, vector_db = load_and_process_documents(DATA_DIR, OLLAMA_EMBEDDING_MODEL, CHROMA_DB_DIR, OLLAMA_LLM_MODEL)
        if rag_chain is None:
            st.stop() # Stop if document loading failed
        st.success("RAG system initialized!")
    except Exception as e:
        st.error(f"Failed to initialize RAG system. Please ensure Ollama is running (`ollama serve`) and models (`{OLLAMA_LLM_MODEL}`, `{OLLAMA_EMBEDDING_MODEL}`) are pulled.")
        st.exception(e) # Display full exception traceback for debugging
        st.stop()


# Accept user input
if prompt := st.chat_input("What do you want to know?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        with st.spinner("Thinking..."):
            try:
                response = rag_chain.invoke({"query": prompt})
                result = response['result']
                sources = response.get('source_documents', [])

                full_response += result
                if sources:
                    full_response += "\n\n**Sources:**\n"
                    for i, doc in enumerate(sources):
                        source_name = doc.metadata.get('source', 'Unknown source')
                        # For PDF pages, try to get page number
                        if 'page' in doc.metadata:
                            source_name += f" (Page {doc.metadata['page'] + 1})" # Page numbers are 0-indexed
                        # For CSV, it often includes line numbers
                        if 'row' in doc.metadata:
                            source_name += f" (Row {doc.metadata['row'] + 1})" # Row numbers are 0-indexed
                        full_response += f"- {source_name}\n"
                        # full_response += f"  > {doc.page_content[:200]}...\n" # Uncomment to see snippet

                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                st.error(f"An error occurred during RAG processing: {e}")
                st.warning("Please ensure Ollama is running (`ollama serve`) and the models are pulled.")
                message_placeholder.markdown(f"Error: {e}")
                st.session_state.messages.append({"role": "assistant", "content": f"Error: {e}"})
