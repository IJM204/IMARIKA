# streamlit_app.py

import streamlit as st
import os
import requests
from dotenv import load_dotenv

from langchain_community.document_loaders import TextLoader, PyPDFLoader, CSVLoader, JSONLoader
from langchain_ollama import OllamaLLM
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.agents import AgentExecutor, Tool, create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain


# Load environment variables from .env file (for local development)
load_dotenv()

# --- Configuration ---
DATA_DIR = "data"
CHROMA_DB_DIR = "./chroma_db"
OLLAMA_LLM_MODEL = "llama3"
OLLAMA_EMBEDDING_MODEL = "bge-m3"

# --- Set Streamlit Page Config (MUST BE THE FIRST STREAMLIT COMMAND) ---
st.set_page_config(page_title="Offline Agentic RAG with Ollama (Multilingual & Weather)", layout="wide")

# --- OpenWeather API Key (loaded from environment variable) ---
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# --- DEBUG PRINT: Check if API key is loaded ---
print(f"Debug: OPENWEATHER_API_KEY loaded: {OPENWEATHER_API_KEY is not None}")
if OPENWEATHER_API_KEY:
    print(f"Debug: OPENWEATHER_API_KEY value: {OPENWEATHER_API_KEY[:5]}...{OPENWEATHER_API_KEY[-5:]}") # Print partial key for security

if not OPENWEATHER_API_KEY:
    st.warning("OPENWEATHER_API_KEY environment variable not set. Weather forecasting may not work.")


# --- Weather Forecasting Tool Function ---
def get_weather_forecast(location: str) -> str:
    """Fetches the current weather forecast for a given city. Input should be a city name (e.g., "Nairobi")."""
    if not OPENWEATHER_API_KEY:
        return "Error: OpenWeather API key is not configured."

    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = f"{base_url}q={location}&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(complete_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("cod") == 200:
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

# --- Document Loading and Processing (Same as before) ---
@st.cache_resource
def load_and_process_documents(data_dir, embedding_model_name, db_dir, llm_model_name):
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
            loader = CSVLoader(file_path=filepath)
            documents.extend(loader.load())
        elif filename.endswith(".json"):
            st.info(f"Loading JSON file: {filename}")
            loader = JSONLoader(file_path=filepath, jq_schema='.[].text', text_content=True)
            documents.extend(loader.load())
        else:
            st.warning(f"Skipping unsupported file type: {filename}")

    if not documents:
        st.error(f"No usable documents found in '{data_dir}'. Please check file types.")
        return None, None

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, # Using the smaller chunk size for better memory management
        chunk_overlap=100,
        length_function=len,
        is_separator_regex=False,
    )
    texts = text_splitter.split_documents(documents)

    embeddings = OllamaEmbeddings(model=embedding_model_name)

    should_rebuild = False
    if not os.path.exists(db_dir) or not os.listdir(db_dir):
        should_rebuild = True
    else:
        try:
            test_vector_store = Chroma(persist_directory=db_dir, embedding_function=embeddings)
            st.info(f"Loading existing ChromaDB from {db_dir}...")
            vector_store = test_vector_store
        except Exception:
            st.warning(f"Error loading existing ChromaDB. Forcing rebuild at {db_dir}.")
            should_rebuild = True

    if should_rebuild:
        st.info(f"Creating new ChromaDB at {db_dir} (new/updated data or embedding model change to {embedding_model_name}). This may take a while...")
        vector_store = Chroma.from_documents(
            documents=texts,
            embedding=embeddings,
            persist_directory=db_dir
        )
        st.success("ChromaDB created and persisted.")
    else:
        st.success("Vector store loaded.")

    return vector_store # Only return vector_store, agent is created separately

