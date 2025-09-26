# 🌾 Imarika - Agricultural AI Assistant with LangGraph & Knowledge Graph

An intelligent agricultural advisory system powered by LangGraph, Knowledge Graph, and Ollama models. Specialized in 6 East African crops with multilingual support (English/Swahili).

## 🏗️ Architecture

```
┌─────────────────┐
│   User Input    │
└─────────────────┘
         │
         ▼
┌──────────────────┐
│   LangGraph      │
│ (Orchestrator)   │
└──────────────────┘
         │
┌────────┴─────────┐
▼                  ▼
┌────────────────┐  ┌────────────────┐
│ Planner Agent  │  │   Executor     │
│ (Query Analysis)│  │ (Tool Runner)  │
└────────────────┘  └────────────────┘
         │                  │
         ▼                  ▼
┌────────────────┐  ┌──────────────┐
│ Tool Router    │  │ Synthesizer  │
│ (Dynamic Gates)│  │ (Response)   │
└────────────────┘  └──────────────┘
         │
┌────────┴──────────────┐
▼          ▼          ▼
┌──────────────┐  ┌──────────────┐
│  Weather     │  │  Knowledge   │
│  API Tool    │  │  Graph Tool  │
└──────────────┘  └──────────────┘
```

## 📁 Project Structure

```
offline_agri_rag_ollama/
├── 🎯 Core System
│   ├── langgraph_imarika.py          # Main LangGraph agent system
│   ├── knowledge_graph.py            # Knowledge graph builder & query
│   ├── streamlit_openwebui_style.py  # Modern chat interface
│   └── run.py                        # Main runner script
│
├── 📊 Data & Storage
│   ├── data/                         # Agricultural CSV datasets
│   │   ├── beans.csv
│   │   ├── cassava.csv
│   │   ├── finger_millet.csv
│   │   ├── maize.csv
│   │   ├── sorghum.csv
│   │   └── sweet_potatoes.csv
│   └── chroma_db/                   # Vector database (legacy)
│
├── 🔧 Configuration
│   ├── requirements.txt             # Python dependencies
│   ├── .env.example                 # Environment variables template
│   ├── .streamlit/config.toml       # Streamlit configuration
│   ├── docker-compose.yml           # Docker setup
│   └── Dockerfile                   # Docker image definition
│
├── 📚 Legacy & Examples
│   ├── legacy/                      # Original implementations
│   │   ├── rag_agent+sw.py         # Original RAG system
│   │   ├── streamlit_app+sw.py     # Original Streamlit app
│   │   └── improvements_suggestions.py
│   └── examples/                    # Architecture examples
│       ├── agentic_architecture.py # LangGraph examples
│       └── streamlit_langgraph.py  # Alternative interfaces
│
└── 📖 Documentation
    ├── README.md                    # This file
    └── docs/                        # Architecture diagrams
        ├── Flowchart.jpg
        └── Flowchart1.jpg
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Ollama installed with models:
  - `llama3` (4.7GB)
  - `mxbai-embed-large` (669MB)
- OpenWeather API key (optional)

### Installation

1. **Clone & Setup**
```bash
git clone <repository>
cd offline_agri_rag_ollama
pip install -r requirements.txt
```

2. **Install Ollama Models**
```bash
ollama pull llama3
ollama pull mxbai-embed-large
```

3. **Environment Setup** (Optional)
```bash
cp .env.example .env
# Edit .env with your OpenWeather API key
```

4. **Run the System**
```bash
# Quick start - Chat interface
python run.py

# Or specific modes
python run.py chat      # Start chat interface
python run.py test      # Run system tests
python run.py build-kg  # Rebuild knowledge graph
```

## 🎯 Key Features

### 🧠 LangGraph Agent System
- **Planner Agent**: Analyzes queries and determines tool requirements
- **Tool Router**: Dynamic selection of weather API and/or knowledge graph
- **Executor**: Runs selected tools and gathers data
- **Synthesizer**: Combines results into coherent responses

### 📊 Knowledge Graph
- **22 Nodes**: Crops, nutrients, pests, activities, growth stages
- **72 Edges**: Relationships like "needs", "attacks", "affects"
- **Graph Queries**: Traversal-based information retrieval

### 🌤️ Weather Integration
- Real-time weather data from OpenWeather API
- Agricultural advice based on current conditions
- Location-aware recommendations

### 🌍 Multilingual Support
- English and Swahili responses
- Context-appropriate language selection
- East African agricultural terminology

## 🌱 Supported Crops

1. **Beans** (Maharage)
2. **Cassava** (Mihogo)
3. **Finger Millet** (Ulezi)
4. **Maize** (Mahindi)
5. **Sorghum** (Mtama)
6. **Sweet Potatoes** (Viazi vitamu)

## 💬 Usage Examples

### Capability Query
```
User: "What can you do?"
Imarika: "🌾 Habari! Mimi ni Imarika, mshauri wako wa kilimo..."
```

### Crop Information
```
User: "What nutrients does maize need?"
Imarika: "Maize needs Nitrogen, Phosphorus, Potassium, Manure, Compost..."
```

### Weather-based Advice
```
User: "How does weather affect cassava in Nairobi?"
Imarika: "Current weather in Nairobi: 22°C, 65% humidity..."
```

### Knowledge Graph Queries
```
User: "Tell me about bean pests"
Imarika: "Based on relationships: Weevil attacks Beans..."
```

## 🔧 Configuration

### Streamlit Config (`.streamlit/config.toml`)
```toml
[theme]
primaryColor = "#2E8B57"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F8F0"

[server]
fileWatcherType = "none"
```

### Environment Variables
```bash
OPENWEATHER_API_KEY=your_api_key_here  # Optional for weather features
```

## 🐳 Docker Deployment

```bash
# Build and run
docker-compose up -d

# Access at http://localhost:8501
```

## 🧪 Testing

### Test Knowledge Graph
```bash
python knowledge_graph.py
# Output: Shows nodes, edges, and relationship queries
```

### Test LangGraph Agent
```bash
python langgraph_imarika.py
# Output: Runs test queries through the full pipeline
```

### Interactive Testing
```bash
streamlit run streamlit_openwebui_style.py
# Access: http://localhost:8501
```

## 🔄 System Flow

1. **User Input** → Query received
2. **Planner Agent** → Analyzes intent and determines tools needed
3. **Tool Router** → Selects weather API and/or knowledge graph
4. **Executor** → Runs tools and gathers data
5. **Synthesizer** → Combines results and generates response
6. **Response** → Delivered to user via chat interface

## 📈 Performance

- **Knowledge Graph**: 22 nodes, 72 relationships
- **Response Time**: ~2-5 seconds (depending on Ollama model)
- **Memory Usage**: ~2GB (with loaded models)
- **Supported Languages**: English, Swahili

## 🛠️ Troubleshooting

### Common Issues

1. **Ollama Models Not Found**
```bash
ollama list  # Check installed models
ollama pull llama3  # Install missing models
```

2. **Knowledge Graph Empty**
```bash
python knowledge_graph.py  # Rebuild graph from CSV data
```

3. **Streamlit Port Issues**
```bash
streamlit run streamlit_openwebui_style.py --server.port 8502
```

4. **Weather API Errors**
- Check API key in environment variables
- System works without weather data if API unavailable

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Ollama** for local LLM inference
- **LangGraph** for agent orchestration
- **NetworkX** for knowledge graph implementation
- **Streamlit** for web interface
- **OpenWeather** for weather data API

---

**Built with ❤️ for East African farmers**