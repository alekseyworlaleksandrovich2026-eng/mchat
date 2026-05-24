"""Bot engine - core message processing pipeline with streaming."""

from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any
import uuid

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.messages import (
    build_assistant_tool_call_message,
    build_tool_result_message,
    sanitize_history_messages,
)
from app.utils.chat_upload import attachment_prompt_text
from app.bot.provider import create_provider
from app.bot.patent_links import linkify_patent_ids, patent_link_settings_from_skills
from app.bot.skill_context import (
    append_patent_tool_hints,
    build_openai_tools,
    build_prompt_skill_section,
    knowledge_base_ids_for_chat,
    load_skills_for_chat,
)
from app.knowledge.rag import RagService
from app.models.ai_config import AIConfig
from app.models.conversation import Conversation
from app.models.customer import CustomerConfig
from app.models.message import Message
from app.models.skill import Skill
from app.utils.outbound_assets import enrich_message_extra_data
from app.bot.auto_reply_rules import (
    build_auto_reply_note,
    detect_message_channel,
    match_auto_reply_rules,
)

_PATENT_SEARCH_PRESENTATION_NUDGE = (
    "（用户看不到本条消息。）\n"
    "请根据上一条 patent-search 工具返回的结果，用中文给用户写完整回复，"
    "严格按以下结构（不要省略任何部分）：\n\n"
    "1. 第一行：🔍 搜索完成\n"
    "2. 第二行：📊 找到 {总条数} 条专利（总条数取自工具结果）\n"
    "3. 空一行\n"
    "4. 制表符分隔表格（不要用 Markdown 管道表格），表头："
    "序号\\t专利号\\t标题\\t申请人\\t申请日\n"
    "   逐行展示工具结果中的专利；申请日从工具数据提取，格式 YYYY-MM-DD；"
    "若无申请日则留空\n"
    "5. 空一行\n"
    "6. 一行：📄 当前仅展示前 {本页条数} 条，共 {总条数} 条匹配。\n"
    "7. 小标题「初步观察」，接着 4–6 条要点（列表），概括申请人类型、"
    "代表性机构、技术方向、总量\n"
    "8. 结尾用自然语言列出可继续的操作：统计分析、翻页、查看详情/权利要求/"
    "法律状态、企业专利画像等\n"
    "不要输出工具原文 emoji 列表，不要写 command= / page= 等技术参数。"
)
_PATENT_SEARCH_OBSERVATION_NUDGE = (
    "（专利检索结果表格已在上方展示给用户，用户看不到本条消息。）\n"
    "请用中文写一段回复，以小标题「初步观察」开头，接着用 4–6 条要点（列表即可）概括："
    "主要申请人类型（企业/高校/外资等）、代表性机构、技术方向、以及总申请量说明；"
    "不要重复表格、不要罗列专利号、不要写 command= / page= 等技术参数。\n"
    "最后用 1–2 句自然语言说明：如需某条详情、权利要求、法律状态，"
    "或按公司、IPC、时间范围精确筛选，让用户直接告诉你即可。"
)
_ENABLE_PATENT_SEARCH_PRESENTATION = True
_ENABLE_PATENT_SEARCH_SUMMARY = False
_HISTORY_MESSAGE_LIMIT = 60


def _is_patent_search_success(
    tool_name: str, command: str, tool_display: str
) -> bool:
    return (
        tool_name == "patent-search"
        and command == "search"
        and "🔍 搜索完成" in tool_display
        and not tool_display.lstrip().startswith("❌")
    )


def _tool_result_display_text(result: Any) -> str:
    """Text to stream to the user from a tool result (preserves markdown links)."""
    if isinstance(result, str) and result.strip():
        return result.strip() + "\n\n"
    if isinstance(result, dict):
        err = result.get("error")
        if err:
            return f"❌ {err}\n\n"
        for key in ("message", "content", "text"):
            val = result.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip() + "\n\n"
    return ""