# --- 4. Set Up the RAG and Agent Chains ---
@st.cache_resource # Cache the agent executor too
def setup_agent_executor(_vector_store, llm_model_name): # Renamed to _vector_store
    llm = OllamaLLM(model=llm_model_name)
    retriever = _vector_store.as_retriever(search_kwargs={"k": 3}) # Use _vector_store here

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
        func=rag_chain.invoke,
        description="Useful for answering questions about the documents in your knowledge base. "
                    "Input should be a question string (e.g., 'What is cassava farming?').",
        coroutine=None,
    )

    # --- 4.2. Define the Weather Tool ---
    weather_tool = Tool(
        name="WeatherForecast",
        func=get_weather_forecast,
        description="Useful for getting the current weather forecast for a specified city. "
                    "Input should be a single string: the city name (e.g., 'Nairobi', 'London', 'Tokyo').",
        coroutine=None,
    )

    tools = [rag_tool, weather_tool]

    # --- 4.3. Set up the Agent ---
    agent_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that can answer questions based on a knowledge base "
                   "or by fetching weather information. Respond in Swahili if the query is in Swahili; "
                   "otherwise, respond in English. Always prioritize using the most relevant tool to answer the user's request. "
                   "If the user asks for weather, use the WeatherForecast tool. For other information, use the KnowledgeBase tool. "
                   "You have access to the following tools: {tools}\n"
                   "To use a tool, you must follow this exact format:\n\n"
                   "Thought: I should think about what to do.\n"
                   "Action: tool_name\n"
                   "Action Input: input for the tool\n"
                   "Observation: tool_output\n"
                   "... (this Thought/Action/Action Input/Observation can repeat N times)\n"
                   "Thought: I now know the final answer\n"
                   "Final Answer: the final answer to the original input question\n\n"
                   "Here's an example of how to use the WeatherForecast tool:\n"
                   "User: What's the weather in Busia?\n"
                   "Thought: The user is asking about the weather. I should use the WeatherForecast tool to get the current weather for 'Busia'.\n"
                   "Action: WeatherForecast\n"
                   "Action Input: Busia\n"
                   "Observation: Current weather in Busia, KE:\nTemperature: 25.0°C (feels like 26.0°C)\nHumidity: 70%\nDescription: Light rain.\n"
                   "Thought: I have the weather information. I can now provide the final answer.\n"
                   "Final Answer: The current weather in Busia, Kenya is 25.0°C (feels like 26.0°C) with light rain and 70% humidity.\n\n"
                   ),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
        ("placeholder", "{tool_names}"),
    ])

    agent = create_react_agent(llm, tools, agent_prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

    return agent_executor


# --- Streamlit UI ---
# Initialize chat history (Moved this higher up)
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("📚 Offline Agentic RAG with Ollama (English/Swahili & Weather)")
st.markdown("Ask questions based on your local documents or get current weather forecasts!")

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Load and process documents, then setup the agent (cached for performance)
with st.spinner("Initializing Agentic RAG system (loading models and vector store)..."):
    try:
        vector_db = load_and_process_documents(DATA_DIR, OLLAMA_EMBEDDING_MODEL, CHROMA_DB_DIR, OLLAMA_LLM_MODEL)
        if vector_db is None:
            st.stop()

        agent_executor = setup_agent_executor(vector_db, OLLAMA_LLM_MODEL)

        st.success("Agentic RAG system initialized!")
    except Exception as e:
        st.error(f"Failed to initialize Agentic RAG system. Please ensure Ollama is running (`ollama serve`) and models (`{OLLAMA_LLM_MODEL}`, `{OLLAMA_EMBEDDING_MODEL}`) are pulled.")
        st.exception(e)
        st.stop()


# Accept user input
if prompt := st.chat_input("What do you want to know? (Unauliza nini? Au, hali ya hewa iko vipi [mji]?):"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        with st.spinner("Thinking..."):
            try:
                response = agent_executor.invoke({"input": prompt})
                full_response = response['output']

                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                st.error(f"An error occurred during agent processing: {e}")
                st.warning("Please ensure Ollama is running (`ollama serve`) and the models are pulled.")
                st.warning("Also, check your OPENWEATHER_API_KEY environment variable and network connection.")
                message_placeholder.markdown(f"Error: {e}")
                st.session_state.messages.append({"role": "assistant", "content": f"Error: {e}"})
