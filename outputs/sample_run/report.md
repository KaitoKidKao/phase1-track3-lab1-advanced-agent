# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_mini.json
- Mode: openai
- Records: 200
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.97 | 0.98 | 0.01 |
| Avg attempts | 1 | 1.06 | 0.06 |
| Avg token estimate | 1505.5 | 1656.45 | 150.95 |
| Avg latency (ms) | 4070.54 | 4599.77 | 529.23 |

## Failure modes
```json
{
  "react": {
    "none": 97,
    "wrong_final_answer": 3
  },
  "reflexion": {
    "none": 98,
    "reflection_overfit": 2
  }
}
```

## Extensions implemented
- structured_evaluator
- reflection_memory
- benchmark_report_json
- mock_mode_for_autograding

## Discussion
Reflexion helps when the first attempt stops after the first hop or drifts to a wrong second-hop entity. The tradeoff is higher attempts, token cost, and latency. In a real report, students should explain when the reflection memory was useful, which failure modes remained, and whether evaluator quality limited gains.
