# Show, Don't Cite

**An answer engine whose claims come with runnable proofs of concept instead of links, and a test that tells real evidence from hollow evidence.**

Answer engines like Perplexity attach citations. A citation tells you that *someone said* something. It does not tell you the claim is true, still true, or true in the sense the answer uses it. For a large class of technical claims (about code, algorithms, numerics, probability, ML behaviour) we can do better: run something.

Here is a small example of why this matters. For years, `sum([0.1]*10) != 1.0` was the standard demonstration that Python's `sum()` is less accurate than `math.fsum()`. It is in countless tutorials and Stack Overflow answers. On Python 3.12 and later it no longer works, because `sum()` switched to compensated summation for floats. A citation-backed answer would repeat the old example. A PoC-backed answer runs it and finds out. This benchmark's own gold check for that claim (`c017`) failed on exactly this point while it was being written.

## The problem this project studies

Executable evidence has its own failure mode: **a proof of concept can run, pass, and prove nothing.** Language models are known to write tests that assert something trivially true. If an answer engine attaches such a PoC to a false claim, the reader now holds a false claim *with a green checkmark next to it*. That is worse than an unsupported claim.

So the core contribution is not "generate a PoC". It is a cheap, model-agnostic check that a PoC actually discriminates.

## The negation check

For every claim C, the system also states its negation ¬C. It asks the prover for a PoC for each, in **two independent calls**. The prover is never told which one is the original. Both PoCs run in a sandbox, and each must end by printing `RESULT: PASS` or `RESULT: FAIL`.

| | ¬C PoC passes | ¬C PoC fails |
|---|---|---|
| **C PoC passes** | **VACUOUS**: both "proven", so the evidence is hollow | **DEMONSTRATED** |
| **C PoC fails** | **REFUTED**: the claim is shown false | INCONCLUSIVE |

The prover can also answer `NOT_DEMONSTRABLE` (history, opinion, missing data). That gives **ABSTAIN**, an honest outcome rather than a failure.

This borrows the idea behind mutation testing in software engineering, where a test suite that cannot tell correct code from a mutant is worthless. Here it is moved from code to natural-language claims: the "mutant" is the negated claim.

## Results so far: harness validation

Before running real language models, the pipeline is validated with three synthetic provers on the seed benchmark (66 claims: 32 true, 30 false, 4 untestable).

| prover | what it does | false claims accepted, **single PoC** | false claims accepted, **negation-checked** | hollow PoCs caught by static lint |
|---|---|---|---|---|
| `oracle` | ships the hand-written gold check | 0% | 0% | n/a |
| `hollow-plain` | prints `RESULT: PASS` unconditionally | **100%** | **0%** | 100% |
| `hollow-disguised` | computes a statistic, then passes behind a condition that is always true | **100%** | **0%** | **0%** |

Read the last two rows together. A prover that always "proves" what it is asked gets every false claim accepted under the single-PoC baseline. A static check, the obvious first defence, catches the lazy version and is completely blind to the disguised one. The negation check catches both, without ever reading the code.

Reproduce:

```bash
python -m sdc run --prover hollow-disguised --out results/hollow-disguised.jsonl
python -m sdc report results/hollow-disguised.jsonl -o results/hollow-disguised.html
```

Reports for all three are in `results/`.

**Next: real language models.** Run the same benchmark with any OpenAI-compatible endpoint or a local Hugging Face model (see below). The open questions are empirical:

- **RQ1.** How often do LLM-written PoCs for *false* claims pass? That is the false-acceptance rate of "proof-attached" answers without the negation check.
- **RQ2.** How much of that does the negation check remove, and what does it cost in coverage (true claims that become VACUOUS or INCONCLUSIVE)?
- **RQ3.** Are vacuous PoCs mostly the lazy kind (static lint catches them) or the disguised kind (only behavioural checks catch them)? Does this change with model size?
- **RQ4.** Do models abstain on claims that cannot be tested by code, or do they produce confident pseudo-evidence for history and opinion?

## The benchmark

