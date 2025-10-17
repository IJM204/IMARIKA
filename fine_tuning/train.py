#!/usr/bin/env python3

import argparse
from dataset_generator import AgriDatasetGenerator

try:
    from qlora_trainer import QLoRATrainer
    from evaluator import AgriEvaluator
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("Transformers not available. Only dataset generation supported.")
    TRANSFORMERS_AVAILABLE = False

def main():
    parser = argparse.ArgumentParser(description="Fine-tune Llama3 for Agricultural Assistant")
    parser.add_argument("--stage", choices=["generate", "train", "evaluate", "all"], 
                       default="all", help="Which stage to run")
    parser.add_argument("--samples", type=int, default=2000, 
                       help="Number of training samples to generate")
    parser.add_argument("--model", default="meta-llama/Llama-2-7b-chat-hf",
                       help="Base model to fine-tune")
    
    args = parser.parse_args()
    
    if args.stage in ["generate", "all"]:
        print("🌾 Generating agricultural dataset...")
        generator = AgriDatasetGenerator()
        dataset = generator.generate_instruction_pairs(args.samples)
        generator.save_dataset(dataset)
        print(f"✅ Generated {len(dataset)} training samples")
    
    if args.stage in ["train", "all"]:
        print("🚀 Starting QLoRA fine-tuning...")
        trainer = QLoRATrainer(args.model)
        trainer.train("fine_tuning/agri_dataset.jsonl")
        print("✅ Fine-tuning completed")
    
    if args.stage in ["evaluate", "all"]:
        print("📊 Evaluating model performance...")
        evaluator = AgriEvaluator(
            base_model_path=args.model,
            adapter_path="fine_tuning/imarika-llama3"
        )
        results = evaluator.run_evaluation()
        print("✅ Evaluation results:")
        print(f"   Base model accuracy: {results['crop_accuracy']['base_avg']:.2%}")
        print(f"   Fine-tuned accuracy: {results['crop_accuracy']['fine_tuned_avg']:.2%}")
        print(f"   Improvement: {results['crop_accuracy']['improvement']:.2%}")

if __name__ == "__main__":
    main()