#!/usr/bin/env python3
"""Chat Completions via the official OpenAI Python SDK, pointed at Model Router.

    export ROUTER_KEY=rk_YOUR_KEY
    export OPENAI_API_KEY=sk-YOUR_OPENAI_KEY   # and/or GROQ_API_KEY=gsk_YOUR_GROQ_KEY
    pip install -r examples/requirements.txt
    python examples/chat.py
"""
from __future__ import annotations

import os
import sys

from openai import OpenAI

BASE = os.environ.get("BASE", "https://model-router.lee-anthony57.workers.dev") + "/v1"
ROUTER_KEY = os.environ.get("ROUTER_KEY")
if not ROUTER_KEY:
    sys.exit("Set ROUTER_KEY to your rk_… key (see the README)")

headers = {}
if os.environ.get("OPENAI_API_KEY"):
    headers["X-OpenAI-Key"] = os.environ["OPENAI_API_KEY"]
if os.environ.get("GROQ_API_KEY"):
    headers["X-Groq-Key"] = os.environ["GROQ_API_KEY"]
if not headers:
    sys.exit("Set OPENAI_API_KEY and/or GROQ_API_KEY")

client = OpenAI(base_url=BASE, api_key=ROUTER_KEY, default_headers=headers)


# Prefer the with_raw_response helper so we can print router headers (no secrets).
create = client.chat.completions.with_raw_response.create

print("== auto chat")
raw = create(
    model="auto",
    max_tokens=128,
    messages=[{"role": "user", "content": "Say the word hello."}],
)
msg = raw.parse()
h = raw.headers
print("assistant:", (msg.choices[0].message.content or "").strip())
for name in (
    "X-Router-Model",
    "X-Router-Provider",
    "X-Router-Route",
    "X-Router-Intent",
    "X-Router-Sticky",
    "X-Router-Est-Cost-USD",
    "X-Router-Usage",
):
    val = h.get(name)
    if val:
        print(f"  {name}: {val}")

print("\n== sticky session (X-Router-Session)")
session = "python-example-" + str(os.getpid())
raw1 = create(
    model="auto",
    max_tokens=128,
    messages=[{"role": "user", "content": "Write a one-line Python hello function. Reply OK."}],
    extra_headers={"X-Router-Session": session},
)
c1 = raw1.parse()
print(
    "turn 1:",
    (c1.choices[0].message.content or "").strip(),
    "|",
    raw1.headers.get("X-Router-Model"),
    raw1.headers.get("X-Router-Sticky"),
    raw1.headers.get("X-Router-Intent"),
)
raw2 = create(
    model="auto",
    max_tokens=128,
    messages=[{"role": "user", "content": "Thanks, one word."}],
    extra_headers={"X-Router-Session": session},
)
c2 = raw2.parse()
print(
    "turn 2:",
    (c2.choices[0].message.content or "").strip(),
    "|",
    raw2.headers.get("X-Router-Model"),
    raw2.headers.get("X-Router-Sticky"),
    raw2.headers.get("X-Router-Intent"),
)
