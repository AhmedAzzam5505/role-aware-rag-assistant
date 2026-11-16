# Evaluation results (2026-11-16, mode=offline, corpus=dubai)

Rates in brackets are 95% Wilson confidence intervals.

## Test set: dubai (45 questions)

| Metric | normal/A | normal/B | mistagged/A | mistagged/B | mistagged_all/A | mistagged_all/B | mistagged_all_bad_register/A | mistagged_all_bad_register/B |
|---|---|---|---|---|---|---|---|---|
| accuracy_% | 42.3 | 11.5 | 42.3 | 11.5 | 42.3 | 11.5 | 42.3 | 11.5 |
| accuracy_95ci | 42.3% [25.5, 61.1] | 11.5% [4.0, 29.0] | 42.3% [25.5, 61.1] | 11.5% [4.0, 29.0] | 42.3% [25.5, 61.1] | 11.5% [4.0, 29.0] | 42.3% [25.5, 61.1] | 11.5% [4.0, 29.0] |
| faithfulness_proxy_% | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| leak_rate_restricted_% | 66.7 | 0.0 | 66.7 | 0.0 | 100.0 | 0.0 | 100.0 | 0.0 |
| leak_rate_95ci | 66.7% [30.0, 90.3] | 0.0% [0.0, 39.0] | 66.7% [30.0, 90.3] | 0.0% [0.0, 39.0] | 100.0% [61.0, 100.0] | 0.0% [0.0, 39.0] | 100.0% [61.0, 100.0] | 0.0% [0.0, 39.0] |
| leaks_all_questions | 34 | 0 | 34 | 0 | 36 | 0 | 36 | 0 |
| over_refusal_% | 3.8 | 84.6 | 3.8 | 84.6 | 3.8 | 84.6 | 3.8 | 84.6 |
| unanswerable_refused_% | 7.7 | 100.0 | 7.7 | 100.0 | 7.7 | 100.0 | 7.7 | 100.0 |
| avg_latency_ms | 17.5 | 18.9 | 18.5 | 20.1 | 21.5 | 18.5 | 17.9 | 20.2 |
| p95_latency_ms | 18.7 | 23.7 | 19.6 | 24.3 | 38.5 | 22.5 | 19.1 | 24.9 |
| avg_cost_usd | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| verifier_blocks | 0 | 36 | 0 | 36 | 0 | 36 | 0 | 36 |
| n | 45 | 45 | 45 | 45 | 45 | 45 | 45 | 45 |

## Version A vs Version B on restricted questions (paired, exact McNemar test)

| Test set / condition | n | only A leaked | only B leaked | p |
|---|---|---|---|---|
| dubai/normal | 6 | 4 | 0 | 0.125 |
| dubai/mistagged | 6 | 4 | 0 | 0.125 |
| dubai/mistagged_all | 6 | 6 | 0 | 0.0312 |
| dubai/mistagged_all_bad_register | 6 | 6 | 0 | 0.0312 |

## Version A vs Version B on unanswerable questions (normal tagging, exact McNemar test)

| Test set | n | only B refused | only A refused | p |
|---|---|---|---|---|
| dubai | 13 | 12 | 0 | 0.0005 |
