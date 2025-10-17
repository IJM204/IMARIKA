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
│   ├── core/                        # Main application logic
│   ├── data/                        # Agricultural datasets
│   └── run.py                       # Main runner script
│
├── 🎨 Professional Frontend
│   ├── frontend/                    # Top-notch UI/UX system
│   └── run_frontend.py              # Frontend launcher
│
├── 🧠 Fine-Tuning System
│   └── fine_tuning/                 # Complete fine-tuning pipeline
│
├── 📚 Documentation
│   ├── docs/                        # Technical documentation
│   ├── README.md                    # This file
│   ├── SETUP.md                     # Quick setup guide
│   └── PROJECT_STRUCTURE.md         # Detailed file organization
│
├── 🧪 Testing & Evaluation
│   ├── tests/                       # Unit and integration tests
│   └── evaluation/                  # Performance metrics and reports
│
├── 🔧 Configuration
│   ├── utils/                       # Utility scripts
│   ├── requirements.txt             # Dependencies
│   └── .streamlit/                  # Streamlit configuration
│
└── 📚 Legacy & Examples
    ├── legacy/                      # Original implementations
    └── examples/                    # Architecture examples
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed file organization.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Ollama installed with models:
  - `llama3` (4.7GB)
  - `mxbai-embed-large` (669MB)
- OpenWeather API key (optional)
- **For Fine-Tuning**: GPU with 8GB+ VRAM (RTX 3070/4060 Ti or better)

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
# Professional Frontend (Recommended for showcase)
python run_frontend.py

# Or legacy interface
python run.py chat      # Basic chat interface

# Other modes
python run.py test      # Run system tests
python run.py build-kg  # Rebuild knowledge graph
```

### 🧠 Fine-Tuning Llama3 (Optional)

Transform Llama3 into a specialized agricultural expert:

```bash
# Install fine-tuning dependencies
cd fine_tuning
pip install -r requirements.txt

# Generate agricultural dataset (2000 samples)
python train.py --stage generate --samples 2000

# Fine-tune with QLoRA (2-4 hours with GPU)
python train.py --stage train

# Evaluate performance improvement
python train.py --stage evaluate

# Run all stages
python train.py --stage all
```

**Hardware Requirements:**
- **Minimum**: 8GB GPU VRAM
- **Recommended**: 12GB+ GPU VRAM
- **Training Time**: 2-4 hours

**Performance Improvements:**
- **+107.9% overall performance** improvement
- **+400% more complete** responses
- **+201% more agricultural** terminology
- **+60% more accurate** information
- Maintains existing LangGraph architecture

**Evaluation Metrics:**
```bash
# Run performance comparison
python metrics_comparison.py

# View detailed analysis
python show_improvements.py
```

See [FINE_TUNING_DOCUMENTATION.md](FINE_TUNING_DOCUMENTATION.md) for detailed performance metrics and evaluation results.

## 🎯 Key Features

### 🧠 LangGraph Agent System
- **Planner Agent**: Analyzes queries and determines tool requirements
- **Tool Router**: Dynamic selection of weather API and/or knowledge graph
- **Executor**: Runs selected tools and gathers data
- **Synthesizer**: Combines results into coherent responses

### 📊 Enhanced Knowledge Graph
- **30+ Nodes**: Crops, nutrients, pests, diseases, activities, growth stages
- **95+ Edges**: Relationships like "needs", "attacks", "affects"
- **Graph Queries**: Traversal-based information retrieval
- **Interactive Viewer**: Separate navigation pages for visualization and data

### 🌤️ Location-Based Weather Integration
- **User Location Input**: Configurable location in sidebar
- **Real-time Weather**: Current conditions (temperature, humidity, wind, pressure)
- **3-Day Forecast**: Extended weather predictions for agricultural planning
- **Location-Aware Advice**: Agricultural recommendations based on local weather
- **Dynamic Updates**: Change location anytime for updated weather data

### 💬 Modern Chat Interface
- Clean, professional design with sidebar navigation
- Native Streamlit chat components with typing indicators
- Built-in recommendations for quick queries
- Separate pages for Chat, Graph Visualization, and Graph Data
- Persistent location and weather display

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

## 📊 Knowledge Graph Visualization

### Interactive Viewer
- Built into the chat interface
- Expandable section with graph visualization
- Real-time graph statistics and node information

### Generate Standalone Visualization
```bash
python -m utils.visualize_knowledge_graph
```

**Outputs:**
- `knowledge_graph_visualization.png` - Visual network diagram
- `knowledge_graph_data.json` - Complete graph data for analysis

### Graph Statistics
- **Nodes**: 30+ (6 crops, 7 nutrients, 8+ pests/diseases, 5 activities, 4 stages)
- **Relationships**: 95+ connections
- **Relation Types**: needs, attacks, affects, requires, has_stage

### Node Categories
```
Crops: Beans, Cassava, Finger Millet, Maize, Sorghum, Sweet Potatoes
Nutrients: Nitrogen, Phosphorus, Potassium, Manure, Compost, DAP, NPK
Pests & Diseases: Insects, Weevil, Borer, Rodents, Diseases, Rot, Fungal
Activities: Land preparation, Planting, Nutrient Management, Harvesting
Stages: Planting, Harvest (growth stages extracted from data)
```

## 🧪 Testing

### Test Knowledge Graph
```bash
python run.py build-kg
# Output: Shows nodes, edges, and relationship queries
```

### Test LangGraph Agent
```bash
python run.py test
# Output: Runs test queries through the full pipeline
```

### Test Fine-Tuned Model
```bash
cd fine_tuning
python evaluator.py
# Output: Compares base vs fine-tuned model accuracy
```

### Performance Evaluation
```bash
python evaluation/metrics/metrics_comparison.py
# Output: Comprehensive performance metrics comparison

python evaluation/reports/show_improvements.py
# Output: Dataset analysis and system improvements
```

### Interactive Testing
```bash
python run.py chat
# Access: http://localhost:8501
```

## 🔄 System Flow

1. **User Input** → Query received via ChatGPT-style interface
2. **Planner Agent** → Analyzes intent and determines tools needed
3. **Tool Router** → Selects weather API and/or knowledge graph
4. **Executor** → Runs tools and gathers data
5. **Synthesizer** → Combines results and generates response
6. **Response** → Delivered with typing animation and formatting

## 📈 Performance

- **Knowledge Graph**: 30+ nodes, 95+ relationships
- **Response Time**: ~2-5 seconds (depending on Ollama model)
- **Memory Usage**: ~2GB (with loaded models)
- **Weather Data**: Real-time + 3-day forecast
- **Supported Languages**: English, Swahili
- **Interface**: Modern Streamlit design with sidebar navigation

## 🛠️ Troubleshooting

### Common Issues

1. **Ollama Models Not Found**
```bash
ollama list  # Check installed models
ollama pull llama3  # Install missing models
```

2. **Knowledge Graph Empty**
```bash
python run.py build-kg  # Rebuild graph from CSV data
```

3. **Streamlit Port Issues**
```bash
python run.py chat --server.port 8502
```

4. **Import Errors**
```bash
# Ensure you're in the project root directory
cd offline_agri_rag_ollama
python run.py
```

5. **Weather API Errors**
- Check API key in environment variables
- System works without weather data if API unavailable

6. **Fine-Tuning Issues**
```bash
# Check GPU availability
python -c "import torch; print(torch.cuda.is_available())"

# Reduce batch size if out of memory
# Edit qlora_trainer.py: per_device_train_batch_size=2

# Use CPU fallback (slower)
# System automatically falls back to Ollama if fine-tuned model unavailable
```

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

**Built with hineni for East African farmers**