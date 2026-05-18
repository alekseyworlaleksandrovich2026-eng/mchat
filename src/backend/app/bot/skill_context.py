"""Resolve skills and knowledge scope for a chat turn."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import CustomerConfig
from app.models.skill import Skill
from app.skill.utils import get_prompt_body, has_executable_script


def _ids_from_config(value: list[str] | None) -> list[str] | None:
    """None = use all; [] = use none; non-empty = filter to those ids."""
    if value is None:
        return None
    cleaned = [str(x).strip() for x in value if str(x).strip()]
    return cleaned


async def load_skills_for_chat(
    db: AsyncSession,
    user_id: str,
    customer_config: CustomerConfig | None = None,
) -> tuple[list[Skill], list[Skill]]:
    """Return (prompt_skills, executable_tool_skills) for this chat."""
    result = await db.execute(
        select(Skill).where(
            Skill.user_id == user_id,
            Skill.enabled == True,
        )
    )
    all_skills = list(result.scalars().all())

    allowed_ids = None
    if customer_config is not None:
        allowed_ids = _ids_from_config(
            getattr(customer_config, "skill_ids", None)
        )

    if allowed_ids is not None:
        if len(allowed_ids) == 0:
            return [], []
        allowed_set = set(allowed_ids)
        all_skills = [s for s in all_skills if s.id in allowed_set]

    prompt_skills: list[Skill] = []
    tool_skills: list[Skill] = []

    for skill in all_skills:
        skill_type = (skill.skill_type or "tool").lower()
        executable = has_executable_script(skill.path)

        if skill_type == "webhook":
            tool_skills.append(skill)
            continue

        if skill_type == "prompt" or (skill_type == "tool" and not executable):
            if get_prompt_body(skill):
                prompt_skills.append(skill)
            continue

        if skill_type in ("tool", "function") and executable:
            tool_skills.append(skill)

    return prompt_skills, tool_skills


# Keep system prompt lean — full SKILL.md can be 10k+ chars per skill.
_MAX_PROMPT_SKILL_CHARS = 1500

# Default OpenAI tool schemas for known skills (when SKILL.md has no parameters).
_DEFAULT_TOOL_PARAMETERS: dict[str, dict[str, Any]] = {
    "patent-search": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "enum": [
                    "search",
                    "detail",
                    "claims",
                    "description",
                    "legal",
                    "citing",
                    "similar",
                    "analysis",
                    "company",
                    "copyright",
                    "trademark",
                    "help",
                ],
                "description": "专利技能子命令，默认 search",
            },
            "query": {
                "type": "string",
                "description": "检索式/关键词（search、analysis、copyright 等）",
            },
            "patent_id": {
                "type": "string",
                "description": "专利公开号（detail、claims、legal 等）",
            },
            "company_name": {"type": "string", "description": "企业名称（company）"},
            "dimension": {
                "type": "string",
                "enum": [
                    "applicant",
                    "ipc",
                    "applicationYear",
                    "legalStatus",
                    "province",
                ],
                "description": "统计分析维度（command=analysis 时必填）",
            },
            "page": {"type": "integer", "description": "页码"},
            "page_size": {"type": "integer", "description": "每页条数"},
        },
        "required": ["command"],
    },
}


def _truncate_prompt_body(body: str) -> str:
    if len(body) <= _MAX_PROMPT_SKILL_CHARS:
        return body
    return (
        body[:_MAX_PROMPT_SKILL_CHARS]
        + "\n\n…（技能说明已截断，完整内容见技能文件）"
    )


_PATENT_LINK_PRESERVE_HINT = (
    "\n\n## Tool: patent-search\n"
    "- search（默认）: query + 可选 page, page_size, details, scope, sort\n"
    "- analysis: 必须同时传 command=analysis、query、dimension（applicant|ipc|"
    "applicationYear|legalStatus|province）\n"
    "- detail/claims/legal 等: 传 patent_id\n"
    "- company: 传 company_name\n"
    "统计分析/详情/企业画像等命令会一次性返回完整结果，不要再次调用 search 重复列表。\n"
    "仅 search 成功且表格已展示后：再写「初步观察」式自然语言总结（要点列表），"
    "勿重复表格、勿向用户展示 command=/page= 等技术参数。"
)


def append_patent_tool_hints(
    system_prompt: str, tool_skills: list[Skill]
) -> str:
    if any((s.name or "") == "patent-search" for s in tool_skills):
        return system_prompt + _PATENT_LINK_PRESERVE_HINT
    return system_prompt


def build_prompt_skill_section(prompt_skills: list[Skill]) -> str:
    if not prompt_skills:
        return ""
    parts: list[str] = []
    for skill in prompt_skills:
        desc = (skill.description or "").strip()
        body = get_prompt_body(skill)
        if body and body != desc:
            body = _truncate_prompt_body(body)
        elif desc:
            body = desc
        else:
            continue
        parts.append(f"### Skill: {skill.name}\n{body}")
    if not parts:
        return ""
    return "\n\n## Active Skills\n" + "\n\n".join(parts)


def build_openai_tools(tool_skills: list[Skill]) -> list[dict[str, Any]]:
    tools: list[dict[str, Any]] = []
    for skill in tool_skills:
        config = skill.config or {}
        parameters = config.get("parameters")
        if not parameters or parameters == {"type": "object", "properties": {}}:
            parameters = _DEFAULT_TOOL_PARAMETERS.get(
                skill.name,
                {"type": "object", "properties": {}},
            )
        desc = (skill.description or "").strip()
        if len(desc) > 500:
            desc = desc[:500] + "…"
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": skill.name,
                    "description": desc or f"Run skill {skill.name}",
                    "parameters": parameters,
                },
            }
        )
    return tools


def knowledge_base_ids_for_chat(
    customer_config: CustomerConfig | None,
) -> list[str] | None:
    if customer_config is None:
        return None
    return _ids_from_config(getattr(customer_config, "knowledge_base_ids", None))
