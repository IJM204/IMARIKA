# streamlit_app.py

import streamlit as st
import os
import requests
import time
from dotenv import load_dotenv

def stream_text(text, placeholder, delay=0.03):
    """Stream text progressively with typing effect"""
    streamed_text = ""
    
    # Split by sentences for more natural pausing
    sentences = text.split('. ')
    
    for i, sentence in enumerate(sentences):
        if i > 0:
            sentence = '. ' + sentence
        
        words = sentence.split()
        for word in words:
            streamed_text += word + " "
            placeholder.markdown(streamed_text + "▌")  # Blinking cursor
            time.sleep(delay)
        
        # Longer pause at end of sentences
        if sentence.endswith('.'):
            time.sleep(delay * 3)
    
    # Remove cursor
    placeholder.markdown(streamed_text.strip())
    return streamed_text.strip()

from langchain_community.document_loaders import TextLoader, PyPDFLoader, CSVLoader, JSONLoader
from langchain_ollama import OllamaLLM
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.agents import AgentExecutor, Tool, create_react_agent
from langchain_core.prompts import ChatPromptTemplate
try:
    from langchain import hub
except ImportError:
    hub = None
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

load_dotenv()

DATA_DIR = "data"
CHROMA_DB_DIR = "./chroma_db"
OLLAMA_LLM_MODEL = "llama3"
OLLAMA_EMBEDDING_MODEL = "bge-large"  # Using available model

st.set_page_config(page_title="Offline Agentic RAG with Ollama (Multilingual & Weather)", layout="wide")

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

if not OPENWEATHER_API_KEY:
    st.warning("OPENWEATHER_API_KEY environment variable not set. Weather forecasting may not work.")


def get_current_weather(location: str) -> str:
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
            wind_data = data.get("wind", {})
            
            temp = main_data["temp"]
            feels_like = main_data["feels_like"]
            humidity = main_data["humidity"]
            pressure = main_data.get("pressure", "N/A")
            wind_speed = wind_data.get("speed", "N/A")
            description = weather_data["description"]
            city = data["name"]
            country = data["sys"]["country"]

            return (
                f"Current weather in {city}, {country}:\n"
                f"Temperature: {temp}°C (feels like {feels_like}°C)\n"
                f"Humidity: {humidity}%\n"
                f"Pressure: {pressure} hPa\n"
                f"Wind Speed: {wind_speed} m/s\n"
                f"Description: {description.capitalize()}\n"
                f"🌾 Agricultural note: Good for farming activities" if humidity > 60 and temp < 30 else "⚠️ Consider irrigation needs"
            )
        elif data.get("cod") == "404":
            return f"Could not find weather for '{location}'. Please check the city name."
        else:
            return f"Error fetching weather data for '{location}': {data.get('message', 'Unknown error from API')}"
    except requests.exceptions.Timeout:
        return f"Error: Request to OpenWeather API timed out for '{location}'."
    except requests.exceptions.RequestException as e:
        return f"Network error while fetching weather: {e}"
    except Exception as e:
        return f"Unexpected error while processing weather data: {e}"


def get_agricultural_advice(location: str) -> str:
    """Provide agricultural advice based on current weather"""
    weather_data = get_current_weather(location)
    if "Error" in weather_data:
        return weather_data
    
    # Extract temperature and humidity for advice
    lines = weather_data.split('\n')
    temp_line = next((line for line in lines if 'Temperature:' in line), '')
    humidity_line = next((line for line in lines if 'Humidity:' in line), '')
    
    advice = f"{weather_data}\n\n🌾 Agricultural Recommendations:\n"
    
    try:
        temp = float(temp_line.split('°C')[0].split(':')[1].strip())
        humidity = int(humidity_line.split('%')[0].split(':')[1].strip())
        
        if temp > 30:
            advice += "• High temperature - ensure adequate irrigation\n"
        if humidity < 40:
            advice += "• Low humidity - consider mulching to retain soil moisture\n"
        if humidity > 80:
            advice += "• High humidity - monitor for fungal diseases\n"
        if 20 <= temp <= 28 and 50 <= humidity <= 70:
            advice += "• Ideal conditions for most crops\n"
            
    except (ValueError, IndexError):
        advice += "• Check local agricultural extension for specific recommendations\n"
    
    return advice


