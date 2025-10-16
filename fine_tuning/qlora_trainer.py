import torch
from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer, 
    TrainingArguments, 
    Trainer,
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset
import json

class QLoRATrainer:
    def __init__(self, model_name: str = "meta-llama/Llama-2-7b-chat-hf"):
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    def setup_quantization_config(self):
        return BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True
        )
    
    def setup_lora_config(self):
        return LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=16,
            lora_alpha=32,
            lora_dropout=0.1,
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
        )
    
    def load_model_and_tokenizer(self):
        quantization_config = self.setup_quantization_config()
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            quantization_config=quantization_config,
            device_map="auto",
            torch_dtype=torch.float16
        )
        
        lora_config = self.setup_lora_config()
        self.model = get_peft_model(self.model, lora_config)
        
    def prepare_dataset(self, dataset_path: str):
        with open(dataset_path, 'r') as f:
            data = [json.loads(line) for line in f]
        
        def format_chat(example):
            messages = example["messages"]
            text = self.tokenizer.apply_chat_template(messages, tokenize=False)
            return {"text": text}
        
        dataset = Dataset.from_list(data)
        dataset = dataset.map(format_chat)
        
        def tokenize(example):
            tokens = self.tokenizer(
                example["text"],
                truncation=True,
                padding=False,
                max_length=512,
                return_tensors=None
            )
            tokens["labels"] = tokens["input_ids"].copy()
            return tokens
        
        return dataset.map(tokenize, remove_columns=dataset.column_names)
    
    def train(self, dataset_path: str, output_dir: str = "fine_tuning/imarika-llama3"):
        self.load_model_and_tokenizer()
        train_dataset = self.prepare_dataset(dataset_path)
        
        training_args = TrainingArguments(
            output_dir=output_dir,
            per_device_train_batch_size=4,
            gradient_accumulation_steps=4,
            num_train_epochs=3,
            learning_rate=2e-4,
            fp16=True,
            logging_steps=10,
            save_steps=500,
            warmup_steps=100,
            weight_decay=0.01,
            remove_unused_columns=False
        )
        
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            tokenizer=self.tokenizer
        )
        
        trainer.train()
        trainer.save_model()
        
if __name__ == "__main__":
    trainer = QLoRATrainer()
    trainer.train("fine_tuning/agri_dataset.jsonl")