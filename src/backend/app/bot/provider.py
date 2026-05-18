"""LLM Provider factory and provider implementations."""

import json
from collections.abc import AsyncGenerator
from typing import Any

from loguru import logger

from app.bot.dsml_parser import contains_dsml, parse_dsml_tool_calls, strip_dsml_blocks
from app.models.ai_config import AIConfig


def _delta_reasoning_content(delta: Any) -> str | None:
    """DeepSeek thinking mode returns chain-of-thought on the delta."""
    if delta is None:
        return None
    rc = getattr(delta, "reasoning_content", None)
    if rc:
        return str(rc)
    model_extra = getattr(delta, "model_extra", None)
    if isinstance(model_extra, dict) and model_extra.get("reasoning_content"):
        return str(model_extra["reasoning_content"])
    if hasattr(delta, "model_dump"):
        try:
            dumped = delta.model_dump()
            if dumped.get("reasoning_content"):
                return str(dumped["reasoning_content"])
        except Exception:
            pass
    return None


def _message_reasoning_content(message: Any) -> str | None:
    """Read reasoning_content from a completed chat message."""
    if message is None:
        return None
    rc = getattr(message, "reasoning_content", None)
    if rc:
        return str(rc)
    extra = getattr(message, "model_extra", None)
    if isinstance(extra, dict) and extra.get("reasoning_content"):
        return str(extra["reasoning_content"])
    if hasattr(message, "model_dump"):
        try:
            dumped = message.model_dump()
            if dumped.get("reasoning_content"):
                return str(dumped["reasoning_content"])
        except Exception:
            pass
    return None


def _is_deepseek_thinking_api(client: Any, model: str) -> bool:
    """DeepSeek V3.2+ thinking mode requires reasoning_content on tool turns."""
    base = str(getattr(client, "base_url", "") or "").lower()
    if "deepseek" in base:
        return True
    m = (model or "").lower()
    return m.startswith("deepseek") or "reasoner" in m


def _chunk_reasoning_content(chunk: Any) -> str | None:
    """Fallback: read reasoning_content from raw chunk JSON."""
    if not hasattr(chunk, "model_dump"):
        return None
    try:
        data = chunk.model_dump()
        choices = data.get("choices") or []
        if not choices:
            return None
        delta = choices[0].get("delta") or {}
        rc = delta.get("reasoning_content")
        return str(rc) if rc else None
    except Exception:
        return None


