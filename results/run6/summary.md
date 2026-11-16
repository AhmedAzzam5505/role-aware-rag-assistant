# Evaluation results (2026-11-16, mode=offline, corpus=real)

Rates in brackets are 95% Wilson confidence intervals.

## Test set: real (45 questions)

| Metric | normal/A | normal/B | mistagged/A | mistagged/B | mistagged_all/A | mistagged_all/B | mistagged_all_bad_register/A | mistagged_all_bad_register/B |
|---|---|---|---|---|---|---|---|---|
| accuracy_% | 78.6 | 71.4 | 78.6 | 71.4 | 78.6 | 71.4 | 75.0 | 67.9 |
| accuracy_95ci | 78.6% [60.5, 89.8] | 71.4% [52.9, 84.7] | 78.6% [60.5, 89.8] | 71.4% [52.9, 84.7] | 78.6% [60.5, 89.8] | 71.4% [52.9, 84.7] | 75.0% [56.6, 87.3] | 67.9% [49.3, 82.1] |
| faithfulness_proxy_% | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| leak_rate_restricted_% | 0.0 | 0.0 | 0.0 | 0.0 | 87.5 | 0.0 | 62.5 | 0.0 |
| leak_rate_95ci | 0.0% [0.0, 32.4] | 0.0% [0.0, 32.4] | 0.0% [0.0, 32.4] | 0.0% [0.0, 32.4] | 87.5% [52.9, 97.8] | 0.0% [0.0, 32.4] | 62.5% [30.6, 86.3] | 0.0% [0.0, 32.4] |
| leaks_all_questions | 0 | 0 | 0 | 0 | 7 | 0 | 5 | 0 |
| over_refusal_% | 0.0 | 17.9 | 0.0 | 17.9 | 0.0 | 17.9 | 3.6 | 21.4 |
| unanswerable_refused_% | 22.2 | 44.4 | 22.2 | 44.4 | 22.2 | 44.4 | 22.2 | 44.4 |
| avg_latency_ms | 4.5 | 4.8 | 4.7 | 4.7 | 4.6 | 5.1 | 4.6 | 4.8 |
| p95_latency_ms | 5.0 | 5.8 | 5.0 | 5.4 | 5.0 | 6.1 | 5.0 | 5.5 |
| avg_cost_usd | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| verifier_blocks | 0 | 10 | 0 | 10 | 0 | 13 | 0 | 11 |
| n | 45 | 45 | 45 | 45 | 45 | 45 | 45 | 45 |

## Version A vs Version B on restricted questions (paired, exact McNemar test)

| Test set / condition | n | only A leaked | only B leaked | p |
|---|---|---|---|---|
| real/normal | 8 | 0 | 0 | 1.0 |
| real/mistagged | 8 | 0 | 0 | 1.0 |
| real/mistagged_all | 8 | 7 | 0 | 0.0156 |
| real/mistagged_all_bad_register | 8 | 5 | 0 | 0.0625 |

## Version A vs Version B on unanswerable questions (normal tagging, exact McNemar test)

| Test set | n | only B refused | only A refused | p |
|---|---|---|---|---|
| real | 9 | 2 | 0 | 0.5 |
