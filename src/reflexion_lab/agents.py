from __future__ import annotations
from dataclasses import dataclass
from typing import Literal
from .runtime import actor_answer, evaluator, reflector
from .schemas import AttemptTrace, QAExample, ReflectionEntry, RunRecord

@dataclass
class BaseAgent:
    agent_type: Literal["react", "reflexion"]
    max_attempts: int = 1
    def run(self, example: QAExample) -> RunRecord:
        reflection_memory: list[str] = []
        reflections: list[ReflectionEntry] = []
        traces: list[AttemptTrace] = []
        final_answer = ""
        final_score = 0
        
        for attempt_id in range(1, self.max_attempts + 1):
            # 1. Actor step
            actor_res = actor_answer(example, attempt_id, self.agent_type, reflection_memory)
            answer = actor_res["answer"]
            
            # 2. Evaluator step
            eval_res = evaluator(example, answer)
            judge = eval_res["result"]
            
            # 3. Track metrics
            total_usage = actor_res["usage"]["total_tokens"] + eval_res["usage"]["total_tokens"]
            total_latency = actor_res["latency_ms"] + eval_res["latency_ms"]
            
            # 4. Record trace
            trace = AttemptTrace(
                attempt_id=attempt_id, 
                answer=answer, 
                score=judge.score, 
                reason=judge.reason, 
                token_estimate=total_usage, 
                latency_ms=total_latency
            )
            
            final_answer = answer
            final_score = judge.score
            
            if judge.score == 1:
                traces.append(trace)
                break
            
            # 5. Reflexion step
            if self.agent_type == "reflexion" and attempt_id < self.max_attempts:
                refl_res = reflector(example, attempt_id, judge)
                reflection_entry = refl_res["entry"]
                
                reflections.append(reflection_entry)
                # Update reflection memory for next actor call
                reflection_memory.append(f"Attempt {attempt_id} failed. Lesson: {reflection_entry.lesson}. Strategy: {reflection_entry.next_strategy}")
                
                # Add reflection usage/latency to current trace
                trace.token_estimate += refl_res["usage"]["total_tokens"]
                trace.latency_ms += refl_res["latency_ms"]
                trace.reflection = reflection_entry
            
            traces.append(trace)
            
        total_tokens = sum(t.token_estimate for t in traces)
        total_latency = sum(t.latency_ms for t in traces)
        
        # Determine failure mode
        failure_mode = "none" if final_score == 1 else "wrong_final_answer"
        if final_score == 0 and len(traces) == self.max_attempts:
            failure_mode = "reflection_overfit" if self.agent_type == "reflexion" else "wrong_final_answer"
            
        return RunRecord(
            qid=example.qid, 
            question=example.question, 
            gold_answer=example.gold_answer, 
            agent_type=self.agent_type, 
            predicted_answer=final_answer, 
            is_correct=bool(final_score), 
            attempts=len(traces), 
            token_estimate=total_tokens, 
            latency_ms=total_latency, 
            failure_mode=failure_mode, 
            reflections=reflections, 
            traces=traces
        )

class ReActAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(agent_type="react", max_attempts=1)

class ReflexionAgent(BaseAgent):
    def __init__(self, max_attempts: int = 3) -> None:
        super().__init__(agent_type="reflexion", max_attempts=max_attempts)
