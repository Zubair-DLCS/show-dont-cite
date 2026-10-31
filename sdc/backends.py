"""Chat-model backends. Anything that can turn (system, user) into text."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request


class ChatBackend:
    name = "base"

    def complete(self, system: str, user: str) -> str:  # pragma: no cover
        raise NotImplementedError


class OpenAICompatibleBackend(ChatBackend):
    """Any /chat/completions endpoint: Groq, OpenRouter, Together, vLLM, Ollama,
    Gemini's OpenAI-compatible endpoint, OpenAI itself.

    Configure with env vars SDC_API_BASE, SDC_API_KEY, SDC_MODEL, or arguments.
    """

    def __init__(self, model: str | None = None, api_base: str | None = None,
                 api_key: str | None = None, temperature: float = 0.2,
                 max_tokens: int = 2048, max_retries: int = 6):
        self.model = model or os.environ.get("SDC_MODEL")
        self.api_base = (api_base or os.environ.get("SDC_API_BASE", "")).rstrip("/")
        self.api_key = api_key or os.environ.get("SDC_API_KEY", "")
        if not self.model or not self.api_base:
            raise ValueError("Set SDC_MODEL and SDC_API_BASE (and SDC_API_KEY if the "
                             "endpoint needs one), or pass --model/--api-base.")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.name = f"api:{self.model}"

    def complete(self, system: str, user: str) -> str:
        body = json.dumps({
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
        }).encode()
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        delay = 2.0
        for attempt in range(self.max_retries):
            req = urllib.request.Request(f"{self.api_base}/chat/completions",
                                         data=body, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=180) as resp:
                    data = json.loads(resp.read().decode())
                return data["choices"][0]["message"]["content"] or ""
            except urllib.error.HTTPError as exc:
                if exc.code in (429, 500, 502, 503, 504) and attempt < self.max_retries - 1:
                    time.sleep(delay)
                    delay *= 2
                    continue
                detail = exc.read().decode(errors="replace")[:500]
                raise RuntimeError(f"HTTP {exc.code} from {self.api_base}: {detail}") from exc
            except urllib.error.URLError:
                if attempt < self.max_retries - 1:
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise
        raise RuntimeError("unreachable")


class TransformersBackend(ChatBackend):
    """Local Hugging Face model, e.g. on a Colab T4:
    Qwen/Qwen2.5-Coder-7B-Instruct with load_in_4bit=True."""

    def __init__(self, model: str, load_in_4bit: bool = True,
                 max_new_tokens: int = 1536, temperature: float = 0.2):
        import torch  # noqa: F401  (imported here so the package works without it)
        from transformers import AutoModelForCausalLM, AutoTokenizer
        kwargs = {"device_map": "auto", "torch_dtype": "auto"}
        if load_in_4bit:
            from transformers import BitsAndBytesConfig
            kwargs["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True)
        self.tok = AutoTokenizer.from_pretrained(model)
        self.model = AutoModelForCausalLM.from_pretrained(model, **kwargs)
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.name = f"hf:{model}"

    def complete(self, system: str, user: str) -> str:
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        ids = self.tok.apply_chat_template(msgs, add_generation_prompt=True,
                                           return_tensors="pt").to(self.model.device)
        out = self.model.generate(ids, max_new_tokens=self.max_new_tokens,
                                  do_sample=self.temperature > 0,
                                  temperature=max(self.temperature, 1e-5),
                                  pad_token_id=self.tok.eos_token_id)
        return self.tok.decode(out[0, ids.shape[1]:], skip_special_tokens=True)
