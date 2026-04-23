import os
import time
from typing import Any, Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    """
    Client for interacting with OpenAI API.
    Handles token usage tracking and latency measurement.
    """
    def __init__(self, model: str = "gpt-4o-mini"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # Fallback for initialization, will error on call if still missing
            print("Warning: OPENAI_API_KEY not found in environment.")
            
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL_NAME", model)

    def generate(self, prompt: str, system_prompt: Optional[str] = None, json_mode: bool = False) -> Dict[str, Any]:
        """
        Generates a response from the LLM.
        """
        start_time = time.time()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response_format = {"type": "json_object"} if json_mode else None
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0, # Better for reasoning/consistency
                response_format=response_format
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return {
                "text": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "latency_ms": latency_ms
            }
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return {
                "text": f"Error: {str(e)}",
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "latency_ms": int((time.time() - start_time) * 1000)
            }
