# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
# Proprietary and confidential. See LICENSE for terms.
"""ClearGlass Autonomous Agent OS v8.0 — runtime.

A deterministic, stdlib-only, fail-closed orchestration layer that turns the
``agents/clearglass_agent_os`` definition into runnable code:

* :mod:`agent_os.governance` — risk scoring + approval gating (fail-closed).
* :mod:`agent_os.roster`     — the thirteen specialist sub-agents as data.
* :mod:`agent_os.planning`   — objective -> executable DAG (waves + critical path).
* :mod:`agent_os.orchestrator` — the executive loop that produces a mission report.
* :mod:`agent_os.self_check` — governance self-check + executive report entrypoint.

Everything here is import-light (standard library only) so it runs unchanged
inside minimal CI environments, mirroring ``clearglass-commerce`` and
``sentinel`` conventions.
"""
from __future__ import annotations

__version__ = "8.0.0"

from .governance import RiskAssessment, RiskTier, score_action
from .orchestrator import AgentOS, MissionReport
from .roster import ROSTER, SubAgent

__all__ = [
    "AgentOS",
    "MissionReport",
    "ROSTER",
    "RiskAssessment",
    "RiskTier",
    "SubAgent",
    "score_action",
    "__version__",
]
