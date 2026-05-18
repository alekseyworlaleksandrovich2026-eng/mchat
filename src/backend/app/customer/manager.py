"""Customer service manager - tracks agents and routes conversations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from loguru import logger


class CustomerManager:
    """Manages customer service agent state and conversation routing."""

    def __init__(self) -> None:
        self._online_agents: dict[str, dict[str, Any]] = {}
        self._agent_sessions: dict[str, str] = {}  # agent_id -> session_id

    def agent_online(
        self, agent_id: str, agent_info: dict[str, Any] | None = None
    ) -> None:
        """Mark an agent as online."""
        self._online_agents[agent_id] = {
            "agent_id": agent_id,
            "online_at": datetime.now(timezone.utc).isoformat(),
            "status": "online",
            **(agent_info or {}),
        }
        logger.info(f"Agent {agent_id} is now online")

    def agent_offline(self, agent_id: str) -> None:
        """Mark an agent as offline."""
        self._online_agents.pop(agent_id, None)
        self._agent_sessions.pop(agent_id, None)
        logger.info(f"Agent {agent_id} is now offline")

    def get_online_agents(self) -> list[dict[str, Any]]:
        """Get list of online agents."""
        return list(self._online_agents.values())

    def get_online_count(self) -> int:
        """Get count of online agents."""
        return len(self._online_agents)

    def is_agent_online(self, agent_id: str) -> bool:
        """Check if an agent is online."""
        return agent_id in self._online_agents

    def route_conversation(
        self, visitor_id: str, preferred_agent: str | None = None
    ) -> dict[str, Any] | None:
        """Route a visitor to the best available agent."""
        if preferred_agent and preferred_agent in self._online_agents:
            return self._online_agents[preferred_agent]

        # Round-robin: return the first available agent
        for agent_id, agent_info in self._online_agents.items():
            return {
                "agent_id": agent_id,
                **agent_info,
            }

        return None

    def bind_session(self, agent_id: str, session_id: str) -> None:
        """Bind an agent to a WebSocket session."""
        self._agent_sessions[agent_id] = session_id

    def unbind_session(self, agent_id: str) -> None:
        """Unbind an agent from their WebSocket session."""
        self._agent_sessions.pop(agent_id, None)

    def get_agent_session(self, agent_id: str) -> str | None:
        """Get the WebSocket session ID for an agent."""
        return self._agent_sessions.get(agent_id)


# Singleton instance
customer_manager = CustomerManager()
