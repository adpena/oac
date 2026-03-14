from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from oac.profile_models import AdapterProfile, HookPhase, HookRuntime


@dataclass(slots=True)
class HookResult:
    """Outcome of a single hook execution."""

    name: str
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    notes: list[str] = field(default_factory=list)


def run_hooks(
    profile: AdapterProfile, phase: HookPhase, context: dict[str, Any], root: Path = Path(".")
) -> list[HookResult]:
    """Execute all enabled hooks for a specific phase."""
    results: list[HookResult] = []

    # Prepare environment with context
    env = os.environ.copy()
    env["OAC_HOOK_PHASE"] = phase.value
    env["OAC_TARGET"] = profile.target.value
    env["OAC_PROFILE"] = profile.profile_name
    env["OAC_CONTEXT"] = json.dumps(context)

    for hook in profile.hooks:
        if hook.phase != phase or not hook.enabled:
            continue

        entrypoint = root / hook.entrypoint
        if not entrypoint.exists():
            results.append(
                HookResult(
                    name=hook.name,
                    success=False,
                    exit_code=-1,
                    stdout="",
                    stderr=f"Entrypoint not found: {hook.entrypoint}",
                    notes=["Hook failed because the entrypoint file was missing."],
                )
            )
            continue

        cmd: list[str] = []
        if hook.runtime == HookRuntime.PYTHON:
            cmd = ["python3", str(entrypoint)]
        elif hook.runtime == HookRuntime.TYPESCRIPT:
            # Prefer bun, fallback to node
            has_bun = subprocess.run(["which", "bun"], capture_output=True).returncode == 0
            cmd = ["bun", str(entrypoint)] if has_bun else ["node", str(entrypoint)]
        elif hook.runtime == HookRuntime.ZIG:
            cmd = ["zig", "run", str(entrypoint)]
        elif hook.runtime == HookRuntime.SHELL:
            cmd = ["bash", str(entrypoint)]
        else:
            # Other runtimes expect a compiled binary or direct execution
            cmd = [str(entrypoint)]

        cmd.extend(hook.args)

        hook_env = env.copy()
        hook_env.update(hook.env)

        try:
            process = subprocess.run(
                cmd,
                env=hook_env,
                capture_output=True,
                text=True,
                timeout=hook.timeout_seconds,
                cwd=root,
            )
            notes: list[str] = []
            if isinstance(hook.notes, str):
                notes = [hook.notes]
            elif hook.notes:
                notes = list(hook.notes)

            results.append(
                HookResult(
                    name=hook.name,
                    success=process.returncode == 0,
                    exit_code=process.returncode,
                    stdout=process.stdout,
                    stderr=process.stderr,
                    notes=notes,
                )
            )
        except subprocess.TimeoutExpired:
            results.append(
                HookResult(
                    name=hook.name,
                    success=False,
                    exit_code=-2,
                    stdout="",
                    stderr="Hook timed out.",
                    notes=[f"Timeout exceeded: {hook.timeout_seconds}s"],
                )
            )
        except Exception as exc:
            results.append(
                HookResult(
                    name=hook.name,
                    success=False,
                    exit_code=-3,
                    stdout="",
                    stderr=str(exc),
                    notes=["Execution error occurred."],
                )
            )

    return results
