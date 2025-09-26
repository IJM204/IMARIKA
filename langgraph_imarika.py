import os
import json
import requests
import pandas as pd
from typing import Dict, List, Any, TypedDict
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langgraph.graph import StateGraph, END
import chromadb
from knowledge_graph import AgriKnowledgeGraph

# State definition
class AgentState(TypedDict):
    query: str
    plan: str
    tools_needed: List[str]
    weather_data: Dict[str, Any]
    knowledge_data: List[str]
    final_response: str
    step: str

# Initialize models
llm = OllamaLLM(model="llama3", temperature=0.1)
embeddings = OllamaEmbeddings(model="mxbai-embed-large")

class WeatherTool:
    def __init__(self):
        self.name = "weather_api"
        self.description = "Get current weather data for agricultural advice"
    
    def run(self, location: str) -> Dict[str, Any]:
        api_key = os.getenv("OPENWEATHER_API_KEY", "your_api_key_here")
        url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "temperature": data["main"]["temp"],
                    "humidity": data["main"]["humidity"],
                    "description": data["weather"][0]["description"],
                    "location": location
                }
        except:
            pass
        return {"error": "Weather data unavailable"}

class KnowledgeGraphTool:
    def __init__(self):
        self.name = "knowledge_graph"
        self.description = "Query agricultural knowledge graph for crop relationships"
        self.kg = AgriKnowledgeGraph()
    
    def run(self, query: str) -> List[str]:
        return self.kg.query(query)

# Initialize tools
weather_tool = WeatherTool()
knowledge_tool = KnowledgeGraphTool()

# Agent functions
def planner_agent(state: AgentState) -> AgentState:
    """Analyzes query and creates execution plan"""
    query = state["query"]
    
    prompt = f"""As Imarika, an agricultural assistant, analyze this query and determine what tools are needed:
Query: {query}

Available tools:
- weather_api: For weather-related questions
- knowledge_graph: For crop information from our database

Respond with:
1. PLAN: Brief execution strategy
2. TOOLS: List tools needed (weather_api, knowledge_graph, or both)

Focus only on: Beans, Cassava, Finger Millet, Maize, Sorghum, Sweet Potatoes."""
    
    response = llm.invoke(prompt)
    
    # Parse response
    tools_needed = []
    if "weather" in query.lower() or "temperature" in query.lower() or "rain" in query.lower():
        tools_needed.append("weather_api")
    if any(crop in query.lower() for crop in ["bean", "cassava", "millet", "maize", "sorghum", "potato"]):
        tools_needed.append("knowledge_graph")
    
    if not tools_needed:
        tools_needed.append("knowledge_graph")
    
    return {
        **state,
        "plan": response,
        "tools_needed": tools_needed,
        "step": "executor"
    }

def executor(state: AgentState) -> AgentState:
    """Executes tools based on plan"""
    query = state["query"]
    tools_needed = state["tools_needed"]
    
    weather_data = {}
    knowledge_data = []
    
    # Execute weather tool
    if "weather_api" in tools_needed:
        # Extract location from query or use default
        location = "Nairobi"  # Default location
        for word in query.split():
            if word.lower() in ["nairobi", "kampala", "dar", "kigali", "dodoma"]:
                location = word
                break
        weather_data = weather_tool.run(location)
    
    # Execute knowledge tool
    if "knowledge_graph" in tools_needed:
        knowledge_data = knowledge_tool.run(query)
    
    return {
        **state,
        "weather_data": weather_data,
        "knowledge_data": knowledge_data,
        "step": "synthesizer"
    }