class LLMProvider:
    """Base class for LLM providers."""

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream chat completion. Yields dicts with 'type' key.

        Types:
        - content: {"type": "content", "content": "..."}
        - tool_call: {"type": "tool_call", "tool_call": {...}}
        - done: {"type": "done"}
        """
        if False:  # pragma: no cover
            yield  # Make this an async generator

    async def _parse_stream_chunks(
        self, stream: Any
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Parse streaming chunks from an OpenAI-compatible API."""
        tool_acc: dict[int, dict[str, Any]] = {}
        content_buffer = ""
        dsml_mode = False

        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta is None:
                continue

            reasoning = _delta_reasoning_content(delta) or _chunk_reasoning_content(
                chunk
            )
            if reasoning:
                yield {"type": "reasoning", "content": reasoning}

            if delta.content:
                content_buffer += delta.content
                if contains_dsml(content_buffer):
                    dsml_mode = True
                if not dsml_mode:
                    yield {"type": "content", "content": delta.content}

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index if tc.index is not None else 0
                    if idx not in tool_acc:
                        tool_acc[idx] = {
                            "id": "",
                            "name": "",
                            "arguments": "",
                        }
                    if tc.id:
                        tool_acc[idx]["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            tool_acc[idx]["name"] = tc.function.name
                        if tc.function.arguments:
                            tool_acc[idx]["arguments"] += tc.function.arguments

        for idx in sorted(tool_acc.keys()):
            entry = tool_acc[idx]
            args_raw = entry.get("arguments") or ""
            if args_raw:
                try:
                    arguments = json.loads(args_raw)
                except json.JSONDecodeError:
                    arguments = {"raw": args_raw}
            else:
                arguments = {}
            call_id = entry.get("id") or f"call_{idx}"
            yield {
                "type": "tool_call",
                "tool_call": {
                    "id": call_id,
                    "name": entry.get("name") or "",
                    "arguments": arguments,
                },
            }

        if not tool_acc and content_buffer:
            for call in parse_dsml_tool_calls(content_buffer):
                yield {"type": "tool_call", "tool_call": call}

        yield {"type": "done"}


class OpenAIProvider(LLMProvider):
    """OpenAI-compatible provider."""

    def __init__(self, ai_config: AIConfig) -> None:
        from openai import AsyncOpenAI

        client_kwargs = {"api_key": ai_config.api_key}
        if ai_config.api_base:
            client_kwargs["base_url"] = ai_config.api_base

        self.client = AsyncOpenAI(**client_kwargs)
        self.model = ai_config.model
        self._deepseek_thinking = _is_deepseek_thinking_api(self.client, self.model)

    async def _stream_tool_round_non_streaming(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Non-stream completion so reasoning_content is available for tool calls."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
        msg = response.choices[0].message
        reasoning = _message_reasoning_content(msg)
        if reasoning:
            yield {"type": "reasoning", "content": reasoning}

        content = msg.content or ""
        native_calls = list(msg.tool_calls or [])
        dsml_calls = parse_dsml_tool_calls(content) if not native_calls else []

        display = strip_dsml_blocks(content) if dsml_calls else content
        if display and display.strip():
            yield {"type": "content", "content": display}

        if native_calls:
            for tc in native_calls:
                args_raw = tc.function.arguments if tc.function else ""
                try:
                    arguments = json.loads(args_raw) if args_raw else {}
                except json.JSONDecodeError:
                    arguments = {"raw": args_raw}
                yield {
                    "type": "tool_call",
                    "tool_call": {
                        "id": tc.id or "",
                        "name": (tc.function.name if tc.function else "") or "",
                        "arguments": arguments,
                    },
                }
        else:
            for call in dsml_calls:
                yield {"type": "tool_call", "tool_call": call}

        yield {"type": "done"}

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[dict[str, Any], None]:
        if tools and self._deepseek_thinking:
            try:
                async for chunk in self._stream_tool_round_non_streaming(
                    messages, tools, temperature, max_tokens
                ):
                    yield chunk
                return
            except Exception as e:
                logger.warning(
                    f"DeepSeek non-stream tool round failed, falling back to stream: {e}"
                )

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            "stream_options": {"include_usage": False},
        }
        if tools:
            kwargs["tools"] = tools

        try:
            stream = await self.client.chat.completions.create(**kwargs)
            async for chunk in self._parse_stream_chunks(stream):
                yield chunk
        except Exception as e:
            logger.error(f"OpenAI provider error: {e}")
            yield {"type": "content", "content": f"Error: {e}"}
            yield {"type": "done"}


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, ai_config: AIConfig) -> None:
        from anthropic import AsyncAnthropic

        client_kwargs = {"api_key": ai_config.api_key}
        self.client = AsyncAnthropic(**client_kwargs)
        self.model = ai_config.model

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[dict[str, Any], None]:
        # Anthropic expects system as separate parameter
        system_prompt = None
        api_messages = []
        for m in messages:
            if m["role"] == "system":
                system_prompt = m["content"]
            else:
                api_messages.append(m)

        kwargs = {
            "model": self.model,
            "messages": api_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        try:
            async with self.client.messages.stream(**kwargs) as stream:
                async for text in stream.text_stream:
                    yield {"type": "content", "content": text}

            yield {"type": "done"}
        except Exception as e:
            logger.error(f"Anthropic provider error: {e}")
            yield {"type": "content", "content": f"Error: {e}"}
            yield {"type": "done"}


class GoogleProvider(LLMProvider):
    """Google Generative AI (Gemini) provider."""

    def __init__(self, ai_config: AIConfig) -> None:
        from google import genai

        self.client = genai.Client(api_key=ai_config.api_key)
        self.model = ai_config.model

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[dict[str, Any], None]:
        # Convert openai-style messages to Gemini format
        system_instruction = None
        google_messages = []
        for m in messages:
            if m["role"] == "system":
                system_instruction = m["content"]
            else:
                role = "model" if m["role"] == "assistant" else m["role"]
                google_messages.append({
                    "role": role,
                    "parts": [{"text": m["content"]}],
                })

        try:
            gen_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }

            contents = google_messages if google_messages else None

            if contents:
                response = self.client.models.generate_content_stream(
                    model=self.model,
                    contents=contents,
                    config=gen_config,
                )
            else:
                response = self.client.models.generate_content_stream(
                    model=self.model,
                    contents="Hello",
                    config=gen_config,
                )

            for chunk in response:
                if chunk.text:
                    yield {"type": "content", "content": chunk.text}

            yield {"type": "done"}
        except Exception as e:
            logger.error(f"Google provider error: {e}")
            yield {"type": "content", "content": f"Error: {e}"}
            yield {"type": "done"}


