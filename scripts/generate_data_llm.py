import os
import json
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

def generate_samples(batch_size=5, difficulty="medium"):
    prompt = f"""
    Hãy tạo {batch_size} mẫu dữ liệu câu hỏi đa chặng (multi-hop QA) theo định dạng JSON cho tập dữ liệu HotpotQA.
    Mức độ khó: {difficulty}

    Yêu cầu:
    1. Mỗi mẫu phải có: qid (duy nhất), difficulty ({difficulty}), question, gold_answer, và context (danh sách các đoạn văn liên quan).
    2. Context phải bao gồm ít nhất 2 đoạn văn (ContextChunk) có thông tin để trả lời câu hỏi. Mỗi đoạn văn có title và text.
    3. Câu hỏi phải yêu cầu suy luận qua ít nhất 2 bước (ví dụ: A là ai? A sinh ra ở đâu? Thành phố đó có con sông nào chảy qua?).
    4. Trả về một danh sách JSON.

    Định dạng JSON:
    [
      {{
        "qid": "gen_{difficulty}_{{timestamp}}",
        "difficulty": "{difficulty}",
        "question": "...",
        "gold_answer": "...",
        "context": [
          {{"title": "...", "text": "..."}},
          {{"title": "...", "text": "..."}}
        ]
      }}
    ]
    """
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.8
        )
        data = json.loads(response.choices[0].message.content)
        # Handle cases where the LLM might return a dict with a key instead of a list
        if isinstance(data, dict):
            for key in data:
                if isinstance(data[key], list):
                    return data[key]
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error generating batch: {e}")
        return []

def main():
    all_samples = []
    # Cấu hình số lượng cho mỗi độ khó
    difficulties = [("easy", 30), ("medium", 40), ("hard", 30)]
    
    print(f"Bắt đầu tạo 100 mẫu dữ liệu bằng {MODEL}...")
    
    for diff, total in difficulties:
        count = 0
        while count < total:
            batch_size = min(5, total - count)
            print(f"Đang tạo {batch_size} mẫu mức {diff}... ({count}/{total})")
            batch = generate_samples(batch_size, diff)
            if batch:
                # Ensure qid is unique
                for i, s in enumerate(batch):
                    s['qid'] = f"gen_{diff}_{int(time.time())}_{count+i}"
                all_samples.extend(batch)
                count += len(batch)
            time.sleep(1) # Tránh rate limit
            
    # Lưu file
    output_path = "data/hotpot_100.json"
    os.makedirs("data", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_samples, f, ensure_ascii=False, indent=2)
    
    print(f"\nThành công! Đã tạo {len(all_samples)} mẫu tại {output_path}")

if __name__ == "__main__":
    main()
