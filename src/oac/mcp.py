from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from oac.adapters import AdapterOptions, get_adapter
from oac.capsule import load_capsule
from oac.evals import evaluate_capsule
from oac.proposals import (
    create_proposal_bundle,
    preview_promotion,
    proposal_bundle_to_dict,
)


def serve_mcp(capsule_root: Path):
    """Orchestration-ready MCP server for OAC."""
    capsule = load_capsule(capsule_root)

    def send_response(result: Any, request_id: Any = None):
        payload = {"jsonrpc": "2.0", "id": request_id, "result": result}
        print(json.dumps(payload), flush=True)

    def send_error(code: int, message: str, request_id: Any = None):
        err = {"code": code, "message": message}
        payload = {"jsonrpc": "2.0", "id": request_id, "error": err}
        print(json.dumps(payload), flush=True)

    # Initial capability announcement
    print(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {
                    "mcp_version": "1.0",
                    "capsule_id": capsule.manifest.capsule_id,
                    "capabilities": {
                        "resources": {"list": True, "read": True},
                        "tools": {"list": True, "call": True},
                    },
                },
            }
        ),
        flush=True,
    )

    for line in sys.stdin:
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")

            if method == "resources/list":
                resources = []
                for group in (capsule.identity, capsule.memory, capsule.procedures):
                    for record in group:
                        rel_path = record.path.relative_to(capsule_root).as_posix()
                        resources.append(
                            {
                                "uri": f"oac://records/{rel_path}",
                                "name": record.title or record.path.name,
                                "mimeType": "text/markdown",
                                "description": record.summary
                                or f"OAC record of kind {record.kind}",
                            }
                        )
                for skill in capsule.skills:
                    rel_path = skill.path.relative_to(capsule_root).as_posix()
                    resources.append(
                        {
                            "uri": f"oac://records/{rel_path}",
                            "name": f"Skill: {skill.name}",
                            "mimeType": "text/markdown",
                            "description": "Durable agent skill workflow.",
                        }
                    )
                send_response({"resources": resources}, req_id)

            elif method == "resources/read":
                uri = req.get("params", {}).get("uri", "")
                if not uri.startswith("oac://records/"):
                    send_error(-32602, "Invalid URI", req_id)
                    continue

                rel_path = uri.replace("oac://records/", "")
                file_path = capsule_root / rel_path
                if not file_path.exists():
                    send_error(-32602, "Resource not found", req_id)
                    continue

                content = file_path.read_text(encoding="utf-8")
                send_response(
                    {"contents": [{"uri": uri, "mimeType": "text/markdown", "text": content}]},
                    req_id,
                )

            elif method == "tools/list":
                send_response(
                    {
                        "tools": [
                            {
                                "name": "oac_status",
                                "description": "Get high-level capsule status and target list.",
                                "inputSchema": {"type": "object", "properties": {}},
                            },
                            {
                                "name": "oac_read_record",
                                "description": "Read an OAC record by path or ID.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "path": {
                                            "type": "string",
                                            "description": "Relative path to record",
                                        },
                                        "record_id": {
                                            "type": "string",
                                            "description": "Stable record ID",
                                        },
                                    },
                                },
                            },
                            {
                                "name": "oac_hydrate",
                                "description": "Project the capsule into a native target surface.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "target": {
                                            "type": "string",
                                            "description": "Harness target (e.g. codex)",
                                        },
                                        "output": {
                                            "type": "string",
                                            "description": "Local path for projection",
                                        },
                                    },
                                    "required": ["target", "output"],
                                },
                            },
                            {
                                "name": "oac_learn",
                                "description": (
                                    "Automated pipeline: Ingest native edits, "
                                    "generate proposal, and run evals."
                                ),
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "target": {
                                            "type": "string",
                                            "description": "Harness target",
                                        },
                                        "source": {
                                            "type": "string",
                                            "description": "Path to the modified target surface",
                                        },
                                    },
                                    "required": ["target", "source"],
                                },
                            },
                            {
                                "name": "oac_promote",
                                "description": (
                                    "Canonicalize a proposal bundle (Write back to capsule)."
                                ),
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "proposal_path": {
                                            "type": "string",
                                            "description": "Path to proposal JSON",
                                        }
                                    },
                                    "required": ["proposal_path"],
                                },
                            },
                        ]
                    },
                    req_id,
                )

            elif method == "tools/call":
                params = req.get("params", {})
                tool_name = params.get("name")
                args = params.get("arguments", {})

                if tool_name == "oac_status":
                    send_response(
                        {
                            "capsule_id": capsule.manifest.capsule_id,
                            "targets": [t.name.value for t in capsule.manifest.targets],
                            "record_counts": {
                                "identity": len(capsule.identity),
                                "memory": len(capsule.memory),
                                "procedures": len(capsule.procedures),
                                "skills": len(capsule.skills),
                            },
                        },
                        req_id,
                    )

                elif tool_name == "oac_read_record":
                    target_path = args.get("path")
                    record_id = args.get("record_id")
                    found_content = None
                    if target_path:
                        p = capsule_root / target_path
                        if p.exists():
                            found_content = p.read_text(encoding="utf-8")
                    elif record_id:
                        for group in (capsule.identity, capsule.memory, capsule.procedures):
                            for r in group:
                                if r.record_id == record_id:
                                    found_content = r.body
                                    break
                    if found_content:
                        send_response(
                            {"content": [{"type": "text", "text": found_content}]}, req_id
                        )
                    else:
                        send_error(-32602, "Record not found", req_id)

                elif tool_name == "oac_hydrate":
                    target = args["target"]
                    output = Path(args["output"])
                    adapter = get_adapter(target)
                    report = adapter.hydrate(capsule_root, output, AdapterOptions())
                    send_response(
                        {
                            "status": "success",
                            "updated": report.updated_count,
                            "unchanged": report.unchanged_count,
                        },
                        req_id,
                    )

                elif tool_name == "oac_learn":
                    target = args["target"]
                    source = Path(args["source"])
                    adapter = get_adapter(target)
                    # 1. Ingest
                    ingest_report = adapter.ingest(source, capsule_root, AdapterOptions())
                    # 2. Propose
                    bundle = create_proposal_bundle(capsule_root, ingest_report)
                    # 3. Eval
                    eval_report = evaluate_capsule(capsule_root, bundle)

                    send_response(
                        {
                            "status": "success" if eval_report.passed else "eval-failed",
                            "proposal": proposal_bundle_to_dict(bundle),
                            "eval": {
                                "passed": eval_report.passed,
                                "checks": [
                                    {"name": c.name, "passed": c.passed, "summary": c.summary}
                                    for c in eval_report.checks
                                ],
                            },
                        },
                        req_id,
                    )

                elif tool_name == "oac_promote":
                    from oac.proposals import load_proposal_bundle

                    prop_path = Path(args["proposal_path"])
                    bundle = load_proposal_bundle(prop_path)
                    # Apply promotion
                    report = preview_promotion(bundle, capsule_root, apply=True, eval_passed=True)
                    send_response(
                        {"status": "success", "promotion_id": report.promotion_id}, req_id
                    )

        except EOFError:
            break
        except Exception as exc:
            send_error(-32603, str(exc), req_id)
