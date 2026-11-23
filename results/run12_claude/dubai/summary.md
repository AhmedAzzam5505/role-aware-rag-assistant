# Evaluation results (2026-11-24, mode=offline, corpus=dubai)

Rates in brackets are 95% Wilson confidence intervals.

## Test set: dubai (45 questions)

| Metric | normal/A | normal/B | mistagged_all/A | mistagged_all/B |
|---|---|---|---|---|
| accuracy_% | 38.5 | 42.3 | 46.2 | 38.5 |
| accuracy_95ci | 38.5% [22.4, 57.5] | 42.3% [25.5, 61.1] | 46.2% [28.8, 64.5] | 38.5% [22.4, 57.5] |
| faithfulness_proxy_% | 76.9 | 100.0 | 82.1 | 93.3 |
| leak_rate_restricted_% | 0.0 | 0.0 | 16.7 | 0.0 |
| leak_rate_95ci | 0.0% [0.0, 39.0] | 0.0% [0.0, 39.0] | 16.7% [3.0, 56.4] | 0.0% [0.0, 39.0] |
| leaks_all_questions | 0 | 0 | 1 | 0 |
| over_refusal_% | 50.0 | 57.7 | 50.0 | 61.5 |
| unanswerable_refused_% | 100.0 | 100.0 | 100.0 | 100.0 |
| avg_latency_ms | 1844.7 | 3153.2 | 2394.5 | 3199.4 |
| p95_latency_ms | 3249.5 | 8651.2 | 5362.7 | 7087.3 |
| avg_cost_usd | 0.004991 | 0.008288 | 0.005299 | 0.007421 |
| verifier_blocks | 0 | 2 | 0 | 3 |
| n | 45 | 45 | 45 | 45 |

## Version A vs Version B on restricted questions (paired, exact McNemar test)

| Test set / condition | n | only A leaked | only B leaked | p |
|---|---|---|---|---|
| dubai/normal | 6 | 0 | 0 | 1.0 |
| dubai/mistagged_all | 6 | 1 | 0 | 1.0 |

## Version A vs Version B on unanswerable questions (normal tagging, exact McNemar test)

| Test set | n | only B refused | only A refused | p |
|---|---|---|---|---|
| dubai | 13 | 0 | 0 | 1.0 |
