"""Heuristic model capabilities for chat UI (attachments, vision)."""

from __future__ import annotations

from pydantic import BaseModel


class ModelCapabilities(BaseModel):
    supports_attachments: bool = True
    supports_vision: bool = False


_NO_ATTACHMENT_PATTERNS = (
    "o1-preview",
    "o1-mini",
    "o1-pro",
)

_NO_VISION_PATTERNS = (
    "reasoner",
    "r1-distill",
    "-r1",
    "text-davinci",
    "instruct",
)

_VISION_PATTERNS = (
    "gpt-4o",
    "gpt-4-turbo",
    "gpt-4-vision",
    "gpt-4.1",
    "vision",
    "-vl",
    "qvq",
    "gemini",
    "claude-3",
    "claude-sonnet",
    "claude-opus",
    "claude-haiku",
    "deepseek-v4",
    "qwen-vl",
    "qwen2-vl",
    "glm-4v",
)


def model_capabilities(provider: str, model: str) -> ModelCapabilities:
    """Infer chat attachment / vision support from provider + model id."""
    p = (provider or "").lower()
    m = (model or "").lower()
    combined = f"{p}/{m}"

    supports_attachments = not any(x in m or x in combined for x in _NO_ATTACHMENT_PATTERNS)

    supports_vision = any(x in m or x in combined for x in _VISION_PATTERNS) and not any(
        x in m for x in _NO_VISION_PATTERNS
    )

    # OpenAI multimodal families
    if p == "openai" and m.startswith("gpt-4"):
        supports_vision = supports_vision or "mini" in m or "o" in m or "turbo" in m

    # Anthropic / Google chat models generally support images
    if p in ("anthropic", "google"):
        supports_vision = True

    # Ollama / local: allow files; vision only when model name suggests it
    if p == "ollama":
        supports_vision = any(x in m for x in ("vision", "vl", "llava", "moondream"))

    return ModelCapabilities(
        supports_attachments=supports_attachments,
        supports_vision=supports_vision,
    )
