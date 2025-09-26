# rag_agent.py

import os
from langchain_community.document_loaders import TextLoader, PyPDFLoader, CSVLoader, JSONLoader
from langchain_chroma import Chroma # Updated import for Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_ollama import OllamaEmbeddings # Fixed import for OllamaEmbeddings
from langchain_ollama import OllamaLLM # New import for OllamaLLM
from langchain_core.prompts import ChatPromptTemplate


# --- Configuration ---
DATA_DIR = "data"
CHROMA_DB_DIR = "./chroma_db"
OLLAMA_LLM_MODEL = "llama3" # The LLM model pulled via Ollama (known to have some multilingual capability)
OLLAMA_EMBEDDING_MODEL = "bge-m3" # Changed to a multilingual embedding model

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
            loader = CSVLoader(file_path=filepath)
            documents.extend(loader.load())
        elif filename.endswith(".json"):
            print(f"Loading JSON file: {filename}")
            loader = JSONLoader(file_path=filepath, jq_schema='.[].text', text_content=True)
            documents.extend(loader.load())
        else:
            print(f"Skipping unsupported file type: {filename}")
    return documents

# --- 2. Split Documents into Chunks ---
def split_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)

# --- 3. Create Embeddings and Store in ChromaDB ---
def get_vector_store(texts, embedding_model_name, db_dir):
    embeddings = OllamaEmbeddings(model=embedding_model_name)

    # Ensure the directory exists with proper permissions
    if os.path.exists(db_dir):
        # Check if we can write to the directory
        if not os.access(db_dir, os.W_OK):
            print(f"Warning: No write access to {db_dir}, creating a new directory")
            # Rename the old directory and create a new one
            import shutil
            backup_dir = f"{db_dir}_backup"
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir, ignore_errors=True)
            try:
                os.rename(db_dir, backup_dir)
            except PermissionError:
                # If we can't rename, use a different directory
                db_dir = "./chroma_db_new"
                print(f"Using alternative directory: {db_dir}")
            os.makedirs(db_dir, exist_ok=True)
    else:
        os.makedirs(db_dir, exist_ok=True)

    try:
        if os.path.exists(db_dir) and os.listdir(db_dir) and os.access(db_dir, os.W_OK):
            print(f"Loading existing ChromaDB from {db_dir}")
            vector_store = Chroma(persist_directory=db_dir, embedding_function=embeddings)
        else:
            print(f"Creating new ChromaDB at {db_dir}")
            vector_store = Chroma.from_documents(
                documents=texts,
                embedding=embeddings,
                persist_directory=db_dir
            )
            print("ChromaDB created and persisted.")
        return vector_store
    except Exception as e:
        print(f"Error with ChromaDB: {e}")
        # Fallback to in-memory vector store if persistent storage fails
        print("Falling back to in-memory vector store (will not persist)")
        return Chroma.from_documents(documents=texts, embedding=embeddings)

# --- 4. Set Up the RAG Chain ---
def setup_rag_chain(vector_store, llm_model_name):
    llm = OllamaLLM(model=llm_model_name) # Changed from Ollama to OllamaLLM
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})

    # Define a prompt template for multilingual conversation
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that answers questions based on the provided context. "
                   "If the query is in Swahili, respond in Swahili. Otherwise, respond in English. "
                   "If you don't know the answer, just say that you don't know. "
                   "Context: {context}"),
        ("user", "{input}") # <<<--- FIXED THIS: Changed {query} to {input}
    ])

    # Combine retriever and LLM with the custom prompt
    from langchain.chains.combine_documents import create_stuff_documents_chain
    from langchain.chains import create_retrieval_chain

    question_answering_chain = create_stuff_documents_chain(llm, prompt_template)
    rag_chain = create_retrieval_chain(retriever, question_answering_chain)

    return rag_chain

# --- Main function to run the RAG system ---
if __name__ == "__main__":
    print("--- Initializing Offline RAG System ---")

    if not os.path.exists(DATA_DIR):
        print(f"Error: Data directory '{DATA_DIR}' not found. Please create it and add your documents.")
        exit()

    try:
        # Check if we can access the directory
        db_accessible = os.path.exists(CHROMA_DB_DIR) and os.access(CHROMA_DB_DIR, os.R_OK | os.W_OK)
        
        if db_accessible and os.listdir(CHROMA_DB_DIR):
            current_db_embeddings = OllamaEmbeddings(model=OLLAMA_EMBEDDING_MODEL)
            should_rebuild = OLLAMA_EMBEDDING_MODEL != current_db_embeddings.model
        else:
            should_rebuild = True
    except Exception as e:
        print(f"Exception when checking database: {e}")
        should_rebuild = True

    if should_rebuild:
        print(f"Processing documents for the first time or rebuilding due to embedding model change ({OLLAMA_EMBEDDING_MODEL}) or DB not found/corrupted...")
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
            response = rag_chain.invoke({"input": query})
            print(f"AI: {response['answer']}")
            if response.get('context'):
                print("\nSources:")
                for i, doc in enumerate(response['context']):
                    print(f"- Source {i+1}: {doc.metadata.get('source', 'Unknown source')}")
                print("-" * 30)
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Please ensure Ollama is running (`ollama serve`) and the models are pulled.")
