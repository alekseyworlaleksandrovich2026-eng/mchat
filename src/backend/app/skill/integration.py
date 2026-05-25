"""Per-skill integration metadata (channel-level secret overrides)."""

from __future__ import annotations

from typing import Any


def integration_spec_from_config(skill_name: str, config: dict | None) -> dict[str, Any] | None:
    """
    Read integration requirements from skill.config.

    Supported shapes:
      integration: { fields: [{key, label, secret?}], allow_channel_override?: bool }
      required_secrets: ["api_token"] or {"api_token": "API Token"}
    """
    if not config:
        return None

    integration = config.get("integration")
    if isinstance(integration, dict) and integration.get("fields"):
        fields = integration.get("fields") or []
        if fields:
            return {
                "skill": skill_name,
                "fields": [_normalize_field(f) for f in fields if isinstance(f, dict)],
                "allow_channel_override": bool(
                    integration.get("allow_channel_override", True)
                ),
                "source": "skill",
            }

    required = config.get("required_secrets")
    fields: list[dict[str, Any]] = []
    if isinstance(required, list):
        for item in required:
            if isinstance(item, str) and item.strip():
                fields.append(
                    {"key": item.strip(), "label": item.strip(), "secret": True}
                )
    elif isinstance(required, dict):
        for key, label in required.items():
            if str(key).strip():
                fields.append(
                    {
                        "key": str(key).strip(),
                        "label": str(label) if label else str(key),
                        "secret": True,
                    }
                )

    if fields:
        return {
            "skill": skill_name,
            "fields": fields,
            "allow_channel_override": bool(config.get("allow_channel_override", True)),
            "source": "skill",
        }
    return None


def _normalize_field(raw: dict[str, Any]) -> dict[str, Any]:
    key = str(raw.get("key") or "").strip()
    return {
        "key": key,
        "label": str(raw.get("label") or key),
        "secret": bool(raw.get("secret", True)),
        "placeholder": raw.get("placeholder"),
        "help": raw.get("help"),
    }


def merge_integration_schemas(
    *schemas: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Merge template + skill specs; skill name is unique key."""
    by_skill: dict[str, dict[str, Any]] = {}
    for schema in schemas:
        if not schema:
            continue
        for block in schema:
            if not isinstance(block, dict):
                continue
            name = str(block.get("skill") or "").strip()
            if not name:
                continue
            existing = by_skill.get(name)
            if existing is None:
                by_skill[name] = dict(block)
                continue
            # Template labels win; union fields by key
            field_map = {
                str(f.get("key")): f
                for f in (existing.get("fields") or [])
                if isinstance(f, dict) and f.get("key")
            }
            for f in block.get("fields") or []:
                if isinstance(f, dict) and f.get("key"):
                    field_map[str(f["key"])] = f
            existing["fields"] = list(field_map.values())
            existing["allow_channel_override"] = block.get(
                "allow_channel_override",
                existing.get("allow_channel_override", True),
            )
    return list(by_skill.values())
