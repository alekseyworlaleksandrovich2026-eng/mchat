"""Server ops skill — read-only health, logs, Milvus, kubectl get."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

_K8S_RESOURCES = frozenset({"pods", "nodes", "deployments", "services", "events"})
_OPS_COMMANDS = frozenset({"health", "logs", "milvus", "k8s", "redis", "disk"})


def _tail_log(source: str, lines: int) -> dict[str, Any]:
    safe_lines = max(20, min(int(lines or 80), 200))
    log_file = "error.log" if source == "error" else "app.log"
    path = Path("logs") / log_file
    if not path.exists():
        return {"ok": False, "message": f"日志不存在: {path}"}
    text = path.read_text(encoding="utf-8", errors="replace")
    chunk = text.splitlines()[-safe_lines:]
    return {
        "ok": True,
        "source": source,
        "lines": chunk,
        "path": str(path.resolve()),
    }


def _health() -> dict[str, Any]:
    port = os.environ.get("SERVER_PORT") or os.environ.get("PORT") or "3001"
    url = f"http://127.0.0.1:{port}/api/health"
    out: dict[str, Any] = {"url": url}
    try:
        with urlopen(url, timeout=8) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            out["http_status"] = resp.status
            try:
                out["body"] = json.loads(body)
            except json.JSONDecodeError:
                out["body"] = body[:2000]
        out["ok"] = True
    except URLError as e:
        out["ok"] = False
        out["error"] = str(e)
    return out


def _milvus() -> dict[str, Any]:
    try:
        from app.knowledge.milvus_client import milvus_client
        from app.knowledge.milvus_runtime import get_milvus_runtime

        runtime = get_milvus_runtime()
        return {
            "ok": True,
            "enabled": runtime.enabled,
            "host": runtime.host,
            "port": runtime.port,
            "connected": bool(milvus_client._connected),
            "collection_dimension": milvus_client.dimension,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _redis_ping() -> dict[str, Any]:
    try:
        from app.core.config import settings

        url = (settings.redis_url or "").strip()
        if not url:
            return {"ok": False, "error": "未配置 REDIS_URL"}
        import redis

        client = redis.from_url(url, socket_connect_timeout=5)
        client.ping()
        return {"ok": True, "redis_url": url.split("@")[-1][:120]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _disk_usage() -> dict[str, Any]:
    import shutil

    paths = [Path("/"), Path(".").resolve()]
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for p in paths:
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        try:
            usage = shutil.disk_usage(p)
            out.append(
                {
                    "path": key,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "percent_used": round(100 * usage.used / usage.total, 1)
                    if usage.total
                    else 0,
                }
            )
        except OSError as e:
            out.append({"path": key, "error": str(e)})
    return {"ok": True, "volumes": out}


def _k8s_get(namespace: str, resource: str) -> dict[str, Any]:
    kubectl = shutil.which("kubectl")
    if not kubectl:
        return {
            "ok": False,
            "error": "未找到 kubectl；请在服务器安装并配置 KUBECONFIG",
        }
    ns = (namespace or "default").strip()
    res = (resource or "pods").strip().lower()
    if res not in _K8S_RESOURCES:
        return {
            "ok": False,
            "error": f"resource 必须是: {', '.join(sorted(_K8S_RESOURCES))}",
        }
    cmd = [
        kubectl,
        "get",
        res,
        "-n",
        ns,
        "-o",
        "wide",
        "--request-timeout=30s",
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=35,
            check=False,
        )
        return {
            "ok": proc.returncode == 0,
            "command": " ".join(cmd),
            "stdout": (proc.stdout or "")[-8000:],
            "stderr": (proc.stderr or "")[-2000:],
            "exit_code": proc.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "kubectl 超时"}
    except OSError as e:
        return {"ok": False, "error": str(e)}


def run(
    *,
    command: str = "health",
    source: str = "app",
    lines: int = 80,
    namespace: str = "default",
    resource: str = "pods",
    **_: Any,
) -> dict[str, Any]:
    cmd = (command or "health").strip().lower()
    if cmd == "health":
        return _health()
    if cmd == "logs":
        return _tail_log(source, lines)
    if cmd == "milvus":
        return _milvus()
    if cmd == "k8s":
        return _k8s_get(namespace, resource)
    if cmd == "redis":
        return _redis_ping()
    if cmd == "disk":
        return _disk_usage()
    return {"ok": False, "error": f"未知 command: {cmd}，可选: {', '.join(sorted(_OPS_COMMANDS))}"}
