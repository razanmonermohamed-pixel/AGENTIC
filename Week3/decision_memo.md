# Decision Memo — COSC726 Lab 2

## 1. What exactly changed between runs?
- **A → B:** Added an explicit role, scope, checkable constraints, and a strict JSON output contract.
- **B → C:** Kept B unchanged and added three invented few-shot examples targeting null abstention, compound requests without an order ID, and the rare `other` enum.
- **C → D:** Returned to B and added named intermediate reasoning fields for delay counting, policy clause, threshold check, and approval basis; the intermediate fields are consumed internally and are not part of the final contract.
- **D → E:** Kept B's wording unchanged and enforced `K.SCHEMA` at decoding time. This changes the decoder rather than the prompt.

## 2. Which dimension moved, and by how much?

| Technique | Parse | Schema | Fields | False-fill | Safe | Tokens/call | Latency |
|---|---:|---:|---:|---:|---|---:|---:|
| A-naive | 17% | 17% | 100% | 0% | FAIL | 192 | 420 ms |
| B-system | 100% | 67% | 85% | 17% | FAIL | 352 | 500 ms |
| C-fewshot | 100% | 92% | 92% | 8% | OK | 612 | 610 ms |
| D-reasoning | 100% | 100% | 96% | 8% | OK | 462 | 1850 ms |
| E-constrained | 100% | 100% | 96% | 8% | OK | 357 | 540 ms |


The largest improvement is from A to B on parseability: the output contract removes prose/fence failures. Few-shot examples reduce the remaining behavioural faults, while D adds substantial latency and completion cost without improving the final rubric enough to justify it. E closes syntax/schema failures through constrained decoding, but it cannot solve referential truth.

## 3. Which technique would I ship, and at what cost per call?
I would ship **E — schema-constrained**, subject to the external validation gates. It preserves the concise B specification while enforcing the output shape at generation time. Its measured cost is the E row above: about the reported token count per call and 540 ms simulated latency. The important point is that E is not considered safe merely because the schema is valid; Gate 3 and Gate 4 remain mandatory.

## 4. Which failure remains, and which gate catches it?
The persistent failure is the fabricated-but-shape-valid order ID in **E11**. The model can emit `A1102`, which matches `^A[0-9]{4}$`, but the order does not exist in `KNOWN_ORDER_IDS`. **Gate 3 (referential integrity)** catches it. This cannot be fixed by prompt wording or JSON Schema alone; it requires a lookup/tool/database check.

## 5. What would make me revert this choice?
I would revert or add a human-review fallback if a real-model evaluation showed any safety violation, materially worse abstention/false-fill behaviour, unacceptable latency or token cost, or systematic failures on new languages/domains. I would also revert if constrained decoding caused incompatibility with required downstream tooling.

## 6. What did the measurement NOT tell me?
These results are measurements of a deterministic **published fault model**, not a real LLM. The evaluation has only 12 hand-written fixtures, one author, no inter-annotator agreement, and only one Arabic case, so it cannot establish multilingual robustness. The fixtures also do not estimate production prevalence. The simulator's exact defect probabilities and costs are artificial. Finally, the rubric cannot prove that the prompt generalizes to unseen customers, new policies, adversarial attacks, or distribution shift. A production claim would require a larger independently annotated test set, real-model runs with a pinned model snapshot, and monitoring of safety and gate failures.

## Week 4 takeaways
- Input that breaks the best prompt: **E11**, because a syntactically valid ID can still be nonexistent.
- Rule that cannot be guaranteed by prompt alone: **referential existence**; it needs a database/tool lookup, permissions, or human review.
