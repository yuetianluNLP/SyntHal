# SyntHal

Dataset for **Relational Linearity is a Predictor of Hallucinations**, accepted to the **EMNLP 2026 main conference**.

SyntHal contains **3,000 English prompts across 15 relations**, with 200 prompt records per relation. The subjects are synthetic names designed to create likely knowledge gaps. In the benchmark's synthetic setting, refusal is the intended response and a committed object value is counted as a hallucination. Synthetic construction does not prove that every name was absent from every model's training data.

## Get the data

- **[SyntHal prompts (JSONL)](data/00_dataset_SyntHal/SyntHal_prompts.jsonl)**
- [Raw JSONL download](https://raw.githubusercontent.com/yuetianluNLP/SyntHal/main/data/00_dataset_SyntHal/SyntHal_prompts.jsonl)
- [Relation inventory and templates](docs/relation_inventory.csv)
- [Data index](data/DATA_INDEX.md)

```bash
git clone https://github.com/yuetianluNLP/SyntHal.git
cd SyntHal
python3 scripts/validate_dataset.py
```

Read the dataset with Python's standard library:

```python
import json
from pathlib import Path

path = Path('data/00_dataset_SyntHal/SyntHal_prompts.jsonl')
with path.open(encoding='utf-8') as f:
    examples = [json.loads(line) for line in f if line.strip()]

print(len(examples))  # 3000
print(examples[0]['prompt'])  # Who is the CEO of Ludisi Systems?
```

## Record format

Each line is one JSON object. Each record has six fields:

| Field | Meaning |
|---|---|
| `dataset` | Dataset name, `SyntHal` |
| `relation_key` | Relation identifier, such as `company_ceo` |
| `subject` | Synthetic subject string |
| `template` | Question template with one `{}` placeholder |
| `prompt` | Template rendered with the subject |
| `example_id` | Record ID, such as `company_ceo__0000` |

The synthetic prompts have no gold object answers. Do not use the gold objects in the separate natural-LRE analysis tables as answers for SyntHal prompts.

## Accompanying analyses

The accompanying aggregate tables report the ARR submission results for Figure 1 (SyntHal hallucination), Figure 2 (natural-output plausibility), natural answered-case accuracy, and gold-object concentration controls.

For natural-LRE tables, a response labeled `Hallucination` means a committed non-gold response under the released evaluation protocol. A gold mismatch is not necessarily a verified factual falsehood. Likewise, a plausible relation filler need not be correct for the queried subject.

## Terms

The supplied [License and Terms](data/LICENSE_AND_TERMS.md) are preserved unchanged. They describe research and review use; this release does not add an MIT, Creative Commons, or other permissive license. Third-party resources remain subject to their original licenses and terms.

## Citation

Please cite the paper when using SyntHal:

```bibtex
@misc{lu2026relational,
  title = {Relational Linearity is a Predictor of Hallucinations},
  author = {Lu, Yuetian and Liu, Yihong and Gerstner, Sebastian and Hirlimann, Lea and Rohweder, Jonas and Sch{\"u}tze, Hinrich},
  year = {2026},
  note = {Accepted to the EMNLP 2026 main conference}
}
```

Proceedings identifiers can be added when the final bibliographic record is available.