def _merge_tool_call(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    if incoming.get("id"):
        merged["id"] = incoming["id"]
    if incoming.get("name"):
        merged["name"] = incoming["name"]
    if incoming.get("arguments"):
        prev = merged.get("arguments") or {}
        if isinstance(prev, dict) and isinstance(incoming["arguments"], dict):
            merged["arguments"] = {**prev, **incoming["arguments"]}
        else:
            merged["arguments"] = incoming["arguments"]
    return merged


async def _append_rag_context(
    system_prompt: str,
    query: str,
    user_id: str,
    customer_config: CustomerConfig | None,
    chat_fn=None,
) -> tuple[str, list[dict[str, Any]]]:
    kb_ids = knowledge_base_ids_for_chat(customer_config)
    rag = RagService()
    all_results = []

    try:
        if kb_ids:
            for kb_id in kb_ids:
                search_results = await rag.search(
                    query=query,
                    user_id=user_id,
                    knowledge_base_id=kb_id,
                    top_k=3,
                    chat_fn=chat_fn,
                )
                all_results.extend(search_results.results)
        else:
            search_results = await rag.search(
                query=query,
                user_id=user_id,
                top_k=3,
                chat_fn=chat_fn,
            )
            all_results.extend(search_results.results)
    except Exception as e:
        logger.warning(f"RAG search failed: {e}")
        return system_prompt, []

    if not all_results:
        return system_prompt, []

    seen: set[str] = set()
    context_parts: list[str] = []
    hit_items: list[dict[str, Any]] = []
    for r in all_results:
        key = f"{r.document_id}:{r.content[:80]}"
        if key in seen:
            continue
        seen.add(key)
        context_parts.append(f"[Source: {r.title}]\n{r.content}")
        hit_items.append(
            {
                "document_id": r.document_id,
                "title": r.title,
                "knowledge_base_id": r.knowledge_base_id,
                "score": round(float(r.score), 4),
            }
        )

    if not context_parts:
        return system_prompt, []

    return (
        system_prompt
        + "\n\n## Knowledge Base Context\n"
        "Use the following information to help answer the user's question:\n\n"
        + "\n\n".join(context_parts)
    ), hit_items


async def process_message(
    conversation: Conversation,
    message: Message,
    ai_config: AIConfig | None,
    db_session: AsyncSession,
    customer_config: CustomerConfig | None = None,
    skill_ids_override: list[str] | None = None,
) -> AsyncGenerator[str, None]:
    """Process a user message through the bot pipeline."""
    try:
        if ai_config is None:
            result = await db_session.execute(
                select(AIConfig).where(AIConfig.is_default == True)
            )
            ai_config = result.scalar_one_or_none()

        if ai_config is None:
            yield "Error: No AI configuration available. Please configure an AI provider first."
            return

        system_prompt = ai_config.system_prompt or "You are a helpful AI assistant."

        prompt_skills, tool_skills = await load_skills_for_chat(
            db_session,
            user_id=ai_config.user_id,
            customer_config=customer_config,
            skill_ids_override=skill_ids_override,
        )
        skill_section = build_prompt_skill_section(prompt_skills)
        if skill_section:
            system_prompt += skill_section

        tools = build_openai_tools(tool_skills)
        system_prompt = append_patent_tool_hints(system_prompt, tool_skills)
        patent_links = patent_link_settings_from_skills(tool_skills)

        def _with_patent_links(text: str) -> str:
            return linkify_patent_ids(
                text,
                enabled=patent_links["enabled"],
                template=str(patent_links["template"]),
            )

        # Create chat_fn for optional query rewriting
        _chat_fn = None
        try:
            from app.bot.query_rewrite_chat import create_rewrite_chat_fn
            _chat_fn = await create_rewrite_chat_fn(ai_config)
        except Exception:
            pass

        system_prompt, knowledge_hits = await _append_rag_context(
            system_prompt,
            message.content,
            ai_config.user_id,
            customer_config,
            chat_fn=_chat_fn,
        )

        auto_reply_matches = await match_auto_reply_rules(
            message.content,
            getattr(customer_config, "auto_reply_rules", None),
            channel=detect_message_channel(getattr(conversation, "contact_info", None)),
        )

        messages_list: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]

        history_result = await db_session.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(_HISTORY_MESSAGE_LIMIT)
        )
        history = list(reversed(history_result.scalars().all()))

        history_payload = []
        for hist_msg in history:
            if hist_msg.id == message.id:
                continue
            history_payload.append(
                {
                    "role": hist_msg.role,
                    "content": hist_msg.content,
                    "extra_data": hist_msg.extra_data,
                }
            )
        messages_list.extend(sanitize_history_messages(history_payload))
        messages_list.append(
            {
                "role": "user",
                "content": attachment_prompt_text(
                    message.content, message.extra_data
                ),
            }
        )

        provider = create_provider(ai_config)
        full_response = ""
        reasoning_content = ""
        tool_calls_map: dict[str, dict[str, Any]] = {}
        first_pass_content = ""

        async for chunk in provider.stream_chat(
            messages=messages_list,
            tools=tools if tools else None,
            temperature=ai_config.temperature,
            max_tokens=ai_config.max_tokens,
        ):
            if chunk.get("type") == "reasoning":
                reasoning_content += chunk.get("content", "") or ""
            elif chunk.get("type") == "content":
                token = chunk.get("content", "")
                if token and not token.startswith("Error:"):
                    first_pass_content += token
                    yield token
            elif chunk.get("type") == "tool_call":
                tc = chunk.get("tool_call", {})
                tid = tc.get("id") or f"call_{uuid.uuid4().hex[:8]}"
                if tid in tool_calls_map:
                    tool_calls_map[tid] = _merge_tool_call(tool_calls_map[tid], tc)
                else:
                    tool_calls_map[tid] = {
                        "id": tid,
                        "name": tc.get("name", ""),
                        "arguments": tc.get("arguments") or {},
                    }

        tool_calls_list = list(tool_calls_map.values())

        if not tool_calls_list and first_pass_content:
            full_response += first_pass_content

        if tool_calls_list:
            messages_list.append(
                build_assistant_tool_call_message(
                    full_response,
                    tool_calls_list,
                    reasoning_content=reasoning_content or None,
                )
            )

            patent_search_for_summary = False
            patent_search_for_presentation = False
            for tc in tool_calls_list:
                tool_name = tc.get("name", "")
                tool_args = dict(tc.get("arguments") or {})
                if tool_name == "patent-search":
                    cmd = str(tool_args.get("command") or "search").lower()
                    if cmd == "search" and tool_args.get("details") is None:
                        tool_args["details"] = True
                try:
                    tool_result = await _execute_tool(
                        tool_name,
                        tool_args,
                        tool_skills,
                        db_session,
                    )
                except BaseException as e:
                    logger.error(f"Tool execution crashed: {e}", exc_info=True)
                    tool_result = {
                        "error": f"技能执行失败: {e}。请检查 API Key 与参数。"
                    }
                messages_list.append(
                    build_tool_result_message(tc["id"], tool_result)
                )

                tool_display = _tool_result_display_text(tool_result)
                if tool_display:
                    tool_display = _with_patent_links(tool_display)
                    cmd = str(tool_args.get("command") or "search").lower()
                    patent_search_ok = _is_patent_search_success(
                        tool_name, cmd, tool_display
                    )
                    if _ENABLE_PATENT_SEARCH_PRESENTATION and patent_search_ok:
                        patent_search_for_presentation = True
                    else:
                        full_response += tool_display
                        yield tool_display
                    if (
                        _ENABLE_PATENT_SEARCH_SUMMARY
                        and patent_search_ok
                    ):
                        patent_search_for_summary = True

            if patent_search_for_presentation:
                messages_list.append(
                    {"role": "user", "content": _PATENT_SEARCH_PRESENTATION_NUDGE}
                )
                presentation_parts: list[str] = []
                async for chunk in provider.stream_chat(
                    messages=messages_list,
                    tools=None,
                    temperature=ai_config.temperature,
                    max_tokens=ai_config.max_tokens,
                ):
                    if chunk.get("type") == "content":
                        token = chunk.get("content", "")
                        if token.startswith("Error:"):
                            presentation_parts.append(f"\n\n{token}")
                        elif token:
                            presentation_parts.append(token)
                            yield token
                if presentation_parts:
                    presentation_text = _with_patent_links(
                        "".join(presentation_parts)
                    )
                    if not presentation_text.endswith("\n\n"):
                        presentation_text = presentation_text.rstrip() + "\n\n"
                    full_response += presentation_text

            if patent_search_for_summary:
                messages_list.append(
                    {"role": "user", "content": _PATENT_SEARCH_OBSERVATION_NUDGE}
                )
                summary_parts: list[str] = []
                async for chunk in provider.stream_chat(
                    messages=messages_list,
                    tools=None,
                    temperature=ai_config.temperature,
                    max_tokens=ai_config.max_tokens,
                ):
                    if chunk.get("type") == "content":
                        token = chunk.get("content", "")
                        if token.startswith("Error:"):
                            summary_parts.append(f"\n\n{token}")
                        elif token:
                            summary_parts.append(token)
                            yield token
                if summary_parts:
                    summary_text = _with_patent_links("".join(summary_parts))
                    if not summary_text.startswith("\n"):
                        summary_text = "\n\n" + summary_text.lstrip()
                    if not summary_text.endswith("\n\n"):
                        summary_text = summary_text.rstrip() + "\n\n"
                    full_response += summary_text

        auto_reply_note = build_auto_reply_note(auto_reply_matches)
        if auto_reply_note:
            note_chunk = f"\n\n{auto_reply_note}" if full_response.strip() else auto_reply_note
            full_response += note_chunk
            yield note_chunk

        if full_response:
            full_response = _with_patent_links(full_response)
            auto_reply_assets = [match["asset"] for match in auto_reply_matches]
            assistant_extra_data = enrich_message_extra_data(
                full_response,
                {
                    "model": ai_config.model,
                    "provider": ai_config.provider,
                    "knowledge_hits": knowledge_hits,
                    "auto_reply_rule_hits": [
                        {
                            "rule_id": match["rule_id"],
                            "rule_name": match["rule_name"],
                            "score": round(float(match["score"]), 4),
                            "asset_name": match["asset"].get("title")
                            or match["asset"].get("name")
                            or match["asset"].get("url"),
                            "matched_keywords": match.get("matched_keywords") or [],
                        }
                        for match in auto_reply_matches
                    ],
                    "outbound_assets": auto_reply_assets,
                },
            )
            assistant_msg = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=full_response,
                extra_data=assistant_extra_data,
            )
            db_session.add(assistant_msg)
            conversation.updated_at = datetime.now(timezone.utc)
            conversation.last_seen_at = datetime.now(timezone.utc)

    except BaseException as e:
        logger.error(f"Bot engine error: {e}", exc_info=True)
        yield f"\n\n抱歉，处理消息时出错：{e}"


async def _execute_tool(
    tool_name: str,
    tool_args: dict[str, Any],
    skills: list[Skill],
    db_session: AsyncSession,
) -> Any:
    """Execute a skill tool function."""
    for skill in skills:
        if skill.name == tool_name and skill.enabled:
            try:
                from app.skill.executor import execute_skill

                return await execute_skill(skill, tool_args)
            except BaseException as e:
                logger.error(f"Tool {tool_name} execution failed: {e}")
                return {"error": str(e)}

    return {"error": f"Tool '{tool_name}' not found or not enabled"}
