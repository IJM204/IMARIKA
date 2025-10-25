#!/usr/bin/env python3
"""
QLoRA Fine-tuned Model Integration for Imarika
Integrates the imarika_csv_qlora_model.zip into the system
"""

import os
import zipfile
import torch
import json
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel
import subprocess
import time

class QLoRAImarika:
    def __init__(self, model_zip_path="imarika_csv_qlora_model.zip"):
        self.model_path = None
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Extract and load model
        if os.path.exists(model_zip_path):
            self.extract_model(model_zip_path)
            self.load_model()
        else:
            print(f"Model zip not found: {model_zip_path}")
    
    def extract_model(self, zip_path):
        """Extract the model from zip file"""
        extract_dir = "fine_tuning/qlora_model"
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        self.model_path = extract_dir
        print(f"✅ Model extracted to: {extract_dir}")
    
    def load_model(self):
        """Load the fine-tuned model"""
        try:
            # Load base model with quantization
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16
            )
            
            # Find base model name from config
            base_model = "unsloth/Llama-3.2-3B-Instruct"  # Default
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(base_model)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load base model
            base_model_obj = AutoModelForCausalLM.from_pretrained(
                base_model,
                quantization_config=bnb_config,
                device_map="auto",
                torch_dtype=torch.bfloat16
            )
            
            # Load LoRA adapter
            self.model = PeftModel.from_pretrained(base_model_obj, self.model_path)
            
            print("✅ QLoRA model loaded successfully")
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.model = None
    
    def generate_response(self, query, context="", max_length=512):
        """Generate response using fine-tuned model"""
        if not self.model or not self.tokenizer:
            return "Model not loaded"
        
        # Format prompt
        system_prompt = "You are an agricultural assistant specializing in East African crops: Beans, Cassava, Finger Millet, Maize, Sorghum, and Sweet Potatoes."
        
        if context:
            full_prompt = f"{system_prompt}\n\nContext: {context}\n\nQuestion: {query}\n\nAnswer:"
        else:
            full_prompt = f"{system_prompt}\n\nQuestion: {query}\n\nAnswer:"
        
        try:
            # Tokenize
            inputs = self.tokenizer(
                full_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=1024
            ).to(self.device)
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_length,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.1
                )
            
            # Decode response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the answer part
            if "Answer:" in response:
                response = response.split("Answer:")[-1].strip()
            
            return response
            
        except Exception as e:
            return f"Generation error: {str(e)}"
    
    def is_available(self):
        """Check if model is loaded and ready"""
        return self.model is not None and self.tokenizer is not None

# Fallback to Ollama if QLoRA not available
class OllamaFallback:
    def generate_response(self, query, context=""):
        try:
            prompt = f"Agricultural assistant for East African crops.\nContext: {context}\nQ: {query}\nA:"
            
            result = subprocess.run(
                ["ollama", "run", "llama3", prompt],
                capture_output=True,
                text=True,
                timeout=15
            )
            return result.stdout.strip()
        except:
            return "Ollama unavailable"
    
    def is_available(self):
        return True

# Main integration class
class IntegratedImarika:
    def __init__(self):
        # Try to load QLoRA model first
        self.qlora_model = QLoRAImarika()
        self.ollama_model = OllamaFallback()
        
        # Determine which model to use
        self.use_qlora = self.qlora_model.is_available()
        
        print(f"🌾 Imarika Integration Status:")
        print(f"   QLoRA Model: {'✅ Available' if self.use_qlora else '❌ Not Available'}")
        print(f"   Ollama Fallback: ✅ Available")
        print(f"   Active Model: {'QLoRA Fine-tuned' if self.use_qlora else 'Ollama Base'}")
    
    def generate_response(self, query, context=""):
        """Generate response using best available model"""
        if self.use_qlora:
            return self.qlora_model.generate_response(query, context)
        else:
            return self.ollama_model.generate_response(query, context)
    
    def get_model_info(self):
        """Get information about active model"""
        return {
            "model_type": "QLoRA Fine-tuned" if self.use_qlora else "Ollama Base",
            "qlora_available": self.use_qlora,
            "device": self.qlora_model.device if self.use_qlora else "CPU"
        }

if __name__ == "__main__":
    # Test the integration
    print("🧪 Testing QLoRA Integration...")
    
    imarika = IntegratedImarika()
    
    # Test queries
    test_queries = [
        "What nutrients does maize need?",
        "How to control pests in beans?",
        "Best planting time for cassava?",
        "Sorghum drought resistance tips"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("=" * 50)
        
        start_time = time.time()
        response = imarika.generate_response(query)
        end_time = time.time()
        
        print(f"Response: {response}")
        print(f"Time: {end_time - start_time:.2f}s")
        print(f"Model: {imarika.get_model_info()['model_type']}")