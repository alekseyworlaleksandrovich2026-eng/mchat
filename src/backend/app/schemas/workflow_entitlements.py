from __future__ import annotations

from pydantic import BaseModel


class WorkflowEntitlementsResponse(BaseModel):
    can_create: bool = True
    can_save_dag: bool = True
    can_run: bool = True
    max_workflows: int = 0
    max_active_runs: int = 0
