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

        usage_info = None
        async for chunk in stream:
            if hasattr(chunk, 'usage') and chunk.usage:
                usage_info = {
                    "prompt_tokens": getattr(chunk.usage, 'prompt_tokens', 0) or 0,
                    "completion_tokens": getattr(chunk.usage, 'completion_tokens', 0) or 0,
                    "total_tokens": getattr(chunk.usage, 'total_tokens', 0) or 0,
                }
                continue
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

        if usage_info:
            yield {"type": "usage", **usage_info}

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

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[dict[str, Any], None]:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
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
        system_prompt = None
        api_messages = []
        for m in messages:
            if m["role"] == "system":
                system_prompt = m["content"]
            else:
                api_messages.append({"role": m["role"], "content": m["content"]})

        anthropic_tools = None
        if tools:
            anthropic_tools = []
            for t in tools:
                func = t.get("function") or t
                anthropic_tools.append({
                    "name": func.get("name", ""),
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters") or {"type": "object", "properties": {}, "required": []},
                })

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": api_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

        try:
            tool_use_acc: dict[int, dict[str, Any]] = {}
            content_idx = 0

            async with self.client.messages.stream(**kwargs) as stream:
                async for event in stream:
                    if event.type == "content_block_start":
                        block = event.content_block
                        if block.type == "tool_use":
                            tool_use_acc[event.index] = {
                                "id": block.id,
                                "name": block.name,
                                "arguments": "",
                            }
                            content_idx = event.index
                    elif event.type == "content_block_delta":
                        delta = event.delta
                        if delta.type == "text_delta":
                            yield {"type": "content", "content": delta.text}
                        elif delta.type == "input_json_delta":
                            if event.index in tool_use_acc:
                                tool_use_acc[event.index]["arguments"] += delta.partial_json
                    elif event.type == "content_block_stop":
                        if event.index in tool_use_acc:
                            entry = tool_use_acc[event.index]
                            args_raw = entry["arguments"]
                            try:
                                arguments = json.loads(args_raw) if args_raw else {}
                            except json.JSONDecodeError:
                                arguments = {"raw": args_raw}
                            yield {
                                "type": "tool_call",
                                "tool_call": {
                                    "id": entry["id"],
                                    "name": entry["name"],
                                    "arguments": arguments,
                                },
                            }
                            del tool_use_acc[event.index]

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
        from google.genai import types

        system_instruction = None
        google_contents: list[Any] = []
        for m in messages:
            if m["role"] == "system":
                system_instruction = m["content"]
            else:
                role = "model" if m["role"] == "assistant" else m["role"]
                google_contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=m["content"])],
                    )
                )

        google_tools = None
        if tools:
            func_declarations = []
            for t in tools:
                func = t.get("function") or t
                params = func.get("parameters") or {"type": "object", "properties": {}}
                func_declarations.append(
                    types.FunctionDeclaration(
                        name=func.get("name", ""),
                        description=func.get("description", ""),
                        parameters=params,
                    )
                )
            google_tools = [types.Tool(function_declarations=func_declarations)]

        gen_config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_instruction,
            tools=google_tools,
        )

        try:
            accumulated_text = ""
            async for response in self.client.aio.models.generate_content_stream(
                model=self.model,
                contents=google_contents,
                config=gen_config,
            ):
                if response.candidates is None:
                    # Handle safety block or empty response
                    continue
                for candidate in response.candidates:
                    if candidate.content is None:
                        continue
                    for part in candidate.content.parts:
                        if part.text:
                            accumulated_text += part.text
                            yield {"type": "content", "content": part.text}
                        elif hasattr(part, "function_call") and part.function_call:
                            fc = part.function_call
                            args = {}
                            if fc.args:
                                args = dict(fc.args) if isinstance(fc.args, dict) else fc.args
                            yield {
                                "type": "tool_call",
                                "tool_call": {
                                    "id": fc.id or f"call_{fc.name}",
                                    "name": fc.name,
                                    "arguments": args,
                                },
                            }

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
