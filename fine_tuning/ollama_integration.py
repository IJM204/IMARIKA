import json
import subprocess
from pathlib import Path

class OllamaFineTuned:
    def __init__(self, dataset_path: str = "agri_dataset.jsonl"):
        self.dataset_path = dataset_path
        self.examples = self._load_examples()
        
    def _load_examples(self):
        """Load training examples for context"""
        examples = []
        if Path(self.dataset_path).exists():
            with open(self.dataset_path, 'r') as f:
                for line in f:
                    data = json.loads(line)
                    examples.append(data)
        return examples[:50]  # Use first 50 as context
    
    def generate_response(self, query: str, context: str = "") -> str:
        """Generate response using Ollama with fine-tuned context"""
        
        # Create enhanced system prompt with examples
        system_prompt = """You are Imarika, an agricultural expert for East African crops: beans, cassava, finger millet, maize, sorghum, and sweet potatoes.

Here are some example responses to learn from:
"""
        
        # Add few examples as context
        for i, example in enumerate(self.examples[:3]):
            messages = example.get("messages", [])
            if len(messages) >= 3:
                user_msg = messages[1]["content"]
                assistant_msg = messages[2]["content"]
                system_prompt += f"\nExample {i+1}:\nUser: {user_msg}\nImarika: {assistant_msg}\n"
        
        system_prompt += f"\nNow respond to this query in the same style:\nContext: {context}\nUser: {query}\nImarika:"
        
        # Use ollama CLI directly
        try:
            result = subprocess.run(
                ["ollama", "run", "llama3", system_prompt],
                capture_output=True,
                text=True,
                timeout=15
            )
            return result.stdout.strip()
        except Exception as e:
            return f"Error generating response: {e}"

def create_enhanced_synthesizer():
    """Create synthesizer that uses fine-tuned context"""
    fine_tuned_model = OllamaFineTuned()
    
    def synthesizer_agent(state):
        query = state.get("query", "")
        weather_data = state.get("weather_data", {})
        kg_data = state.get("kg_data", {})
        
        # Prepare context from tools
        context_parts = []
        if weather_data:
            context_parts.append(f"Weather: {weather_data}")
        if kg_data:
            context_parts.append(f"Knowledge: {kg_data}")
        
        context = " | ".join(context_parts)
        
        # Generate response with enhanced context
        response = fine_tuned_model.generate_response(query, context)
        
        return {"response": response}
    
    return synthesizer_agent

if __name__ == "__main__":
    # Test the enhanced model
    model = OllamaFineTuned()
    
    test_queries = [
        "What nutrients does maize need?",
        "How do I manage pests in beans?",
        "What weather is good for cassava?"
    ]
    
    print("🧠 Testing Enhanced Ollama with Agricultural Context:")
    for query in test_queries:
        print(f"\nQuery: {query}")
        response = model.generate_response(query)
        print(f"Response: {response}")