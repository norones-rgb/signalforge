from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class LLMClient(Protocol):
    def generate(self, prompt: str, max_chars: int) -> str:
        ...


def _find_shared_dir() -> Path:
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        candidate = parent / "shared"
        if candidate.exists() and candidate.is_dir():
            return candidate
    raise FileNotFoundError("shared directory not found")


def load_prompt(name: str) -> str:
    shared_dir = _find_shared_dir()
    prompt_path = shared_dir / "prompts" / name
    return prompt_path.read_text(encoding="utf-8")


def render_prompt(template: str, **kwargs: str) -> str:
    return template.format(**kwargs)


@dataclass
class DummyLLM:
    seed: str = "signalforge"

    def generate(self, prompt: str, max_chars: int) -> str:
        digest = hashlib.sha256((self.seed + prompt).encode("utf-8")).hexdigest()
        body = (
            "SignalForge draft: "
            "A concise, original insight derived from sources. "
            f"Ref {digest[:24]}."
        )
        return body[:max_chars].strip()


class OpenAIClientLLM:
    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini") -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

    def generate(self, prompt: str, max_chars: int) -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("openai package not installed") from exc

        client = OpenAI(api_key=self.api_key)
        response = client.responses.create(
            model=self.model,
            input=prompt,
            max_output_tokens=256,
        )
        text = response.output_text or ""
        return text[:max_chars].strip()


def get_llm() -> LLMClient:
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIClientLLM()
    return DummyLLM()
