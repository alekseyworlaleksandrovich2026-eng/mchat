"""Skill executor - execute skill tool functions in a sandboxed environment."""

from __future__ import annotations

import importlib.util
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from loguru import logger

from app.models.skill import Skill


_SKIP_CONFIG_ENV_KEYS = frozenset({"secrets", "env", "prompt_body", "parameters"})


@contextmanager
def _skill_secrets_env(skill: Skill) -> Iterator[None]:
    """Inject skill secrets and scalar config options into process env."""
    config = skill.config or {}
    secrets = config.get("secrets") or config.get("env") or {}
    if not isinstance(secrets, dict):
        secrets = {}

    prefix = f"MCHAT_SKILL_{skill.name.upper().replace('-', '_')}_"
    previous: dict[str, str | None] = {}
    injected: list[str] = []

    def _set_env(env_key: str, value: Any) -> None:
        if value is None or str(value).strip() == "":
            return
        env_key = str(env_key).strip()
        if env_key not in previous:
            previous[env_key] = os.environ.get(env_key)
            injected.append(env_key)
        os.environ[env_key] = str(value)

    try:
        for key, value in secrets.items():
            env_key = str(key).strip()
            _set_env(f"{prefix}{env_key}", value)
            _set_env(env_key, value)

        for key, value in config.items():
            if key in _SKIP_CONFIG_ENV_KEYS:
                continue
            if isinstance(value, (dict, list)):
                continue
            _set_env(str(key), value)
            _set_env(f"{prefix}{str(key).upper()}", value)

        yield
    finally:
        for key in injected:
            old = previous.get(key)
            if old is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old


async def execute_skill(skill: Skill, args: dict[str, Any]) -> Any:
    """Execute a skill tool function.

    Supports:
    - Python script in the skill directory
    - Shell commands defined in skill config
    - Webhook calls
    """
    skill_type = skill.skill_type

    try:
        if skill_type == "tool":
            return await _execute_python_tool(skill, args)
        elif skill_type == "function":
            return await _execute_python_tool(skill, args)
        elif skill_type == "webhook":
            return await _execute_webhook(skill, args)
        else:
            return {"error": f"Unknown skill type: {skill_type}"}
    except SystemExit as e:
        logger.error(f"Skill '{skill.name}' called sys.exit({e.code})")
        return {
            "error": (
                f"技能 '{skill.name}' 执行异常退出"
                f"{f' (code {e.code})' if e.code else ''}。"
                "请检查技能参数与 API Key 配置。"
            )
        }
    except BaseException as e:
        logger.error(f"Skill '{skill.name}' execution error: {e}")
        return {"error": str(e)}


async def _execute_python_tool(
    skill: Skill, args: dict[str, Any]
) -> Any:
    """Execute a Python-based skill tool."""
    if not skill.path:
        return {"error": "No path defined for skill"}

    skill_path = Path(skill.path)
    skill_dir = skill_path.parent

    # Look for main.py or tool.py in the skill directory
    script_path = skill_dir / "main.py"
    if not script_path.exists():
        script_path = skill_dir / "tool.py"

    if not script_path.exists():
        return {"error": f"No script found in {skill_dir}"}

    try:
        with _skill_secrets_env(skill):
            spec = importlib.util.spec_from_file_location(
                f"skill_{skill.name}", script_path
            )
            if spec is None or spec.loader is None:
                return {"error": f"Failed to load skill module: {skill.name}"}

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "main"):
                result = module.main(**args)
                return _normalize_tool_result(result)
            if hasattr(module, "run"):
                result = module.run(**args)
                return _normalize_tool_result(result)
            return {"error": "No main() or run() function found in skill script"}

    except SystemExit as e:
        logger.error(f"Python tool '{skill.name}' sys.exit({e.code})")
        return {
            "error": (
                "技能脚本异常退出，请勿在工具模式使用 argparse/sys.exit。"
                "请在技能管理中配置 API Key（secrets）。"
            )
        }
    except BaseException as e:
        logger.error(f"Python tool execution failed: {e}")
        return {"error": str(e)}


def _normalize_tool_result(result: Any) -> Any:
    """Ensure tool output is JSON-serializable for the LLM."""
    if result is None:
        return {"ok": True, "message": "技能执行完成（无返回内容）"}
    if isinstance(result, (str, int, float, bool, dict, list)):
        return result
    return str(result)


async def _execute_webhook(
    skill: Skill, args: dict[str, Any]
) -> Any:
    """Execute a webhook-based skill."""
    import httpx

    config = skill.config or {}
    webhook_url = config.get("url", "")

    if not webhook_url:
        return {"error": "No webhook URL configured"}

    headers = {"Content-Type": "application/json"}
    config_secrets = (skill.config or {}).get("secrets") or {}
    if isinstance(config_secrets, dict):
        api_key = config_secrets.get("API_KEY") or config_secrets.get("api_key")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

    try:
        with _skill_secrets_env(skill):
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    webhook_url,
                    json=args,
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()
    except Exception as e:
        logger.error(f"Webhook skill '{skill.name}' failed: {e}")
        return {"error": str(e)}
