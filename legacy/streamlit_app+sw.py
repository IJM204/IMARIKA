# streamlit_app.py

import streamlit as st
import os
import requests
import time
from dotenv import load_dotenv

def stream_text(text, placeholder, delay=0.01):
    """Stream text progressively with typing effect"""
    streamed_text = ""
    words = text.split()
    
    for word in words:
        streamed_text += word + " "
        placeholder.markdown(streamed_text + "▌")
        time.sleep(delay)
    
    placeholder.markdown(streamed_text.strip())
    return streamed_text.strip()

from langchain_community.document_loaders import TextLoader, PyPDFLoader, CSVLoader, JSONLoader
# Corrected imports for OllamaLLM and OllamaEmbeddings
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

# Disable ChromaDB telemetry to avoid dependency issues
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# Disable Streamlit file watching to handle inotify limit
os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"

# --- Configuration ---
DATA_DIR = "data"
CHROMA_DB_DIR = "./chroma_db"
OLLAMA_LLM_MODEL = "llama3" # The LLM model pulled via Ollama (known to have some multilingual capability)
OLLAMA_EMBEDDING_MODEL = "mxbai-embed-large"  # Use available model from your list

# --- Set Streamlit Page Config (MUST BE THE FIRST STREAMLIT COMMAND) ---
st.set_page_config(page_title="Imarika - Agricultural Assistant", layout="wide")

# --- OpenWeather API Key (loaded from environment variable) ---
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# --- DEBUG PRINT: Check if API key is loaded ---
print(f"Debug: OPENWEATHER_API_KEY loaded: {OPENWEATHER_API_KEY is not None}")
if OPENWEATHER_API_KEY:
    print(f"Debug: OPENWEATHER_API_KEY value: {OPENWEATHER_API_KEY[:5]}...{OPENWEATHER_API_KEY[-5:]}") # Print partial key for security

if not OPENWEATHER_API_KEY:
    st.warning("OPENWEATHER_API_KEY environment variable not set. Weather forecasting may not work.")


# --- Weather & Data Functions ---
def get_weather_data(location: str) -> dict:
    """Get weather data from OpenWeather API."""
    if not OPENWEATHER_API_KEY:
        return {"error": "Weather API key not configured."}

    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = f"{base_url}q={location}&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(complete_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("cod") == 200:
            return {
                "success": True,
                "city": data["name"],
                "country": data["sys"]["country"],
                "temperature": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "description": data["weather"][0]["description"],
            }
        else:
            return {"error": f"Location '{location}' not found."}
    except Exception as e:
        return {"error": f"Weather API error: {e}"}

def format_weather_response(weather_data: dict) -> str:
    """Format weather data with agricultural advice."""
    if "error" in weather_data:
        return f"❌ **Weather Error:** {weather_data['error']}"

    temp = weather_data['temperature']
    humidity = weather_data['humidity']

    weather_text = f"🌤️ **Current Weather in {weather_data['city']}**\n"
    weather_text += f"   - 🌡️ Temp: {temp}°C, 💧 Humidity: {humidity}%, ☁️ {weather_data['description'].capitalize()}\n"

    advice_given = False
    if temp > 30:
        weather_text += "   - ⚠️ **High Temp:** Ensure adequate irrigation.\n"
        advice_given = True
    if humidity > 80:
        weather_text += "   - 🍄 **High Humidity:** Monitor for fungal diseases.\n"
        advice_given = True

    if not advice_given:
        weather_text += "   - ✅ Conditions seem moderate for farming.\n"

    return weather_text

def get_value_chains_from_data() -> list:
    """Extract value chains from data folder filenames."""
    expected_crops = {
        'beans.csv': 'Beans', 'cassava.csv': 'Cassava', 'finger_millet.csv': 'Finger Millet',
        'maize.csv': 'Maize', 'sorghum.csv': 'Sorghum', 'sweet_potatoes.csv': 'Sweet Potatoes'
    }
    available_chains = [expected_crops[f] for f in os.listdir(DATA_DIR) if f in expected_crops]
    return available_chains if available_chains else list(expected_crops.values())

@st.cache_resource
def load_and_process_documents(data_dir, embedding_model_name, db_dir, llm_model_name):
    """Load docs, process them, and create a RAG chain."""
    documents = []
    if not os.path.exists(data_dir) or not os.listdir(data_dir):
        st.error(f"Data directory '{data_dir}' not found or is empty. Please create it and add your documents.")
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
            continue
        try:
            documents.extend(loader.load())
        except Exception as e:
            st.warning(f"Could not load {filename}: {e}")

    if not documents:
        st.error(f"No usable documents found in '{data_dir}'. Please check file types.")
        return None

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,  # Smaller chunks for faster processing
        chunk_overlap=50,
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
            vector_store = Chroma(persist_directory=db_dir, embedding_function=embeddings)
        except Exception:
            st.warning("Could not load existing database. Rebuilding...")
            should_rebuild = True

    if should_rebuild:
        st.info("Creating new vector database...")
        try:
            vector_store = Chroma.from_documents(
                documents=texts,
                embedding=embeddings,
                persist_directory=db_dir
            )
        except Exception as e:
            st.error(f"Failed to create vector database: {e}")
            return None

    llm = OllamaLLM(model=llm_model_name)
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})  # Reduced for faster response

    # Simplified prompt for faster processing
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are Imarika. Answer using ONLY the provided context. If no relevant info, say you don't have that data. Context: {context}"),
        ("user", "{input}")
    ])

    question_answering_chain = create_stuff_documents_chain(llm, prompt_template)
    rag_chain = create_retrieval_chain(retriever, question_answering_chain)

    return rag_chain