class OllamaProvider(OpenAIProvider):
    """Ollama local model provider (OpenAI-compatible API)."""

    def __init__(self, ai_config: AIConfig) -> None:
        from openai import AsyncOpenAI

        base_url = ai_config.api_base or "http://localhost:11434/v1"
        self.client = AsyncOpenAI(
            api_key=ai_config.api_key or "ollama",
            base_url=base_url,
        )
        self.model = ai_config.model


class GroqProvider(OpenAIProvider):
    """Groq cloud provider (OpenAI-compatible API, ultra-fast inference)."""

    def __init__(self, ai_config: AIConfig) -> None:
        from openai import AsyncOpenAI

        base_url = ai_config.api_base or "https://api.groq.com/openai/v1"
        self.client = AsyncOpenAI(
            api_key=ai_config.api_key,
            base_url=base_url,
        )
        self.model = ai_config.model


class OpenAICompatibleProvider(OpenAIProvider):
    """Generic OpenAI-compatible provider for custom endpoints."""

    def __init__(self, ai_config: AIConfig) -> None:
        from openai import AsyncOpenAI

        if not ai_config.api_base:
            raise ValueError("api_base is required for openai-compatible provider")

        self.client = AsyncOpenAI(
            api_key=ai_config.api_key or "not-needed",
            base_url=ai_config.api_base,
        )
        self.model = ai_config.model


def _resolve_model_id(ai_config: AIConfig) -> str:
    """Map deprecated provider model ids to current ones."""
    if ai_config.provider == "deepseek":
        aliases = {
            "deepseek-chat": "deepseek-v4-flash",
            "deepseek-reasoner": "deepseek-v4-pro",
        }
        return aliases.get(ai_config.model, ai_config.model)
    return ai_config.model


def create_provider(ai_config: AIConfig) -> LLMProvider:
    """Factory: create the appropriate LLM provider based on config."""
    provider_map: dict[str, type[LLMProvider]] = {
        "openai": OpenAIProvider,
        "deepseek": OpenAIProvider,  # DeepSeek uses OpenAI-compatible API
        "ollama": OllamaProvider,
        "groq": GroqProvider,
        "anthropic": AnthropicProvider,
        "google": GoogleProvider,
        # Generic / compatible providers
        "openai-compatible": OpenAICompatibleProvider,
        "zhipu": OpenAICompatibleProvider,  # Zhipu GLM uses OpenAI-compatible API
        "moonshot": OpenAICompatibleProvider,  # Moonshot/Kimi uses OpenAI-compatible API
        "siliconflow": OpenAICompatibleProvider,  # SiliconFlow uses OpenAI-compatible API
        "together": OpenAICompatibleProvider,  # Together AI uses OpenAI-compatible API
    }

    provider_class = provider_map.get(ai_config.provider)
    if provider_class is None:
        raise ValueError(
            f"Unsupported provider: {ai_config.provider}. "
            f"Supported: {list(provider_map.keys())}"
        )

    resolved_model = _resolve_model_id(ai_config)
    if resolved_model != ai_config.model:
        logger.info(
            f"Model alias: {ai_config.model} -> {resolved_model} "
            f"({ai_config.provider})"
        )
        ai_config.model = resolved_model

    logger.info(
        f"Creating provider: {ai_config.provider} with model {ai_config.model}"
    )
    return provider_class(ai_config)
