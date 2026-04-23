import json
import os
from datasets import load_dataset
from pathlib import Path

def prepare_hotpot_data(num_samples=100, output_path="data/hotpot_100.json"):
    print(f"Loading HotpotQA dataset (validation set, distractor)...")
    # Load the validation set of the 'distractor' configuration
    dataset = load_dataset("hotpot_qa", "distractor", split="validation")
    
    samples = []
    count = 0
    
    print(f"Processing and formatting {num_samples} samples...")
    for item in dataset:
        if count >= num_samples:
            break
            
        # Map HotpotQA fields to QAExample schema
        # context in HotpotQA is {'title': ['Title1', 'Title2'], 'sentences': [['S1', 'S2'], ['S3', 'S4']]}
        # We need to flatten sentences for each title
        context_chunks = []
        for title, sentences in zip(item['context']['title'], item['context']['sentences']):
            context_chunks.append({
                "title": title,
                "text": " ".join(sentences)
            })
            
        formatted_sample = {
            "qid": item['id'],
            "difficulty": item['level'], # easy, medium, hard
            "question": item['question'],
            "gold_answer": item['answer'],
            "context": context_chunks
        }
        
        samples.append(formatted_sample)
        count += 1
        if count % 10 == 0:
            print(f"Processed {count}/{num_samples} samples...")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully saved {len(samples)} samples to {output_path}")

if __name__ == "__main__":
    prepare_hotpot_data()
