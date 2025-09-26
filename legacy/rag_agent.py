# rag_agent.py

import os
import requests # New import for making HTTP requests
from dotenv import load_dotenv # New import for loading environment variables

from langchain_community.document_loaders import TextLoader, PyPDFLoader, CSVLoader, JSONLoader
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

# For agent creation
from langchain.agents import AgentExecutor, Tool, create_react_agent # New imports for agent

# Load environment variables from .env file (for local development)
load_dotenv()

# --- Configuration ---
DATA_DIR = "data"
CHROMA_DB_DIR = "./chroma_db"
OLLAMA_LLM_MODEL = "llama3" # The LLM model pulled via Ollama (known to have some multilingual capability)
OLLAMA_EMBEDDING_MODEL = "bge-m3" # Multilingual embedding model

# --- OpenWeather API Key (loaded from environment variable) ---
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not OPENWEATHER_API_KEY:
    print("Warning: OPENWEATHER_API_KEY environment variable not set. Weather forecasting will not work.")

# --- Weather Forecasting Tool Function ---
def get_weather_forecast(location: str) -> str:
    """Fetches the current weather forecast for a given city. Input should be a city name (e.g., "Nairobi")."""
    if not OPENWEATHER_API_KEY:
        return "Error: OpenWeather API key is not configured."

    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    # Use units=metric for Celsius, adjust as needed
    complete_url = f"{base_url}q={location}&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(complete_url, timeout=10) # Added timeout for robustness
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        if data.get("cod") == 200: # Check for successful response code
            main_data = data["main"]
            weather_data = data["weather"][0]
            temp = main_data["temp"]
            feels_like = main_data["feels_like"]
            humidity = main_data["humidity"]
            description = weather_data["description"]
            city = data["name"]
            country = data["sys"]["country"]

            forecast = (
                f"Current weather in {city}, {country}:\n"
                f"Temperature: {temp}°C (feels like {feels_like}°C)\n"
                f"Humidity: {humidity}%\n"
                f"Description: {description.capitalize()}."
            )
            return forecast
        elif data.get("cod") == "404":
            return f"Could not find weather for '{location}'. Please check the city name."
        else:
            return f"Error fetching weather data for '{location}': {data.get('message', 'Unknown error from API')}"
    except requests.exceptions.Timeout:
        return f"Error: Request to OpenWeather API timed out for '{location}'."
    except requests.exceptions.RequestException as e:
        return f"Error fetching weather data: A network error occurred while connecting to OpenWeather API: {e}"
    except Exception as e:
        return f"An unexpected error occurred while processing weather data: {e}"

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
        print("ChromaDB created and persisted.")
    return vector_store

# --- 4. Set Up the RAG and Agent Chains ---
def setup_agent_executor(vector_store, llm_model_name):
    llm = OllamaLLM(model=llm_model_name)
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})

    # --- 4.1. Define the RAG Chain as a Tool ---
    rag_prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that answers questions based on the provided context. "
                   "If the query is in Swahili, respond in Swahili. Otherwise, respond in English. "
                   "If you don't know the answer, just say that you don't know. "
                   "Context: {context}"),
        ("user", "{input}")
    ])
    question_answering_chain = create_stuff_documents_chain(llm, rag_prompt_template)
    rag_chain = create_retrieval_chain(retriever, question_answering_chain)

    rag_tool = Tool(
        name="KnowledgeBase",
        func=rag_chain.invoke, # LangChain's invoke method makes it callable
        description="Useful for answering questions about the documents in your knowledge base. "
                    "Input should be a question string (e.g., 'What is cassava farming?').",
        coroutine=None, # Not an async function
    )

    # --- 4.2. Define the Weather Tool ---
    weather_tool = Tool(
        name="WeatherForecast",
        func=get_weather_forecast,
        description="Useful for getting the current weather forecast for a specified city. "
                    "Input should be a single string: the city name (e.g., 'Nairobi', 'London', 'Tokyo').",
        coroutine=None, # Not an async function
    )

    tools = [rag_tool, weather_tool]

    # --- 4.3. Set up the Agent ---
    # We use create_react_agent which is a good general-purpose agent.
    # The prompt guides the LLM to choose the right tool.
    # Ensure this prompt is designed for multilingual interaction for tool selection
    agent_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that can answer questions based on a knowledge base "
                   "or by fetching weather information. Respond in Swahili if the query is in Swahili; "
                   "otherwise, respond in English. Always prioritize using the most relevant tool to answer the user's request. "
                   "If the user asks for weather, use the WeatherForecast tool. For other information, use the KnowledgeBase tool. "
                   "You have access to the following tools: {tools}\n"
                   "You can use `tool_code` to execute a tool. "
                   "Use the following format:\n\n"
                   "Thought: you should always think about what to do\n"
                   "Action: the action to take, should be one of [{tool_names}]\n"
                   "Action Input: the input to the action\n"
                   "Observation: the result of the action\n"
                   "... (this Thought/Action/Action Input/Observation can repeat N times)\n"
                   "Thought: I now know the final answer\n"
                   "Final Answer: the final answer to the original input question"),
        ("placeholder", "{chat_history}"), # For future conversational memory
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"), # Where the agent keeps track of its thoughts and tool outputs
    ])

    agent = create_react_agent(llm, tools, agent_prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

    return agent_executor

# --- Main function to run the RAG system ---
if __name__ == "__main__":
    print("--- Initializing Offline Agentic RAG System ---")

    if not os.path.exists(DATA_DIR):
        print(f"Error: Data directory '{DATA_DIR}' not found. Please create it and add your documents.")
        exit()

    # Determine if ChromaDB needs to be rebuilt
    should_rebuild = False
    if not os.path.exists(CHROMA_DB_DIR) or not os.listdir(CHROMA_DB_DIR):
        should_rebuild = True
    else:
        try:
            # Simple heuristic: if embedding model changed, force rebuild.
            # Otherwise, assume existing DB is fine.
            # For robustness, consider storing model name in DB metadata.
            current_db_embeddings_model = OllamaEmbeddings(model=OLLAMA_EMBEDDING_MODEL).model
            # This check is a simplification. For production, compare against stored model name.
            # If you change OLLAMA_EMBEDDING_MODEL, manually delete chroma_db.
            st.info = print # Use print for info messages in CLI
            st.success = print
            embeddings_check = OllamaEmbeddings(model=OLLAMA_EMBEDDING_MODEL)
            test_db = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings_check)
            print("Existing ChromaDB found and potentially compatible.")
            # We don't have a direct way to check the *exact* model name used to create it,
            # so rely on manual deletion for embedding model changes.
        except Exception as e:
            print(f"Error loading existing ChromaDB: {e}. Forcing rebuild.")
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

    # Pass the vector_db to setup_agent_executor
    agent_executor = setup_agent_executor(vector_db, OLLAMA_LLM_MODEL)

    print("\n--- Agentic RAG System Ready! Type 'exit' to quit. ---")
    while True:
        query = input("You: ")
        if query.lower() == 'exit':
            print("Exiting RAG system.")
            break
        print("Thinking...")
        try:
            # The agent executor's invoke method expects 'input'
            response = agent_executor.invoke({"input": query})
            print(f"AI: {response['output']}") # Agent output is typically 'output' key
            print("-" * 30)
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Please ensure Ollama is running (`ollama serve`) and the models are pulled.")
            print("Also, check your OPENWEATHER_API_KEY environment variable.")

