# Evaluation results (2026-11-16, mode=offline, corpus=real)

Rates in brackets are 95% Wilson confidence intervals.

## Test set: real (45 questions)

| Metric | normal/A | normal/B | mistagged/A | mistagged/B | mistagged_all/A | mistagged_all/B | mistagged_all_bad_register/A | mistagged_all_bad_register/B |
|---|---|---|---|---|---|---|---|---|
| accuracy_% | 78.6 | 78.6 | 78.6 | 78.6 | 78.6 | 78.6 | 78.6 | 78.6 |
| accuracy_95ci | 78.6% [60.5, 89.8] | 78.6% [60.5, 89.8] | 78.6% [60.5, 89.8] | 78.6% [60.5, 89.8] | 78.6% [60.5, 89.8] | 78.6% [60.5, 89.8] | 78.6% [60.5, 89.8] | 78.6% [60.5, 89.8] |
| faithfulness_proxy_% | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| leak_rate_restricted_% | 0.0 | 0.0 | 12.5 | 0.0 | 100.0 | 0.0 | 100.0 | 0.0 |
| leak_rate_95ci | 0.0% [0.0, 32.4] | 0.0% [0.0, 32.4] | 12.5% [2.2, 47.1] | 0.0% [0.0, 32.4] | 100.0% [67.6, 100.0] | 0.0% [0.0, 32.4] | 100.0% [67.6, 100.0] | 0.0% [0.0, 32.4] |
| leaks_all_questions | 0 | 0 | 1 | 0 | 8 | 0 | 8 | 0 |
| over_refusal_% | 0.0 | 3.6 | 0.0 | 3.6 | 0.0 | 3.6 | 0.0 | 3.6 |
| unanswerable_refused_% | 22.2 | 55.6 | 22.2 | 55.6 | 22.2 | 55.6 | 22.2 | 55.6 |
| avg_latency_ms | 5.1 | 7.4 | 5.1 | 7.5 | 5.2 | 8.3 | 5.6 | 8.5 |
| p95_latency_ms | 5.3 | 11.7 | 5.2 | 11.5 | 5.5 | 12.5 | 6.5 | 12.5 |
| avg_cost_usd | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| verifier_blocks | 0 | 7 | 0 | 8 | 0 | 11 | 0 | 11 |
| n | 45 | 45 | 45 | 45 | 45 | 45 | 45 | 45 |

## Test set: real2 (45 questions)

| Metric | normal/A | normal/B | mistagged/A | mistagged/B | mistagged_all/A | mistagged_all/B | mistagged_all_bad_register/A | mistagged_all_bad_register/B |
|---|---|---|---|---|---|---|---|---|
| accuracy_% | 55.0 | 50.0 | 55.0 | 50.0 | 55.0 | 50.0 | 55.0 | 50.0 |
| accuracy_95ci | 55.0% [34.2, 74.2] | 50.0% [29.9, 70.1] | 55.0% [34.2, 74.2] | 50.0% [29.9, 70.1] | 55.0% [34.2, 74.2] | 50.0% [29.9, 70.1] | 55.0% [34.2, 74.2] | 50.0% [29.9, 70.1] |
| faithfulness_proxy_% | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| leak_rate_restricted_% | 0.0 | 0.0 | 20.0 | 0.0 | 80.0 | 0.0 | 80.0 | 0.0 |
| leak_rate_95ci | 0.0% [0.0, 43.4] | 0.0% [0.0, 43.4] | 20.0% [3.6, 62.4] | 0.0% [0.0, 43.4] | 80.0% [37.6, 96.4] | 0.0% [0.0, 43.4] | 80.0% [37.6, 96.4] | 0.0% [0.0, 43.4] |
| leaks_all_questions | 0 | 0 | 1 | 0 | 4 | 0 | 4 | 0 |
| over_refusal_% | 0.0 | 20.0 | 0.0 | 20.0 | 0.0 | 20.0 | 0.0 | 20.0 |
| unanswerable_refused_% | 10.0 | 90.0 | 10.0 | 90.0 | 10.0 | 90.0 | 10.0 | 90.0 |
| avg_latency_ms | 5.1 | 8.7 | 5.1 | 8.7 | 6.1 | 8.9 | 5.2 | 10.1 |
| p95_latency_ms | 5.2 | 13.7 | 5.2 | 13.5 | 6.8 | 13.9 | 5.4 | 15.2 |
| avg_cost_usd | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| verifier_blocks | 0 | 24 | 0 | 24 | 0 | 25 | 0 | 25 |
| n | 45 | 45 | 45 | 45 | 45 | 45 | 45 | 45 |

## Version A vs Version B on restricted questions (paired, exact McNemar test)

| Test set / condition | n | only A leaked | only B leaked | p |
|---|---|---|---|---|
| real/normal | 8 | 0 | 0 | 1.0 |
| real2/normal | 5 | 0 | 0 | 1.0 |
| real/mistagged | 8 | 1 | 0 | 1.0 |
| real2/mistagged | 5 | 1 | 0 | 1.0 |
| real/mistagged_all | 8 | 8 | 0 | 0.0078 |
| real2/mistagged_all | 5 | 4 | 0 | 0.125 |
| real/mistagged_all_bad_register | 8 | 8 | 0 | 0.0078 |
| real2/mistagged_all_bad_register | 5 | 4 | 0 | 0.125 |

## Version A vs Version B on unanswerable questions (normal tagging, exact McNemar test)

| Test set | n | only B refused | only A refused | p |
|---|---|---|---|---|
| real | 9 | 3 | 0 | 0.25 |
| real2 | 20 | 16 | 0 | 0.0 |
