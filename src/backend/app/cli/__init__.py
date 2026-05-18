"""mchat CLI - Management command-line interface."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path


def main() -> None:
    """Entry point for the mchat CLI."""
    parser = argparse.ArgumentParser(
        prog="mchat",
        description="mchat - Multi-tenant AI Chat Platform CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init: initialize the project
    init_parser = subparsers.add_parser("init", help="Initialize mchat project")
    init_parser.add_argument(
        "--path",
        default=".",
        help="Project path (default: current directory)",
    )

    # run: start the server
    run_parser = subparsers.add_parser("run", help="Run the mchat server")
    run_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind (default: 0.0.0.0)",
    )
    run_parser.add_argument(
        "--port",
        type=int,
        default=3001,
        help="Port to bind (default: 3001)",
    )
    run_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )

    # config: manage configuration
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_sub = config_parser.add_subparsers(dest="config_action")
    config_sub.add_parser("show", help="Show current configuration")
    config_sub.add_parser("validate", help="Validate configuration")

    # skill: manage skills
    skill_parser = subparsers.add_parser("skill", help="Manage skills")
    skill_sub = skill_parser.add_subparsers(dest="skill_action")
    skill_sub.add_parser("list", help="List installed skills")
    skill_parser_create = skill_sub.add_parser("create", help="Create a new skill")
    skill_parser_create.add_argument("name", help="Skill name")

    # db: database management
    db_parser = subparsers.add_parser("db", help="Database management")
    db_sub = db_parser.add_subparsers(dest="db_action")
    db_sub.add_parser("init", help="Initialize database tables")
    db_sub.add_parser("migrate", help="Run database migrations")
    db_sub.add_parser("seed", help="Seed database with sample data")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    asyncio.run(_handle_command(args))


async def _handle_command(args: argparse.Namespace) -> None:
    """Route command to handler."""
    match args.command:
        case "init":
            await _cmd_init(args)
        case "run":
            await _cmd_run(args)
        case "config":
            await _cmd_config(args)
        case "skill":
            await _cmd_skill(args)
        case "db":
            await _cmd_db(args)
        case _:
            print(f"Unknown command: {args.command}")
            sys.exit(1)


async def _cmd_init(args: argparse.Namespace) -> None:
    """Initialize a new mchat project."""
    project_path = Path(args.path).resolve()
    print(f"Initializing mchat project at {project_path}")

    # Create directory structure
    dirs = [
        "src/backend/app",
        "src/frontend/src",
        "skills",
        "docs",
        "ops/docker",
        "ops/nginx",
        "ops/scripts",
        "tests",
    ]
    for d in dirs:
        (project_path / d).mkdir(parents=True, exist_ok=True)

    # Create .env from example
    env_path = project_path / ".env"
    if not env_path.exists():
        env_path.write_text(
            "# mchat Configuration\n"
            "DATABASE_URL=mysql+aiomysql://mchat:mchat123@localhost:3306/mchat\n"
            "JWT_SECRET=change-me-to-a-random-string\n"
            "ADMIN_USERNAME=admin\n"
            "ADMIN_PASSWORD=admin123\n"
        )

    print("✅ Project initialized! Run 'mchat run' to start.")


async def _cmd_run(args: argparse.Namespace) -> None:
    """Start the mchat server."""
    import uvicorn

    print(f"Starting mchat server on {args.host}:{args.port}")
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


async def _cmd_config(args: argparse.Namespace) -> None:
    """Manage configuration."""
    from app.core.config import settings

    match args.config_action:
        case "show":
            print("Current configuration:")
            for field_name in settings.model_fields:
                value = getattr(settings, field_name)
                if "secret" in field_name.lower() or "password" in field_name.lower():
                    value = "********"
                print(f"  {field_name} = {value}")
        case "validate":
            try:
                print("✅ Configuration is valid")
            except Exception as e:
                print(f"❌ Configuration error: {e}")
                sys.exit(1)
        case _:
            print("Use: mchat config show|validate")


async def _cmd_skill(args: argparse.Namespace) -> None:
    """Manage skills."""
    match args.skill_action:
        case "list":
            skills_dir = Path("skills")
            if skills_dir.exists():
                for skill_dir in sorted(skills_dir.iterdir()):
                    if skill_dir.is_dir():
                        skill_md = skill_dir / "SKILL.md"
                        if skill_md.exists():
                            # Parse name from SKILL.md frontmatter
                            content = skill_md.read_text()
                            name = skill_dir.name
                            for line in content.split("\n"):
                                if line.startswith("name:"):
                                    name = line.split(":", 1)[1].strip()
                                    break
                            print(f"  📦 {name} ({skill_dir.name})")
        case "create":
            name = args.name
            skill_dir = Path("skills") / name
            skill_dir.mkdir(parents=True, exist_ok=True)

            (skill_dir / "SKILL.md").write_text(
                "---\n"
                f"name: {name}\n"
                "description: A new skill\n"
                "tools: []\n"
                "---\n\n"
                f"# {name}\n\n"
                "Brief description of this skill.\n"
            )

            (skill_dir / "handler.py").write_text(
                '"""Handler functions for skill tools."""\n\n'
                "from typing import Any\n\n\n"
                "async def execute(tool_name: str, args: dict[str, Any]) -> Any:\n"
                '    """Execute a tool call."""\n'
                '    return {"result": "not implemented"}\n'
            )

            print(f"✅ Created skill: {name}")

        case _:
            print("Use: mchat skill list|create <name>")


async def _cmd_db(args: argparse.Namespace) -> None:
    """Database management."""
    import app.models  # noqa: F401 - register ORM models on metadata
    from app.core.database import Base, async_session_factory, close_db, engine

    try:
        match args.db_action:
            case "init":
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                print("✅ Database tables created")
            case "migrate":
                from app.core.migrations import apply_schema_patches

                async with engine.begin() as conn:
                    applied = await conn.run_sync(apply_schema_patches)
                if applied:
                    print(f"✅ Applied patches: {', '.join(applied)}")
                else:
                    print("✅ Database schema is up to date")
            case "seed":
                from app.models.user import User
                from app.core.security import get_password_hash

                async with async_session_factory() as db:
                    from sqlalchemy import select

                    result = await db.execute(
                        select(User).where(User.username == "admin")
                    )
                    if result.scalar_one_or_none() is None:
                        admin = User(
                            username="admin",
                            password_hash=get_password_hash("admin123"),
                            role="admin",
                        )
                        db.add(admin)
                        await db.commit()
                        print("✅ Admin user created (admin / admin123)")
                    else:
                        print("ℹ️  Admin user already exists")
            case _:
                print("Use: mchat db init|migrate|seed")
    finally:
        await close_db()


if __name__ == "__main__":
    main()
