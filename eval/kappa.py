"""Inter-rater agreement for the human ratings (Cohen's kappa, per rubric item).

Each rater fills in a copy of eval/rating_sheet_template.csv. Then:
    python -m eval.kappa ratings_rater1.csv ratings_rater2.csv
"""
import csv
import sys
from collections import Counter

ITEMS = ["correctness", "faithfulness", "leak", "refusal_ok"]


def cohen_kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(a) | set(b)) / (n * n)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def main(f1, f2):
    r1 = {r["id"] + r["version"]: r for r in csv.DictReader(open(f1))}
    r2 = {r["id"] + r["version"]: r for r in csv.DictReader(open(f2))}
    keys = sorted(set(r1) & set(r2))
    for item in ITEMS:
        a = [r1[k][item] for k in keys if r1[k][item] != "" and r2[k][item] != ""]
        b = [r2[k][item] for k in keys if r1[k][item] != "" and r2[k][item] != ""]
        if a:
            print(f"{item:13s} n={len(a):3d}  agreement={sum(x == y for x, y in zip(a, b)) / len(a):.2f}  "
                  f"kappa={cohen_kappa(a, b):.2f}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