@st.cache_resource
def load_and_process_documents(data_dir, embedding_model_name, db_dir, llm_model_name):
    documents = []
    if not os.path.exists(data_dir) or not os.listdir(data_dir):
        st.error(f"Data directory '{data_dir}' not found or is empty. Please add documents.")
        return None

    for filename in os.listdir(data_dir):
        filepath = os.path.join(data_dir, filename)
        if filename.endswith(".txt"):
            loader = TextLoader(filepath)
        elif filename.endswith(".pdf"):
            loader = PyPDFLoader(filepath)
        elif filename.endswith(".csv"):
            loader = CSVLoader(file_path=filepath)
        elif filename.endswith(".json"):
            loader = JSONLoader(file_path=filepath, jq_schema='.[].text', text_content=True)
        else:
            st.warning(f"Unsupported file type skipped: {filename}")
            continue
        documents.extend(loader.load())

    if not documents:
        st.error("No documents found.")
        return None

    # Better chunking for agricultural data
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,  # Larger chunks for better context
        chunk_overlap=150,  # More overlap for continuity
        separators=["\n\n", "\n", ".", ",", " "],  # Better separators for agricultural text
    )
    texts = text_splitter.split_documents(documents)
    
    # Add metadata for better retrieval
    for text in texts:
        if 'source' in text.metadata:
            filename = os.path.basename(text.metadata['source'])
            if filename.endswith('.csv'):
                text.metadata['type'] = 'crop_data'
            elif filename.endswith('.json'):
                text.metadata['type'] = 'structured_data'
            else:
                text.metadata['type'] = 'general'

    embeddings = OllamaEmbeddings(model=embedding_model_name)

    if not os.path.exists(db_dir) or not os.listdir(db_dir):
        vector_store = Chroma.from_documents(texts, embedding=embeddings, persist_directory=db_dir)
        st.success("New Chroma vector store created.")
    else:
        vector_store = Chroma(persist_directory=db_dir, embedding_function=embeddings)
        st.success("Loaded existing Chroma vector store.")

    return vector_store


@st.cache_resource
def setup_agent_executor(_vector_store, llm_model_name):
    llm = OllamaLLM(model=llm_model_name)
    # Enhanced retriever for better agricultural context
    retriever = _vector_store.as_retriever(
        search_kwargs={"k": 5}  # Get 5 most relevant documents
    )

    rag_prompt = ChatPromptTemplate.from_messages([
        ("system", """
        You are an agricultural expert. Answer questions using the provided context from local agricultural documents.
        
        Guidelines:
        - Prioritize information from the context over general knowledge
        - For crop questions, provide specific data from CSV files (yields, varieties, seasons)
        - Include practical farming advice when available
        - Respond in the same language as the question (English or Swahili)
        - If context is insufficient, clearly state what information is missing
        
        Context: {context}
        """),
        ("user", "{input}")
    ])

    qa_chain = create_stuff_documents_chain(llm, rag_prompt)
    rag_chain = create_retrieval_chain(retriever, qa_chain)

    def enhanced_rag_search(query):
        """Enhanced RAG search with better context"""
        # Ensure query is passed as a dictionary
        if isinstance(query, str):
            query_dict = {"input": query}
        else:
            query_dict = query
            
        result = rag_chain.invoke(query_dict)
        # Add source information to make responses more informative
        sources = [doc.metadata.get('source', 'Unknown') for doc in result.get('context', [])]
        if sources:
            result['answer'] += f"\n\n📚 Sources: {', '.join(set(sources))}"
        return result['answer']  # Return just the answer string for the tool
    
    rag_tool = Tool(
        name="KnowledgeBase",
        func=enhanced_rag_search,
        description="Search agricultural documents for crop information, farming practices, and local knowledge."
    )

    weather_tool = Tool(
        name="WeatherInfo",
        func=get_agricultural_advice,
        description="Get current weather with agricultural recommendations for farming decisions."
    )

    # Simple ReAct prompt template
    agent_prompt = ChatPromptTemplate.from_template("""
    You are an agricultural expert assistant. Use tools to answer questions about farming and weather.
    
    TOOLS:
    {tools}
    
    Use this format:
    
    Thought: Do I need to use a tool? Yes
    Action: the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: Do I need to use a tool? No
    Final Answer: [your response here]
    
    Begin!
    
    Question: {input}
    Thought:{agent_scratchpad}
    """)

    tools = [rag_tool, weather_tool]
    agent = create_react_agent(llm, tools, agent_prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)


if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("📚 Offline Agentic RAG with Ollama (English/Swahili & Weather)")
st.markdown("Ask questions based on your local documents or weather.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

with st.spinner("Initializing system..."):
    vector_store = load_and_process_documents(DATA_DIR, OLLAMA_EMBEDDING_MODEL, CHROMA_DB_DIR, OLLAMA_LLM_MODEL)
    if vector_store is None:
        st.stop()
    agent_executor = setup_agent_executor(vector_store, OLLAMA_LLM_MODEL)

prompt = st.chat_input("Ask a question or weather update (e.g., Hali ya hewa Busia?)")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Show dynamic status
        status_placeholder = st.empty()
        
        try:
            # Determine what the agent will likely do
            if any(word in prompt.lower() for word in ['weather', 'hali', 'temperature', 'rain']):
                status_placeholder.info("🌦️ Checking weather conditions...")
            else:
                status_placeholder.info("📚 Searching agricultural documents...")
            
            response = agent_executor.invoke({"input": prompt})
            final_answer = response["output"]
            
            # Clear status and show typing indicator
            status_placeholder.empty()
            st.info("✍️ Generating response...")
            
            # Progressive streaming with natural pauses
            full_response = stream_text(final_answer, message_placeholder, delay=0.04)
            st.session_state.messages.append({"role": "assistant", "content": final_answer})
            
            # Clear typing indicator
            st.empty()
                
        except Exception as e:
            error_msg = f"❌ Error: {e}"
            # Progressive error display
            for i, char in enumerate(error_msg):
                full_response += char
                message_placeholder.markdown(full_response + "▌")
                time.sleep(0.02)
            
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