def synthesizer(state: AgentState) -> AgentState:
    """Combines tool results and generates response"""
    query = state["query"]
    weather_data = state.get("weather_data", {})
    knowledge_data = state.get("knowledge_data", [])
    
    # Handle general questions about capabilities
    if any(phrase in query.lower() for phrase in ["what can you do", "what do you do", "who are you", "help", "capabilities"]):
        return {
            **state,
            "final_response": "🌾 Habari! Mimi ni Imarika, mshauri wako wa kilimo.\n\nNinaweza kukusaidia na:\n\n• 🌱 Mazao 6: Mahindi, Maharage, Mihogo, Ulezi, Mtama, Viazi vitamu\n• 🌤️ Hali ya hewa: Ushauri kulingana na mazingira ya sasa\n• 📊 Uhusiano wa mazao: Mbolea, wadudu, magonjwa\n• 🔄 Mipango ya kilimo: Kupanda, kulima, kuvuna\n• 💡 Ushauri wa kisasa: Kutumia teknolojia ya Knowledge Graph\n\nMfano wa maswali:\n- Mahindi yanahitaji mbolea gani?\n- Hali ya hewa inaathirije mihogo?\n- Wadudu gani wanashambulia maharage?\n- Ni wakati gani bora wa kupanda mtama?\n\nUliza swali lolote kuhusu mazao haya! 🚀",
            "step": "end"
        }
    
    # Check if query is outside our expertise
    crops = ["beans", "cassava", "finger millet", "maize", "sorghum", "sweet potatoes"]
    if not any(crop in query.lower() for crop in crops) and not weather_data:
        return {
            **state,
            "final_response": "Samahani, mimi ni Imarika, mshauri wa kilimo. Ninajua tu kuhusu mahindi, maharage, mihogo, ulezi, mtama, na viazi vitamu. Je, una swali kuhusu mazao haya?",
            "step": "end"
        }
    
    # Build context
    context = ""
    if knowledge_data:
        context += f"Agricultural Knowledge:\n{chr(10).join(knowledge_data[:3])}\n\n"
    
    if weather_data and "error" not in weather_data:
        context += f"Current Weather in {weather_data.get('location', 'Unknown')}:\n"
        context += f"Temperature: {weather_data.get('temperature', 'N/A')}°C\n"
        context += f"Humidity: {weather_data.get('humidity', 'N/A')}%\n"
        context += f"Conditions: {weather_data.get('description', 'N/A')}\n\n"
    
    prompt = f"""You are Imarika, a friendly agricultural assistant specializing in 6 crops: Beans, Cassava, Finger Millet, Maize, Sorghum, and Sweet Potatoes.

Context:
{context}

User Question: {query}

Provide a helpful response in English or Swahili as appropriate. Be practical and specific. If weather data is available, include relevant agricultural advice based on current conditions."""
    
    response = llm.invoke(prompt)
    
    return {
        **state,
        "final_response": response,
        "step": "end"
    }

def should_continue(state: AgentState) -> str:
    """Router function for conditional logic"""
    step = state.get("step", "planner")
    
    if step == "executor":
        return "executor"
    elif step == "synthesizer":
        return "synthesizer"
    else:
        return "end"

# Build the graph
def create_graph():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("planner", planner_agent)
    workflow.add_node("executor", executor)
    workflow.add_node("synthesizer", synthesizer)
    
    # Add edges
    workflow.set_entry_point("planner")
    workflow.add_conditional_edges(
        "planner",
        should_continue,
        {
            "executor": "executor",
            "end": END
        }
    )
    workflow.add_conditional_edges(
        "executor",
        should_continue,
        {
            "synthesizer": "synthesizer",
            "end": END
        }
    )
    workflow.add_edge("synthesizer", END)
    
    return workflow.compile()

# Main function
def run_imarika_agent(query: str) -> str:
    """Main function to run the LangGraph agent"""
    app = create_graph()
    
    initial_state = {
        "query": query,
        "plan": "",
        "tools_needed": [],
        "weather_data": {},
        "knowledge_data": [],
        "final_response": "",
        "step": "planner"
    }
    
    result = app.invoke(initial_state)
    return result["final_response"]

if __name__ == "__main__":
    # Test the system
    test_queries = [
        "What are the best practices for growing maize?",
        "How does weather affect cassava farming?",
        "Tell me about beans cultivation in Nairobi",
        "What is quantum physics?",  # Should be rejected
    ]
    
    print("🌾 Imarika LangGraph Agent Testing 🌾\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"Test {i}: {query}")
        print("-" * 50)
        response = run_imarika_agent(query)
        print(f"Response: {response}\n")