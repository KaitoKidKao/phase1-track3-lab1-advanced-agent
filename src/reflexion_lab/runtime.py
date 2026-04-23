from __future__ import annotations
import json
from .schemas import QAExample, JudgeResult, ReflectionEntry
from .llm_client import LLMClient
from .prompts import ACTOR_SYSTEM, EVALUATOR_SYSTEM, REFLECTOR_SYSTEM
from .utils import normalize_answer

llm = LLMClient()

def actor_answer(example: QAExample, attempt_id: int, agent_type: str, reflection_memory: list[str]) -> dict:
    context_str = "\n".join([f"[{c.title}] {c.text}" for c in example.context])
    
    prompt = f"Question: {example.question}\n\nContext:\n{context_str}\n"
    
    if reflection_memory:
        reflections_str = "\n".join([f"- {r}" for r in reflection_memory])
        prompt += f"\nPrevious Reflections:\n{reflections_str}\n"
        
    res = llm.generate(prompt, system_prompt=ACTOR_SYSTEM)
    
    text = res["text"]
    if "Final Answer:" in text:
        answer = text.split("Final Answer:")[-1].strip()
    else:
        answer = text.strip()
        
    return {
        "answer": answer,
        "full_response": text,
        "usage": res["usage"],
        "latency_ms": res["latency_ms"]
    }

def evaluator(example: QAExample, answer: str) -> dict:
    prompt = f"Question: {example.question}\nGold Answer: {example.gold_answer}\nPredicted Answer: {answer}"
    res = llm.generate(prompt, system_prompt=EVALUATOR_SYSTEM, json_mode=True)
    
    try:
        data = json.loads(res["text"])
        # Ensure score is int
        data["score"] = int(data.get("score", 0))
        return {
            "result": JudgeResult(**data),
            "usage": res["usage"],
            "latency_ms": res["latency_ms"]
        }
    except Exception as e:
        print(f"Evaluator JSON Parse Error: {e}. Text: {res['text']}")
        # Fallback
        score = 1 if normalize_answer(example.gold_answer) == normalize_answer(answer) else 0
        return {
            "result": JudgeResult(score=score, reason="Fallback evaluation due to JSON error"),
            "usage": res["usage"],
            "latency_ms": res["latency_ms"]
        }

def reflector(example: QAExample, attempt_id: int, judge: JudgeResult) -> dict:
    prompt = f"Question: {example.question}\nGold Answer: {example.gold_answer}\nReason for failure: {judge.reason}"
    res = llm.generate(prompt, system_prompt=REFLECTOR_SYSTEM, json_mode=True)
    
    try:
        data = json.loads(res["text"])
        data["attempt_id"] = attempt_id
        return {
            "entry": ReflectionEntry(**data),
            "usage": res["usage"],
            "latency_ms": res["latency_ms"]
        }
    except Exception as e:
        print(f"Reflector JSON Parse Error: {e}. Text: {res['text']}")
        return {
            "entry": ReflectionEntry(attempt_id=attempt_id, failure_reason="Fallback reflection", lesson="N/A", next_strategy="Try again"),
            "usage": res["usage"],
            "latency_ms": res["latency_ms"]
        }