`data/claims_seed.jsonl`: 66 claims, each with a hand-written negation and a ground-truth label, across Python semantics, floating-point numerics, algorithms, probability, linear algebra, ML behaviour, and security (e.g. recovering Python's Mersenne Twister state from 624 outputs, or Base64 not being encryption).

**Every testable label is verified by execution**, not by assertion. `gold/gold_checks.py` holds an executable check per claim, and `tests/test_gold_labels.py` re-derives all 62 testable labels through the same sandbox that LLM PoCs go through. A label cannot drift from reality without a test failing.

Design rules for claims:
- Roughly half true and half false, so "always pass" cannot score well.
- Many false claims are *plausible* folk beliefs: "zero correlation implies independence", "standardising features changes OLS predictions", "greedy coin change is optimal".
- Negations are exact logical complements, not weaker or vaguer statements.
- Four untestable claims (history, opinion) measure whether the system knows when *not* to produce evidence.

Target for the full benchmark is about 300 claims. Contributions should follow the same format and must come with a gold check.

## Usage

```bash
pip install -r requirements.txt
python -m pytest -q                     # 80 tests, including label verification

# Any OpenAI-compatible endpoint (Groq, OpenRouter, Together, Ollama, vLLM, OpenAI, Gemini's OpenAI-compatible API, ...)
export SDC_API_BASE=https://api.groq.com/openai/v1
export SDC_API_KEY=...
export SDC_MODEL=<model name from your provider>
python -m sdc run --prover api --out results/my-model.jsonl
python -m sdc eval results/my-model.jsonl
python -m sdc report results/my-model.jsonl -o results/my-model.html

# Local model (e.g. Colab T4, 4-bit)
pip install transformers accelerate bitsandbytes
python -m sdc run --prover hf --model Qwen/Qwen2.5-Coder-7B-Instruct --out results/qwen7b.jsonl

# The answer-engine front end: question -> answer -> atomic claims -> negation-checked PoCs
python -m sdc ask "Is Python's sort stable, and does heapq give you a max-heap?" --report results/ask.html
```

`ask` prints the answer with an evidence verdict next to every claim, and warns if the answer contains a claim its own PoCs refuted.

`notebooks/colab_quickstart.ipynb` runs all of this on Colab.

## Repository layout

```
data/claims_seed.jsonl     benchmark: claim, negation, label, category
gold/gold_checks.py        one executable check per testable claim
sdc/prompts.py             polarity-blind PoC prompt; claim decomposition prompt
sdc/provers.py             LLM prover + oracle and two hollow provers (controls)
sdc/backends.py            OpenAI-compatible HTTP backend; Hugging Face backend
sdc/sandbox.py             separate process, timeout, memory/CPU limits
sdc/lint.py                static hollow-PoC detector (the baseline to beat)
sdc/verdict.py             the negation check
sdc/pipeline.py            claim -> 2 PoCs -> sandbox -> verdict (resumable JSONL)
sdc/evaluate.py            single-PoC vs negation-checked metrics
sdc/report.py              single-file HTML report
sdc/ask.py                 answer-engine mode
tests/                     unit tests + execution-based label verification
```

## Limitations

- **Scope.** This covers claims that can be tested by running code. Claims about history, law or medicine need citations or other evidence. The system is designed to say so (ABSTAIN) rather than fake it.
- **The negation check is necessary, not sufficient.** A prover could write a discriminating PoC that tests the *wrong* claim, e.g. a narrower case that happens to pass. Detecting claim–PoC misalignment, e.g. by having a second model judge whether the PoC tests the claim as worded, is the next step.
- **Empirical, not formal.** Most PoCs are experiments, not proofs. "Demonstrated" means "survived an honest test", the same standard as a well-designed experiment.
- **The sandbox is for reliability, not security.** Generated code runs as your user with resource limits. Run untrusted model output in a container or Colab.

## Related work

- **FactReview** (2026) audits ML papers by executing the authors' released code; removing execution evidence changed 17% of claim statuses. It re-runs existing artifacts. This project *generates* the experiment for open questions. [arXiv:2604.04074](https://arxiv.org/abs/2604.04074)
- **EG-VAR** (2026) attaches Lean-checked proofs to answers over tabular data and abstains otherwise. Formal, but limited to tables. [arXiv:2607.12650](https://arxiv.org/abs/2607.12650)
- **SWE-Mutation** (ACL Findings 2026) shows LLM-generated test suites rarely tell correct code from mutants. That is the same weakness, measured for code rather than claims. [arXiv:2605.22175](https://arxiv.org/abs/2605.22175)
- **Mutation-based specification validation** (IronSpec, Goldweber et al., 2024) checks that a formal specification rejects deliberately wrong variants. The negation check is the natural-language analogue.

## Author

Zubair, University of Malakand. Feedback and claim contributions are welcome via issues and pull requests.

## License

MIT
