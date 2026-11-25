#!/usr/bin/env python3
"""Two agents share one project over Model Router's MCP HTTP API.

Agent "writer" adds a decision to memory, claims a task, appends a log line,
then hands the task to "reviewer". Agent "reviewer" reads context, sees the
lock, adds a note, and releases the task.

Uses curl (not Python urllib): this Worker returns Cloudflare 1010 to some
library HTTP clients.

    export ROUTER_KEY=rk_YOUR_KEY
    python examples/multi_agent_sync.py

No provider key is required: this only uses the memory / lock / log tools.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

BASE = os.environ.get("BASE", "https://model-router.lee-anthony57.workers.dev")
ROUTER_KEY = os.environ.get("ROUTER_KEY")
if not ROUTER_KEY:
    sys.exit("Set ROUTER_KEY to your rk_… key (see the README)")

PROJECT = os.environ.get("PROJECT_ID", "examples-sync-" + time.strftime("%Y%m%d-%H%M%S"))
MCP = BASE.rstrip("/") + "/mcp"
UA = "model-router-examples/1 (curl)"


def curl(method, url, headers, data=None):
    cmd = ["curl", "-sS", "-A", UA, "-X", method, url, "-w", "\nhttp_code:%{http_code}"]
    for k, v in headers.items():
        cmd.extend(["-H", f"{k}: {v}"])
    if data is not None:
        cmd.extend(["--data-binary", data])
    out = subprocess.check_output(cmd, text=True)
    body, _, trailer = out.rpartition("\nhttp_code:")
    code = int(trailer.strip() or "0")
    if code >= 400:
        sys.exit(f"HTTP {code} for {method} {url}: {body[:400]}")
    return json.loads(body) if body.strip() else {}


def mcp(method, params=None, agent=None, project=None):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + ROUTER_KEY,
        "MCP-Protocol-Version": "2025-06-18",
    }
    if agent:
        headers["X-Agent-Name"] = agent
    if project:
        headers["X-Project-Id"] = project
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}})
    return curl("POST", MCP, headers, payload)


def tool(name, arguments, agent, project=None):
    r = mcp("tools/call", {"name": name, "arguments": arguments}, agent=agent, project=project)
    if "error" in r:
        sys.exit(f"{name} RPC error: {r['error']}")
    result = r.get("result") or {}
    if result.get("isError"):
        sys.exit(f"{name} failed: {json.dumps(result)[:400]}")
    sc = result.get("structuredContent")
    if sc is not None:
        return sc
    texts = [c.get("text") for c in result.get("content") or [] if c.get("type") == "text"]
    if texts:
        try:
            return json.loads(texts[0])
        except json.JSONDecodeError:
            return {"text": texts[0]}
    return result


print(f"Project id: {PROJECT}")
print("== writer: create_project, add_memory, claim_task, append_log, handoff_task")
created = tool(
    "create_project",
    {"id": PROJECT, "name": "Examples sync demo", "goals": ["Ship a shared-memory demo"]},
    agent="writer",
)
print("  created:", created.get("id"), "entries:", created.get("entries"))

mem = tool(
    "add_memory",
    {
        "project": PROJECT,
        "type": "decision",
        "text": "Use Postgres, not Mongo, for the primary store.",
        "author": "writer",
    },
    agent="writer",
)
entry = (mem.get("data") or [mem])[0] if isinstance(mem, dict) else mem
print("  memory type:", entry.get("type") if isinstance(entry, dict) else entry)

claim = tool(
    "claim_task",
    {"project": PROJECT, "task": "db-schema", "note": "Drafting the users table", "lease_minutes": 30},
    agent="writer",
)
print("  claimed db-schema until", claim.get("expires_at") or claim)

tool(
    "append_log",
    {
        "project": PROJECT,
        "type": "change",
        "task": "db-schema",
        "text": "Added a draft users table; email is unique.",
    },
    agent="writer",
)

handoff = tool(
    "handoff_task",
    {
        "project": PROJECT,
        "task": "db-schema",
        "to": "reviewer",
        "note": "Schema drafted. Please review the unique email constraint, then release.",
    },
    agent="writer",
)
print("  handed to", handoff.get("holder") or "reviewer")

print("== reviewer: get_context, list_tasks, add_memory, release_task")
ctx = tool("get_context", {"project": PROJECT, "mode": "auto"}, agent="reviewer")
text = ctx.get("text") or ctx.get("context") or json.dumps(ctx)
print("  context excerpt:")
for line in text.splitlines()[:12]:
    print("   ", line)

tasks = tool("list_tasks", {"project": PROJECT}, agent="reviewer")
data = tasks.get("data") or tasks.get("tasks") or tasks
holders = []
if isinstance(data, list):
    holders = [f"{t.get('task')} held by {t.get('holder')}" for t in data if isinstance(t, dict)]
print("  tasks:", ", ".join(holders) or json.dumps(data)[:300])

tool(
    "add_memory",
    {
        "project": PROJECT,
        "type": "note",
        "text": "Reviewer agrees: keep email unique.",
        "author": "reviewer",
    },
    agent="reviewer",
)

released = tool(
    "release_task",
    {"project": PROJECT, "task": "db-schema", "note": "Reviewed and merged."},
    agent="reviewer",
)
print("  released:", released.get("released") or released.get("task") or released)

# Clean up so repeated runs do not pile up demo projects on a free key.
# There is no delete_project MCP tool; the REST route is used here only for cleanup.
gone = curl(
    "DELETE",
    f"{BASE.rstrip('/')}/v1/projects/{PROJECT}",
    {"Authorization": "Bearer " + ROUTER_KEY},
)
print("  cleaned up project:", gone.get("deleted") is True or gone.get("id"))
print("Done.")
