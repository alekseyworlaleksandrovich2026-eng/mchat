#!/usr/bin/env python3
"""Tenant skill runner (deployed by MChat control plane)."""
import json
import os
import sys
from pathlib import Path

# Minimal inline helpers (no app package in sidecar)
import importlib.util
import inspect
from types import SimpleNamespace

def _filter_kwargs(func, args):
    sig = inspect.signature(func)
    params = sig.parameters
    if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()):
        return {k: v for k, v in args.items() if v is not None}
    return {k: v for k, v in args.items() if k in params and v is not None}

def _args_to_namespace(args):
    return SimpleNamespace(
        command=str(args.get("command") or "search").lower(),
        query=args.get("query"),
        patent_id=args.get("patent_id"),
        company_name=args.get("company_name"),
        dimension=args.get("dimension"),
        page=int(args.get("page") or 1),
        page_size=int(args.get("page_size") or args.get("pageSize") or 10),
        scope=args.get("scope") or "cn",
        sort=args.get("sort") or "relation",
        details=bool(args.get("details")),
        limit=int(args.get("limit") or 20),
        type=args.get("type") or "software",
        field=args.get("field"),
        detail=bool(args.get("detail")),
        trademark_id=args.get("trademark_id") or args.get("trademark-id"),
        year_from=args.get("year_from") or None,
        year_to=args.get("year_to") or None,
    )

def _load_module(skill_dir, filename, module_key):
    path = skill_dir / filename
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location(module_key, path)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def _dispatch_namespace(skill_dir, main_module, args):
    skill_mod = _load_module(skill_dir, "patent_skill.py", "patent_skill")
    api_mod = _load_module(skill_dir, "patent_api.py", "patent_api")
    if skill_mod is None or api_mod is None:
        return {"error": "技能 main() 不支持工具参数；请添加 run(**kwargs)"}
    patent_api_cls = getattr(api_mod, "PatentAPI", None)
    patent_skill_cls = getattr(skill_mod, "PatentSkill", None)
    if patent_api_cls is None or patent_skill_cls is None:
        return {"error": "专利技能缺少 PatentAPI / PatentSkill 类"}
    api = patent_api_cls()
    skill = patent_skill_cls(api)
    ns = _args_to_namespace(args)
    handler = skill.commands.get(ns.command)
    if not handler:
        return {"error": f"Unknown command: {ns.command}"}
    return handler(ns)

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: run_skill.py <script_path>"}))
        sys.exit(1)
    script = Path(sys.argv[1]).resolve()
    args = json.loads(os.environ.get("MCHAT_SKILL_ARGS") or "{}")
    spec = importlib.util.spec_from_file_location("skill_entry", script)
    if spec is None or spec.loader is None:
        print(json.dumps({"error": f"Failed to load {script}"}))
        sys.exit(1)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if hasattr(module, "run"):
        result = module.run(**_filter_kwargs(module.run, args))
    elif hasattr(module, "main"):
        sig = inspect.signature(module.main)
        if len(sig.parameters) == 0:
            result = _dispatch_namespace(script.parent, module, args)
        else:
            result = module.main(**_filter_kwargs(module.main, args))
    else:
        result = {"error": "No main() or run() function found"}
    if result is None:
        print(json.dumps({"ok": True, "message": "技能执行完成（无返回内容）"}))
    elif isinstance(result, dict):
        print(json.dumps(result, ensure_ascii=False, default=str))
    elif isinstance(result, (str, int, float, bool, list)):
        print(json.dumps(result, ensure_ascii=False, default=str))
    else:
        print(json.dumps({"result": str(result)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
