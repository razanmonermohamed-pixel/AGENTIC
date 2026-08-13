#!/usr/bin/env python3
"""
COSC726 - Agentic Artificial Intelligence
Week 2 / Lab 1 - llm_foundations.py
Completed student solution.
"""
from __future__ import annotations
import argparse
import math
import random
import sys
from dataclasses import dataclass, field

TOKENIZER_A = {
    "vocab": ["order", "agent", "the", "credit", "policy", "late", "1043",
              "ic", "ing", "ed", " ", "-", "A", "#"],
    "name": "teach-A",
}
TOKENIZER_B = {
    "vocab": ["order", "ag", "ent", "the", "cred", "it", "pol", "icy", "late",
              "10", "43", "ic", "ing", "ed", " ", "-", "A", "#"],
    "name": "teach-B",
}

def _greedy_split(text: str, vocab: list[str]) -> list[str]:
    vocab = sorted(vocab, key=len, reverse=True)
    text, out, i = text.lower(), [], 0
    while i < len(text):
        for v in vocab:
            if v and text.startswith(v.lower(), i):
                out.append(v); i += len(v); break
        else:
            out.append(text[i]); i += 1
    return out

def count_tokens(text: str, tokenizer: dict) -> int:
    """Return the number of tokens produced by the teaching tokenizer."""
    return len(_greedy_split(text, tokenizer["vocab"]))

@dataclass
class ContextPlan:
    kept: list[str] = field(default_factory=list)
    dropped: list[str] = field(default_factory=list)
    rejected: bool = False
    reason: str = ""

def prepare_context(messages: list[str], context_limit: int, reserved_output: int,
                    tokenizer: dict, strategy: str = "drop_oldest") -> ContextPlan:
    """Fit messages into context_limit-reserved_output using an explicit policy."""
    budget = context_limit - reserved_output
    total = lambda ms: sum(count_tokens(m, tokenizer) for m in ms)

    if budget < 0:
        return ContextPlan(rejected=True,
                           reason=f"reserved_output {reserved_output} exceeds context_limit {context_limit}")

    if strategy == "reject":
        input_tokens = total(messages)
        if input_tokens > budget:
            return ContextPlan(
                rejected=True,
                reason=f"input {input_tokens} > budget {budget}",
            )
        return ContextPlan(kept=list(messages))

    if strategy != "drop_oldest":
        raise ValueError(f"unknown context strategy: {strategy}")

    kept, dropped = list(messages), []
    while total(kept) > budget and len(kept) > 1:
        dropped.append(kept.pop(1))

    if total(kept) > budget:
        return ContextPlan(
            kept=kept,
            dropped=dropped,
            rejected=True,
            reason=f"system message requires {total(kept)} tokens > budget {budget}",
        )
    return ContextPlan(kept=kept, dropped=dropped)

def sample_next(distribution: dict[str, float], temperature: float,
                rng: random.Random) -> str:
    """Sample one token using greedy argmax or temperature-scaled probabilities."""
    if not distribution:
        raise ValueError("distribution must not be empty")

    if temperature <= 0:
        top = max(distribution.values())
        return sorted(k for k, v in distribution.items() if v == top)[0]

    positive = {k: v for k, v in distribution.items() if v > 0}
    if not positive:
        raise ValueError("distribution must contain at least one positive probability")

    scaled = {k: math.exp(math.log(v) / temperature) for k, v in positive.items()}
    z = sum(scaled.values())
    r, acc = rng.random(), 0.0
    for k in sorted(scaled):
        acc += scaled[k] / z
        if r <= acc:
            return k
    return sorted(scaled)[-1]

def _run_self_test() -> int:
    failures = []
    try:
        a = count_tokens("order A-1043", TOKENIZER_A)
        b = count_tokens("order A-1043", TOKENIZER_B)
        assert isinstance(a, int) and isinstance(b, int)
        assert a > 0 and b > 0
    except Exception as e:
        failures.append(f"count_tokens: {e}")
    try:
        msgs = ["system rules", "turn one", "turn two", "turn three about the credit"]
        rej = prepare_context(msgs, 8, 4, TOKENIZER_A, "reject")
        assert rej.rejected is True and rej.reason
        drop = prepare_context(msgs, 40, 4, TOKENIZER_A, "drop_oldest")
        assert drop.kept and drop.kept[0] == "system rules"
    except Exception as e:
        failures.append(f"prepare_context: {e}")
    try:
        dist = {"Paris": 0.82, "London": 0.11, "Lyon": 0.05, "Rome": 0.02}
        picks = {sample_next(dist, 0.0, random.Random(s)) for s in range(5)}
        assert picks == {"Paris"}
        hot = sample_next(dist, 1.0, random.Random(1))
        assert hot in dist
    except Exception as e:
        failures.append(f"sample_next: {e}")
    if failures:
        print("SELF-TEST FAILURES:")
        for f in failures: print("  -", f)
        return 1
    print("ALL SELF-TESTS PASSED")
    return 0

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="COSC726 Week 2 lab - LLM foundations")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _run_self_test()
    print("Nothing to run. Implement the three TODOs, then: --self-test")
    return 0

if __name__ == "__main__":
    sys.exit(main())
