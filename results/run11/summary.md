# Evaluation results (2026-11-16, mode=offline, corpus=dubai)

Rates in brackets are 95% Wilson confidence intervals.

## Test set: dubai (45 questions)

| Metric | normal/A | normal/B | mistagged/A | mistagged/B | mistagged_all/A | mistagged_all/B | mistagged_all_bad_register/A | mistagged_all_bad_register/B |
|---|---|---|---|---|---|---|---|---|
| accuracy_% | 42.3 | 46.2 | 42.3 | 46.2 | 42.3 | 46.2 | 42.3 | 46.2 |
| accuracy_95ci | 42.3% [25.5, 61.1] | 46.2% [28.8, 64.5] | 42.3% [25.5, 61.1] | 46.2% [28.8, 64.5] | 42.3% [25.5, 61.1] | 46.2% [28.8, 64.5] | 42.3% [25.5, 61.1] | 46.2% [28.8, 64.5] |
| faithfulness_proxy_% | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| leak_rate_restricted_% | 0.0 | 0.0 | 0.0 | 0.0 | 83.3 | 0.0 | 83.3 | 0.0 |
| leak_rate_95ci | 0.0% [0.0, 39.0] | 0.0% [0.0, 39.0] | 0.0% [0.0, 39.0] | 0.0% [0.0, 39.0] | 83.3% [43.6, 97.0] | 0.0% [0.0, 39.0] | 83.3% [43.6, 97.0] | 0.0% [0.0, 39.0] |
| leaks_all_questions | 0 | 0 | 0 | 0 | 5 | 0 | 5 | 0 |
| over_refusal_% | 3.8 | 23.1 | 3.8 | 23.1 | 3.8 | 23.1 | 3.8 | 23.1 |
| unanswerable_refused_% | 7.7 | 69.2 | 7.7 | 69.2 | 7.7 | 69.2 | 7.7 | 69.2 |
| avg_latency_ms | 17.3 | 58.6 | 17.3 | 57.1 | 16.5 | 55.7 | 17.6 | 57.8 |
| p95_latency_ms | 18.0 | 118.9 | 17.9 | 119.6 | 17.1 | 116.7 | 18.9 | 122.5 |
| avg_cost_usd | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| verifier_blocks | 0 | 16 | 0 | 16 | 0 | 16 | 0 | 16 |
| n | 45 | 45 | 45 | 45 | 45 | 45 | 45 | 45 |

## Version A vs Version B on restricted questions (paired, exact McNemar test)

| Test set / condition | n | only A leaked | only B leaked | p |
|---|---|---|---|---|
| dubai/normal | 6 | 0 | 0 | 1.0 |
| dubai/mistagged | 6 | 0 | 0 | 1.0 |
| dubai/mistagged_all | 6 | 5 | 0 | 0.0625 |
| dubai/mistagged_all_bad_register | 6 | 5 | 0 | 0.0625 |

## Version A vs Version B on unanswerable questions (normal tagging, exact McNemar test)

| Test set | n | only B refused | only A refused | p |
|---|---|---|---|---|
| dubai | 13 | 8 | 0 | 0.0078 |
