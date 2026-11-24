# Evaluation results (2026-11-24, mode=offline, corpus=mock)

Rates in brackets are 95% Wilson confidence intervals.

## Test set: holdout2 (45 questions)

| Metric | normal/A | normal/B | mistagged_all/A | mistagged_all/B |
|---|---|---|---|---|
| accuracy_% | 77.3 | 68.2 | 72.7 | 72.7 |
| accuracy_95ci | 77.3% [56.6, 89.9] | 68.2% [47.3, 83.6] | 72.7% [51.8, 86.8] | 72.7% [51.8, 86.8] |
| faithfulness_proxy_% | 98.8 | 100.0 | 92.1 | 94.1 |
| leak_rate_restricted_% | 0.0 | 0.0 | 50.0 | 0.0 |
| leak_rate_95ci | 0.0% [0.0, 32.4] | 0.0% [0.0, 32.4] | 50.0% [21.5, 78.5] | 0.0% [0.0, 32.4] |
| leaks_all_questions | 0 | 0 | 4 | 0 |
| over_refusal_% | 22.7 | 27.3 | 22.7 | 22.7 |
| unanswerable_refused_% | 100.0 | 100.0 | 100.0 | 100.0 |
| avg_latency_ms | 1564.1 | 2472.2 | 1925.5 | 2970.0 |
| p95_latency_ms | 2883.2 | 4244.7 | 3776.1 | 5419.8 |
| avg_cost_usd | 0.002789 | 0.004036 | 0.003608 | 0.005537 |
| verifier_blocks | 0 | 1 | 0 | 3 |
| n | 45 | 45 | 45 | 45 |

## Version A vs Version B on restricted questions (paired, exact McNemar test)

| Test set / condition | n | only A leaked | only B leaked | p |
|---|---|---|---|---|
| holdout2/normal | 8 | 0 | 0 | 1.0 |
| holdout2/mistagged_all | 8 | 4 | 0 | 0.125 |

## Version A vs Version B on unanswerable questions (normal tagging, exact McNemar test)

| Test set | n | only B refused | only A refused | p |
|---|---|---|---|---|
| holdout2 | 15 | 0 | 0 | 1.0 |
