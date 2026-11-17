# Evaluation results (2026-11-16, mode=offline)

Rates in brackets are 95% Wilson confidence intervals.

## Test set: tuning (45 questions)

| Metric | normal/A | normal/B | mistagged/A | mistagged/B | mistagged_all/A | mistagged_all/B | mistagged_all_bad_register/A | mistagged_all_bad_register/B |
|---|---|---|---|---|---|---|---|---|
| accuracy_% | 92.6 | 92.6 | 92.6 | 92.6 | 92.6 | 92.6 | 92.6 | 92.6 |
| accuracy_95ci | 92.6% [76.6, 97.9] | 92.6% [76.6, 97.9] | 92.6% [76.6, 97.9] | 92.6% [76.6, 97.9] | 92.6% [76.6, 97.9] | 92.6% [76.6, 97.9] | 92.6% [76.6, 97.9] | 92.6% [76.6, 97.9] |
| faithfulness_proxy_% | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| leak_rate_restricted_% | 0.0 | 0.0 | 22.2 | 0.0 | 100.0 | 0.0 | 100.0 | 0.0 |
| leak_rate_95ci | 0.0% [0.0, 29.9] | 0.0% [0.0, 29.9] | 22.2% [6.3, 54.7] | 0.0% [0.0, 29.9] | 100.0% [70.1, 100.0] | 0.0% [0.0, 29.9] | 100.0% [70.1, 100.0] | 0.0% [0.0, 29.9] |
| leaks_all_questions | 0 | 0 | 2 | 0 | 9 | 0 | 9 | 0 |
| over_refusal_% | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| unanswerable_refused_% | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| avg_latency_ms | 1.0 | 0.9 | 0.9 | 0.8 | 0.8 | 0.8 | 0.8 | 0.8 |
| p95_latency_ms | 1.4 | 1.1 | 1.0 | 0.9 | 0.9 | 1.0 | 0.9 | 0.9 |
| avg_cost_usd | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| verifier_blocks | 0 | 0 | 0 | 2 | 0 | 9 | 0 | 9 |
| n | 45 | 45 | 45 | 45 | 45 | 45 | 45 | 45 |

## Test set: holdout (45 questions)

| Metric | normal/A | normal/B | mistagged/A | mistagged/B | mistagged_all/A | mistagged_all/B | mistagged_all_bad_register/A | mistagged_all_bad_register/B |
|---|---|---|---|---|---|---|---|---|
| accuracy_% | 76.0 | 76.0 | 76.0 | 76.0 | 76.0 | 76.0 | 76.0 | 76.0 |
| accuracy_95ci | 76.0% [56.6, 88.5] | 76.0% [56.6, 88.5] | 76.0% [56.6, 88.5] | 76.0% [56.6, 88.5] | 76.0% [56.6, 88.5] | 76.0% [56.6, 88.5] | 76.0% [56.6, 88.5] | 76.0% [56.6, 88.5] |
| faithfulness_proxy_% | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| leak_rate_restricted_% | 0.0 | 0.0 | 18.2 | 0.0 | 100.0 | 0.0 | 100.0 | 9.1 |
| leak_rate_95ci | 0.0% [0.0, 25.9] | 0.0% [0.0, 25.9] | 18.2% [5.1, 47.7] | 0.0% [0.0, 25.9] | 100.0% [74.1, 100.0] | 0.0% [0.0, 25.9] | 100.0% [74.1, 100.0] | 9.1% [1.6, 37.7] |
| leaks_all_questions | 0 | 0 | 2 | 0 | 11 | 0 | 11 | 1 |
| over_refusal_% | 8.0 | 8.0 | 8.0 | 8.0 | 8.0 | 8.0 | 8.0 | 8.0 |
| unanswerable_refused_% | 55.6 | 55.6 | 55.6 | 55.6 | 55.6 | 55.6 | 55.6 | 55.6 |
| avg_latency_ms | 0.9 | 0.9 | 0.8 | 0.8 | 0.8 | 0.8 | 0.8 | 0.8 |
| p95_latency_ms | 1.0 | 1.1 | 0.9 | 1.0 | 1.0 | 0.9 | 0.8 | 1.0 |
| avg_cost_usd | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| verifier_blocks | 0 | 0 | 0 | 1 | 0 | 9 | 0 | 8 |
| n | 45 | 45 | 45 | 45 | 45 | 45 | 45 | 45 |

## Version A vs Version B on restricted questions (paired, exact McNemar test)

| Test set / condition | n | only A leaked | only B leaked | p |
|---|---|---|---|---|
| tuning/normal | 9 | 0 | 0 | 1.0 |
| holdout/normal | 11 | 0 | 0 | 1.0 |
| tuning/mistagged | 9 | 2 | 0 | 0.5 |
| holdout/mistagged | 11 | 2 | 0 | 0.5 |
| tuning/mistagged_all | 9 | 9 | 0 | 0.0039 |
| holdout/mistagged_all | 11 | 11 | 0 | 0.001 |
| tuning/mistagged_all_bad_register | 9 | 9 | 0 | 0.0039 |
| holdout/mistagged_all_bad_register | 11 | 10 | 0 | 0.002 |
