"""Server ops skill — read-only health, logs, Milvus, kubectl get."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

_K8S_RESOURCES = frozenset({"pods", "nodes", "deployments", "services", "events"})
_OPS_COMMANDS = frozenset(
    {"health", "logs", "milvus", "k8s", "redis", "disk", "services", "db"}
)
_SYSTEMD_UNITS = (
    "mchat-cloud-backend.service",
    "mchat-backend.service",
    "mchat-frontend.service",
)


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
    """In-process health summary (no HTTP self-call — avoids single-worker deadlock)."""
    from app.core.config import settings

    db_check = _db_ping()
    milvus_check = _milvus()
    redis_check = _redis_ping()

    milvus_status = "disabled"
    if milvus_check.get("enabled"):
        milvus_status = (
            "connected" if milvus_check.get("connected") else "disconnected"
        )

    status = "healthy"
    if not db_check.get("ok"):
        status = "degraded"
    elif milvus_check.get("enabled") and not milvus_check.get("connected"):
        status = "degraded"
    if getattr(settings, "maintenance_mode", False):
        status = "maintenance"

    summary = (
        f"MChat 健康检查：{status}；数据库 "
        f"{'正常' if db_check.get('ok') else '异常'}；"
        f"Milvus {milvus_status}；Redis "
        f"{'正常' if redis_check.get('ok') else '异常'}"
    )
    return {
        "ok": status in ("healthy", "maintenance"),
        "status": status,
        "message": summary,
        "database": "connected" if db_check.get("ok") else "disconnected",
        "milvus": milvus_status,
        "redis": "connected" if redis_check.get("ok") else "disconnected",
        "maintenance_mode": bool(getattr(settings, "maintenance_mode", False)),
        "server_ops_skills_enabled": bool(
            getattr(settings, "server_ops_skills_enabled", False)
        ),
        "details": {
            "database": db_check,
            "milvus": milvus_check,
            "redis": redis_check,
        },
    }


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


def _systemctl_is_active(systemctl: str, unit: str) -> dict[str, str]:
    for extra in ([], ["--user"]):
        try:
            proc = subprocess.run(
                [systemctl, *extra, "is-active", unit],
                capture_output=True,
                text=True,
                timeout=10,
            )
            scope = "system" if not extra else "user"
            return {
                "unit": unit,
                "scope": scope,
                "active": (proc.stdout or "").strip(),
                "exit_code": str(proc.returncode),
            }
        except (OSError, subprocess.TimeoutExpired) as e:
            last_err = str(e)
    return {"unit": unit, "error": last_err or "systemctl failed"}


def _services() -> dict[str, Any]:
    systemctl = shutil.which("systemctl")
    if not systemctl:
        return {"ok": False, "error": "未找到 systemctl"}
    rows = [_systemctl_is_active(systemctl, unit) for unit in _SYSTEMD_UNITS]
    return {"ok": True, "units": rows}


def _db_ping() -> dict[str, Any]:
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    from sqlalchemy import text

    from app.core.config import settings
    from app.core.database import async_session_factory

    async def _ping() -> None:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))

    def _run_in_thread() -> None:
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_ping())
        finally:
            loop.close()

    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(_run_in_thread).result(timeout=15)
        db_url = (settings.database_url or "").split("@")[-1][:120]
        return {"ok": True, "database": db_url}
    except Exception as e:
        return {"ok": False, "error": str(e)}


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
    if cmd == "services":
        return _services()
    if cmd == "db":
        return _db_ping()
    return {"ok": False, "error": f"未知 command: {cmd}，可选: {', '.join(sorted(_OPS_COMMANDS))}"}
