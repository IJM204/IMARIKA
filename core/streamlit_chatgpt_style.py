import streamlit as st
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from langgraph_imarika import run_imarika_agent
from knowledge_graph import AgriKnowledgeGraph
import matplotlib.pyplot as plt
import networkx as nx

# Page config
st.set_page_config(
    page_title="Imarika AI",
    page_icon="🌾",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_location" not in st.session_state:
    st.session_state.user_location = None
if "weather_data" not in st.session_state:
    st.session_state.weather_data = None

# Sidebar
with st.sidebar:
    st.title("🌾 Imarika AI")
    st.markdown("**Agricultural Assistant**")
    
    # Navigation
    page = st.selectbox(
        "Choose a page:",
        ["💬 Chat", "📊 Knowledge Graph", "📋 Graph Data"]
    )
    
    st.markdown("---")
    
    # Location input
    st.markdown("**📍 Your Location**")
    location_input = st.text_input(
        "Enter your location:",
        value=st.session_state.user_location or "Nairobi",
        placeholder="e.g., Nairobi, Kampala, Dar es Salaam"
    )
    
    if st.button("🌤️ Update Weather", use_container_width=True):
        if location_input:
            st.session_state.user_location = location_input
            # Fetch weather data
            try:
                import requests
                api_key = os.getenv("OPENWEATHER_API_KEY", "your_api_key_here")
                url = f"http://api.openweathermap.org/data/2.5/weather?q={location_input}&appid={api_key}&units=metric"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    st.session_state.weather_data = response.json()
                    st.success(f"Weather updated for {location_input}")
                else:
                    st.error("Could not fetch weather data")
            except:
                st.error("Weather service unavailable")
            st.rerun()
    
    # Display current weather
    if st.session_state.weather_data:
        weather = st.session_state.weather_data
        st.markdown(f"**Current Weather in {st.session_state.user_location}:**")
        st.info(f"🌡️ {weather['main']['temp']}°C | 💧 {weather['main']['humidity']}% | {weather['weather'][0]['description'].title()}")
    
    st.markdown("---")
    
    # Clear chat button
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    
    # System info
    st.markdown("**System Info**")
    st.info("""
    **Model**: Llama3 + LangGraph  
    **Knowledge**: 22 nodes, 72 edges  
    **Crops**: 6 specialized crops  
    **Languages**: English & Swahili
    """)

# Main content area
if page == "💬 Chat":
    st.title("💬 Chat with Imarika")
    
    # Welcome message if no chat history
    if not st.session_state.messages:
        st.markdown("""
        ### 👋 Habari! Mimi ni Imarika, mshauri wako wa kilimo.
        
        Ninaweza kukusaidia na:
        - 🌱 **Mazao 6**: Mahindi, Maharage, Mihogo, Ulezi, Mtama, Viazi vitamu
        - 🌤️ **Hali ya hewa**: Ushauri kulingana na mazingira ya sasa
        - 📊 **Uhusiano wa mazao**: Mbolea, wadudu, magonjwa
        
        **Mfano wa maswali:**
        """)
        
        # Quick start buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("What nutrients does maize need?", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "What nutrients does maize need?"})
                st.rerun()
            if st.button("Tell me about bean pests", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "Tell me about bean pests"})
                st.rerun()
        
        with col2:
            if st.button("How does weather affect cassava?", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "How does weather affect cassava?"})
                st.rerun()
            if st.button("Best practices for sorghum farming", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "Best practices for sorghum farming"})
                st.rerun()
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about crops, weather, or farming practices..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Imarika is thinking..."):
                try:
                    # Pass location context to the agent
                    if st.session_state.user_location:
                        location_context = f" [User location: {st.session_state.user_location}]"
                        enhanced_prompt = prompt + location_context
                    else:
                        enhanced_prompt = prompt
                    
                    response = run_imarika_agent(enhanced_prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = "Samahani, kuna tatizo la kiufundi. Jaribu tena baadaye."
                    st.markdown(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

elif page == "📊 Knowledge Graph":
    st.title("📊 Knowledge Graph Visualization")
    
    try:
        kg = AgriKnowledgeGraph()
        
        # Statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Nodes", kg.graph.number_of_nodes())
        with col2:
            st.metric("Total Edges", kg.graph.number_of_edges())
        with col3:
            node_types = len(set(d.get('type', 'unknown') for _, d in kg.graph.nodes(data=True)))
            st.metric("Node Types", node_types)
        
        # Create visualization
        fig, ax = plt.subplots(figsize=(12, 8))
        pos = nx.spring_layout(kg.graph, k=2, iterations=50)
        
        # Colors for node types
        colors = {
            'crop': '#10b981', 'nutrient': '#3b82f6', 'pest': '#ef4444',
            'activity': '#f59e0b', 'stage': '#8b5cf6'
        }
        
        # Draw nodes by type
        for node_type, color in colors.items():
            nodes = [n for n, d in kg.graph.nodes(data=True) if d.get('type') == node_type]
            if nodes:
                nx.draw_networkx_nodes(kg.graph, pos, nodelist=nodes, 
                                     node_color=color, node_size=800, alpha=0.8, ax=ax)
        
        # Draw edges and labels
        nx.draw_networkx_edges(kg.graph, pos, alpha=0.3, width=1, edge_color='gray', ax=ax)
        nx.draw_networkx_labels(kg.graph, pos, font_size=8, ax=ax)
        
        ax.set_title("Agricultural Knowledge Graph", fontsize=16, pad=20)
        ax.axis('off')
        
        # Legend
        legend_elements = []
        for node_type, color in colors.items():
            nodes = [n for n, d in kg.graph.nodes(data=True) if d.get('type') == node_type]
            if nodes:
                legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                                 markerfacecolor=color, markersize=10, 
                                                 label=f"{node_type.title()} ({len(nodes)})"))
        
        if legend_elements:
            ax.legend(handles=legend_elements, loc='upper right', fontsize=10)
        
        st.pyplot(fig)
        
    except Exception as e:
        st.error(f"Error loading knowledge graph: {e}")

elif page == "📋 Graph Data":
    st.title("📋 Knowledge Graph Data")
    
    try:
        kg = AgriKnowledgeGraph()
        
        # Statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Nodes", kg.graph.number_of_nodes())
        with col2:
            st.metric("Total Edges", kg.graph.number_of_edges())
        with col3:
            node_types = len(set(d.get('type', 'unknown') for _, d in kg.graph.nodes(data=True)))
            st.metric("Node Types", node_types)
        
        # Nodes by type
        st.subheader("Nodes by Type")
        for node_type in ['crop', 'nutrient', 'pest', 'activity', 'stage']:
            nodes = [n for n, d in kg.graph.nodes(data=True) if d.get('type') == node_type]
            if nodes:
                with st.expander(f"{node_type.title()}s ({len(nodes)})"):
                    st.write(", ".join(nodes))
        
        # Sample relationships
        st.subheader("Sample Relationships")
        relationships = []
        for source, target, data in list(kg.graph.edges(data=True))[:20]:
            relation = data.get('relation', 'related_to')
            relationships.append(f"{source} → **{relation}** → {target}")
        
        for i, rel in enumerate(relationships, 1):
            st.write(f"{i}. {rel}")
            
    except Exception as e:
        st.error(f"Error loading graph data: {e}")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "<p>🌾 Imarika AI - Built with ❤️ for East African farmers</p>"
    "</div>", 
    unsafe_allow_html=True
)