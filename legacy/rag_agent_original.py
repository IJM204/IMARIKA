# rag_agent.py

import os
from langchain_community.document_loaders import TextLoader, PyPDFLoader, CSVLoader, JSONLoader
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA

# --- Configuration ---
DATA_DIR = "data" # Directory where your knowledge base documents are stored
CHROMA_DB_DIR = "./chroma_db" # Directory to store ChromaDB persistent data
OLLAMA_LLM_MODEL = "llama3" # The LLM model pulled via Ollama
OLLAMA_EMBEDDING_MODEL = "nomic-embed-text" # The embedding model pulled via Ollama

# --- 1. Load Documents ---
def load_documents(data_dir):
    documents = []
    for filename in os.listdir(data_dir):
        filepath = os.path.join(data_dir, filename)
        if filename.endswith(".txt"):
            print(f"Loading text file: {filename}")
            loader = TextLoader(filepath)
            documents.extend(loader.load())
        elif filename.endswith(".pdf"):
            print(f"Loading PDF file: {filename}")
            loader = PyPDFLoader(filepath)
            documents.extend(loader.load())
        elif filename.endswith(".csv"):
            print(f"Loading CSV file: {filename}")
            # CSVLoader can take a source_column if you want one column as metadata
            # loader = CSVLoader(file_path=filepath, csv_args={"delimiter": ","}, source_column="your_id_column")
            loader = CSVLoader(file_path=filepath)
            documents.extend(loader.load())
        elif filename.endswith(".json"):
            print(f"Loading JSON file: {filename}")
            # --- IMPORTANT: You NEED to adjust the jq_schema based on your JSON structure ---
            # Example 1: If your JSON is a list of objects, and each object is a document
            # E.g., [{"id":1, "text":"doc1"}, {"id":2, "text":"doc2"}]
            loader = JSONLoader(file_path=filepath, jq_schema='.[].text', text_content=True)

            # Example 2: If your JSON has a key "items" which is a list of documents
            # E.g., {"items": [{"content": "abc"}, {"content": "xyz"}]}
            # loader = JSONLoader(file_path=filepath, jq_schema='.items[]', text_content=False) # Or .items[].content if you want only the string

            # For a simple JSON file that's a single object you want as one document:
            # loader = JSONLoader(file_path=filepath, jq_schema='.', text_content=False) # Loads the whole JSON object
            documents.extend(loader.load())
        else:
            print(f"Skipping unsupported file type: {filename}")
    return documents


# --- 2. Split Documents into Chunks ---
def split_documents(documents):
    # Using RecursiveCharacterTextSplitter for robust splitting
    # It attempts to split on different separators to keep chunks semantically coherent
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,      # Max characters in a chunk
        chunk_overlap=200,    # Overlap between chunks to maintain context
        length_function=len,  # Function to calculate chunk length
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)

# --- 3. Create Embeddings and Store in ChromaDB ---
def get_vector_store(texts, embedding_model_name, db_dir):
    # Initialize Ollama for embeddings
    # Ensure Ollama server is running and the embedding model is pulled
    embeddings = OllamaEmbeddings(model=embedding_model_name)

    # Create a new Chroma vector store from documents or load existing one
    # Use persist_directory to save the database to disk
    # If the directory exists and contains data, it will load it
    # Otherwise, it will create a new one
    if os.path.exists(db_dir) and os.listdir(db_dir):
        print(f"Loading existing ChromaDB from {db_dir}")
        vector_store = Chroma(persist_directory=db_dir, embedding_function=embeddings)
    else:
        print(f"Creating new ChromaDB at {db_dir}")
        vector_store = Chroma.from_documents(
            documents=texts,
            embedding=embeddings,
            persist_directory=db_dir
        )
        # vector_store.persist() # Saved automatically
        print("ChromaDB created and persisted.")
    return vector_store

# --- 4. Set Up the RAG Chain ---
def setup_rag_chain(vector_store, llm_model_name):
    # Initialize Ollama LLM
    # Ensure Ollama server is running and the LLM model is pulled
    llm = OllamaLLM(model=llm_model_name)

    # Create a retriever from the vector store
    # 'as_retriever()' allows the LLM to query the vector store for relevant documents
    retriever = vector_store.as_retriever(search_kwargs={"k": 3}) # Retrieve top 3 relevant documents

    # Create the RetrievalQA chain
    # This chain takes a question, retrieves relevant docs, and passes both to the LLM
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff", # 'stuff' means all retrieved docs are "stuffed" into the prompt
        retriever=retriever,
        return_source_documents=True # Optionally return the documents that were used
    )
    return qa_chain

# --- Main function to run the RAG system ---
if __name__ == "__main__":
    print("--- Initializing Offline RAG System ---")

    # Ensure data directory exists
    if not os.path.exists(DATA_DIR):
        print(f"Error: Data directory '{DATA_DIR}' not found. Please create it and add your documents.")
        exit()

    # Load and process documents only if ChromaDB is not initialized or empty
    if not os.path.exists(CHROMA_DB_DIR) or not os.listdir(CHROMA_DB_DIR):
        print("Processing documents for the first time...")
        documents = load_documents(DATA_DIR)
        if not documents:
            print(f"No documents found in '{DATA_DIR}'. Please add some files to populate the knowledge base.")
            exit()
        texts = split_documents(documents)
        vector_db = get_vector_store(texts, OLLAMA_EMBEDDING_MODEL, CHROMA_DB_DIR)
    else:
        print(f"Loading existing vector store from {CHROMA_DB_DIR}...")
        embeddings = OllamaEmbeddings(model=OLLAMA_EMBEDDING_MODEL)
        vector_db = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
        print("Vector store loaded.")


    rag_chain = setup_rag_chain(vector_db, OLLAMA_LLM_MODEL)

    print("\n--- RAG System Ready! Type 'exit' to quit. ---")
    while True:
        query = input("You: ")
        if query.lower() == 'exit':
            print("Exiting RAG system.")
            break
        print("Thinking...")
        try:
            response = rag_chain.invoke({"query": query})
            print(f"AI: {response['result']}")
            if response.get('source_documents'):
                print("\nSources:")
                for i, doc in enumerate(response['source_documents']):
                    print(f"- Source {i+1}: {doc.metadata.get('source', 'Unknown source')}")
                    # print(f"  Content snippet: {doc.page_content[:200]}...") # Uncomment to see snippet
            print("-" * 30)
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Please ensure Ollama is running (`ollama serve`) and the models are pulled.")

