import streamlit as st
import time
from langgraph_imarika import run_imarika_agent

# Page config
st.set_page_config(
    page_title="Imarika AI",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# OpenWebUI-style CSS
st.markdown("""
<style>
/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Main container */
.main {
    padding: 0;
    margin: 0;
}

/* Chat container */
.chat-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    height: 100vh;
    display: flex;
    flex-direction: column;
}

/* Header */
.chat-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 15px 20px;
    border-radius: 12px;
    margin-bottom: 20px;
    text-align: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

/* Messages container */
.messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 10px 0;
    margin-bottom: 20px;
}

/* User message */
.user-message {
    background: #007bff;
    color: white;
    padding: 12px 16px;
    border-radius: 18px 18px 4px 18px;
    margin: 8px 0 8px auto;
    max-width: 70%;
    word-wrap: break-word;
    box-shadow: 0 2px 8px rgba(0,123,255,0.3);
}

/* Assistant message */
.assistant-message {
    background: #f8f9fa;
    color: #333;
    padding: 12px 16px;
    border-radius: 18px 18px 18px 4px;
    margin: 8px auto 8px 0;
    max-width: 70%;
    word-wrap: break-word;
    border: 1px solid #e9ecef;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

/* Input container */
.input-container {
    position: sticky;
    bottom: 0;
    background: white;
    padding: 15px 0;
    border-top: 1px solid #e9ecef;
}

/* Typing indicator */
.typing-indicator {
    display: flex;
    align-items: center;
    padding: 12px 16px;
    margin: 8px auto 8px 0;
    max-width: 70%;
    background: #f8f9fa;
    border-radius: 18px 18px 18px 4px;
    border: 1px solid #e9ecef;
}

.typing-dots {
    display: flex;
    gap: 4px;
}

.typing-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #6c757d;
    animation: typing 1.4s infinite ease-in-out;
}

.typing-dot:nth-child(1) { animation-delay: -0.32s; }
.typing-dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
    0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
    40% { transform: scale(1); opacity: 1; }
}

/* Model info */
.model-info {
    background: rgba(255,255,255,0.9);
    backdrop-filter: blur(10px);
    padding: 8px 12px;
    border-radius: 20px;
    font-size: 12px;
    color: #6c757d;
    margin-bottom: 10px;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.2);
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 6px;
}

::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 3px;
}

::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "is_typing" not in st.session_state:
    st.session_state.is_typing = False

# Main container
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# Header
st.markdown("""
<div class="chat-header">
    <h2>🌾 Imarika AI</h2>
    <p>Your Agricultural Assistant with Knowledge Graph Intelligence</p>
</div>
""", unsafe_allow_html=True)

# Model info
st.markdown("""
<div class="model-info">
    🤖 Powered by Llama3 • 📊 Knowledge Graph • 🌤️ Weather API • 🔄 LangGraph
</div>
""", unsafe_allow_html=True)

# Messages container
messages_container = st.container()

with messages_container:
    # Welcome message if no messages
    if not st.session_state.messages:
        st.markdown("""
        <div class="assistant-message">
            👋 Habari! Mimi ni Imarika, mshauri wako wa kilimo. Ninaweza kukusaidia na:<br><br>
            🌱 <strong>Mazao</strong>: Mahindi, Maharage, Mihogo, Ulezi, Mtama, Viazi vitamu<br>
            🌤️ <strong>Hali ya hewa</strong>: Ushauri kulingana na mazingira<br>
            📊 <strong>Uhusiano wa mazao</strong>: Mbolea, wadudu, magonjwa<br><br>
            Uliza swali lolote kuhusu kilimo!
        </div>
        """, unsafe_allow_html=True)
    
    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
        else:
            # Convert newlines to HTML breaks for proper display
            formatted_content = message["content"].replace('\n', '<br>')
            st.markdown(f'<div class="assistant-message">{formatted_content}</div>', unsafe_allow_html=True)
    
    # Typing indicator
    if st.session_state.is_typing:
        st.markdown("""
        <div class="typing-indicator">
            <span style="margin-right: 8px;">Imarika is thinking</span>
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Input container
st.markdown('<div class="input-container">', unsafe_allow_html=True)

# Chat input
if prompt := st.chat_input("Ask about crops, weather, or farming practices...", key="chat_input"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.is_typing = True
    st.rerun()

# Process message if typing
if st.session_state.is_typing and st.session_state.messages:
    last_message = st.session_state.messages[-1]
    if last_message["role"] == "user":
        try:
            # Get response from LangGraph agent
            response = run_imarika_agent(last_message["content"])
            
            # Add assistant response
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.is_typing = False
            st.rerun()
            
        except Exception as e:
            error_msg = f"Samahani, kuna tatizo la kiufundi. Jaribu tena baadaye."
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            st.session_state.is_typing = False
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)  # Close input container
st.markdown('</div>', unsafe_allow_html=True)  # Close chat container

# Sidebar with quick actions (hidden by default)
with st.sidebar:
    st.header("🔧 Quick Actions")
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.is_typing = False
        st.rerun()
    
    st.markdown("---")
    
    st.subheader("🚀 Example Queries")
    example_queries = [
        "What nutrients does maize need?",
        "How does weather affect cassava?",
        "Tell me about bean pests",
        "Planting advice for sorghum"
    ]
    
    for query in example_queries:
        if st.button(query, key=f"example_{hash(query)}"):
            st.session_state.messages.append({"role": "user", "content": query})
            st.session_state.is_typing = True
            st.rerun()
    
    st.markdown("---")
    
    st.subheader("📊 System Info")
    st.info("""
    **Architecture**: LangGraph Agent
    **Knowledge**: Graph-based relationships
    **Crops**: 6 specialized crops
    **Languages**: English & Swahili
    """)