def generate_assistant_response(prompt: str, rag_chain, user_location: str, selected_value_chains: list) -> str:
    """
    Generates the complete, formatted response from the assistant.
    """
    current_weather = get_weather_data(user_location)
    weather_info = format_weather_response(current_weather)

    # Simplified prompt for faster processing
    enhanced_prompt = f"""Weather: {weather_info}
Crops: {', '.join(selected_value_chains)}
Question: {prompt}

Answer using only the provided context. If no relevant info, say you don't have that data."""

    response = rag_chain.invoke({"input": enhanced_prompt})
    result = response['answer']
    sources = response.get('context', [])

    full_response = weather_info
    full_response += "---\n\n🤖 **Imarika's Agricultural Guidance**\n\n"

    # Check if the response indicates lack of information
    if "don't have" in result.lower() or "don't know" in result.lower() or "no information" in result.lower():
        full_response += f"🙏 I'm sorry, but I don't have specific information about that in my agricultural database.\n\n"
        full_response += f"🌾 **My Expertise:** I specialize in {', '.join(selected_value_chains)} and can only provide guidance based on the agricultural data available to me.\n\n"
        full_response += f"💬 **Suggestion:** Please ask questions related to: {', '.join(selected_value_chains)} farming practices, planting, harvesting, pest management, or soil preparation."
    else:
        full_response += result

    if sources:
        full_response += "\n\n---\n\n📄 **Information Sources**\n\n"
        for i, doc in enumerate(sources, 1):
            source_name = doc.metadata.get('source', 'Unknown source').split('/')[-1]
            if 'page' in doc.metadata:
                source_name += f" (Page {doc.metadata['page'] + 1})"
            if 'row' in doc.metadata:
                source_name += f" (Row {doc.metadata['row'] + 1})"
            full_response += f"{i}. {source_name}\n"

    return full_response

# --- Streamlit UI ---
st.title("🌾 Imarika - Your Agricultural Assistant")

# --- Session State Initialization ---
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Setup Workflow ---
if not st.session_state.setup_complete:
    st.header("Welcome! Let's get you set up.")

    with st.form("setup_form", clear_on_submit=True):
        location = st.text_input("📍 **First, what is your nearest town or city?** (e.g., Busia, Nairobi)", key="user_location_input")

        available_chains = get_value_chains_from_data()
        if not available_chains:
            st.error("Could not find any crop data files in the 'data' folder. Please add your CSV files.")
            st.stop()

        st.write("🌾 **Available Crops in Your Data:**")

        cols = st.columns(3)
        for i, crop in enumerate(available_chains):
            with cols[i % 3]:
                st.write(f"• {crop}")

        st.write("\n**Select the crops you want to focus on:**")
        selected = st.multiselect(
            "Choose your value chains (you can select multiple):",
            available_chains,
            default=[],
            help="Select the crops you're currently growing or planning to grow"
        )

        submitted = st.form_submit_button("Complete Setup", type="primary")

        if submitted:
            if location and selected:
                st.session_state.user_location = location
                st.session_state.selected_value_chains = selected
                st.session_state.setup_complete = True
                welcome_msg = f"🌾 **Habari! I'm Imarika, your agricultural assistant!**\n\n📍 **Your Location:** {st.session_state.user_location}\n🌱 **Your Selected Crops:** {', '.join(selected)}\n\n🎓 **My Expertise:**\n• I specialize ONLY in: Beans, Cassava, Finger Millet, Maize, Sorghum & Sweet Potatoes\n• I provide weather-informed advice based on your local agricultural data\n• I can respond in English or Swahili\n\n⚠️ **Important:** I can only help with information available in my agricultural database. If you ask about topics outside my expertise, I'll kindly let you know!\n\n**Karibu! Ready to help with your farming questions!**"
                st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
                st.rerun()
            if not location: st.warning("⚠️ Please enter your location.")
            if not selected: st.warning("⚠️ Please select at least one crop to continue.")

if not st.session_state.setup_complete:
    st.stop()

# --- Main Chat Interface ---

with st.sidebar:
    st.subheader("🌾 Your Setup")
    st.write(f"📍 **Location:** {st.session_state.user_location}")
    st.write(f"🌿 **Value Chains:** {', '.join(st.session_state.selected_value_chains)}")
    if st.button("Reset Setup"):
        keys_to_clear = ["user_location", "selected_value_chains", "setup_complete", "messages"]
        for key in keys_to_clear:
            st.session_state.pop(key, None)
        st.rerun()

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Load and process documents, and set up the RAG chain (cached for performance)
with st.spinner("Initializing system..."):
    try:
        rag_chain = load_and_process_documents(DATA_DIR, OLLAMA_EMBEDDING_MODEL, CHROMA_DB_DIR, OLLAMA_LLM_MODEL)
        if rag_chain is None:
            st.stop()
    except Exception as e:
        st.error("Failed to initialize system. Please ensure Ollama is running and models are available.")
        st.exception(e)
        st.stop()


# Accept user input
if prompt := st.chat_input("Ask Imarika about your crops... (Uliza Imarika kuhusu mazao yako...)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("🤔 Imarika is thinking..."):
            try:
                full_response = generate_assistant_response(
                    prompt,
                    rag_chain,
                    st.session_state.user_location,
                    st.session_state.selected_value_chains
                )

                final_response = stream_text(full_response, message_placeholder)
                st.session_state.messages.append({"role": "assistant", "content": final_response})

            except Exception as e:
                st.error(f"An error occurred during RAG processing: {e}")
                st.warning("Please ensure Ollama is running (`ollama serve`) and the models are pulled.")
                message_placeholder.markdown(f"Error: {e}")
                st.session_state.messages.append({"role": "assistant", "content": f"Error: {e}"})
