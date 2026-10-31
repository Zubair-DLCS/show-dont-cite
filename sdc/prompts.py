"""Prompts. The PoC prompt is deliberately polarity-blind: the model sees one
statement and never learns whether it is the original claim or its negation,
and the two PoCs are generated in separate, independent calls."""

POC_SYSTEM = (
    "You are a careful empirical scientist and Python programmer. You test "
    "statements by writing small, honest experiments. You never hard-code a "
    "conclusion; the printed result must depend on what the code computes."
)

POC_PROMPT = """Statement: "{statement}"

Write ONE self-contained Python 3 script that tests whether this statement, exactly as worded, is true.

Rules:
- Use only the Python standard library and numpy.
- No network access, no reading user input, no files outside the current directory.
- It must finish in under {timeout} seconds on an ordinary laptop CPU.
- Seed any randomness so the result is reproducible.
- Compute the evidence. The conclusion must depend on computed values, never be hard-coded.
- Before concluding, print the key numbers your conclusion rests on.
- The LAST line printed must be exactly `RESULT: PASS` if your evidence shows the statement is true, or `RESULT: FAIL` if your evidence shows it is false.

If the statement cannot be tested by running code (for example it is about history, a matter of opinion, or needs data you cannot generate), reply with exactly one line and nothing else:
NOT_DEMONSTRABLE: <short reason>

Otherwise reply with only the script, inside a single ```python code block."""

DECOMPOSE_SYSTEM = (
    "You answer technical questions precisely and then break your answer into "
    "atomic, independently checkable claims."
)

DECOMPOSE_PROMPT = """Question: {question}

1. Answer the question in at most 150 words.
2. Then list every distinct factual claim your answer relies on, as atomic statements. For each, also write its precise logical negation (the statement that is true exactly when the claim is false; not merely a weaker or vaguer claim).

Reply in this exact JSON format and nothing else:
{{"answer": "...", "claims": [{{"claim": "...", "negation": "..."}}, ...]}}"""
