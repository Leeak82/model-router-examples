# Model Router examples

A cheaper way to run several AIs from one OpenAI-compatible endpoint: `model: "auto"` picks a capable model from the provider keys you already have, and a shared project memory (plus task locks over MCP) keeps those AIs in sync.

This repository is **examples and a quickstart only** (MIT). It is not the Model Router source.

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/anthonyleebuilds)

## Quick start

- **API base:** `https://model-router.lee-anthony57.workers.dev/v1`
- **Docs:** [https://model-router.lee-anthony57.workers.dev/docs](https://model-router.lee-anthony57.workers.dev/docs)
- **Status:** [https://model-router.lee-anthony57.workers.dev/health](https://model-router.lee-anthony57.workers.dev/health)

### Get a free router key

Key creation is self-serve. From the [docs](https://model-router.lee-anthony57.workers.dev/docs) (the [home page](https://model-router.lee-anthony57.workers.dev/) and [pricing](https://model-router.lee-anthony57.workers.dev/pricing) also point here):

```bash
curl -s -X POST https://model-router.lee-anthony57.workers.dev/v1/keys \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com"}'
```

The email is optional (useful later if billing opens). The response includes a key that looks like `rk_…`. It is shown once — keep it secret. Limit: 5 new keys per IP per day.

You can also call the API without a key using `model: "free-demo"` to confirm connectivity (canned reply, not counted against the daily limit).

### Bring your own provider keys

The router forwards a provider key on each request and does **not** store or log it. You pay OpenAI, Groq, or xAI directly.

| Header | Use |
|---|---|
| `Authorization: Bearer rk_YOUR_KEY` | Your router key (or `X-API-Key`) |
| `X-Provider-Key` | One provider key; prefix detects the vendor (`sk-` OpenAI, `gsk_` Groq, `xai-` xAI) |
| `X-OpenAI-Key` and `X-Groq-Key` | Send both so `auto` can choose across providers |
| `X-XAI-Key` | Required for image generation |

```bash
export BASE=https://model-router.lee-anthony57.workers.dev
export ROUTER_KEY=rk_YOUR_KEY
export OPENAI_API_KEY=sk-YOUR_OPENAI_KEY
export GROQ_API_KEY=gsk_YOUR_GROQ_KEY

curl -s $BASE/v1/chat/completions \
  -H "Authorization: Bearer $ROUTER_KEY" \
  -H "X-OpenAI-Key: $OPENAI_API_KEY" \
  -H "X-Groq-Key: $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"auto","max_tokens":16,"messages":[{"role":"user","content":"Hello"}]}'
```

## Auto routes

| `model` | What it does |
|---|---|
| `auto` | Intent- and complexity-aware: simple chat → cheap (tier 1), code / tools / images / long context → balanced (tier 2), hard reasoning → smart (tier 3) |
| `auto:cheap` | Cheapest capable model among your keys (tier 1+) |
| `auto:balanced` | Cheapest mid-tier model or better (tier 2+) |
| `auto:smart` | Cheapest top-tier model (tier 3); falls back to the best tier you have keys for |
| `auto:code` | Coding ladder that prefers strong code models (`gpt-4.1-mini` / `qwen/qwen3.8-27b`, or `gpt-4.1` for hard tasks) |

Capability checks cover tools, image inputs, and context length. If the first pick errors (not found, rate-limited, blocked, or 5xx), the router tries the next candidate.

Preview a choice without calling a model: `GET /v1/route?model=auto&prompt=...` (add `&tools=1` or `&vision=1` to test filters). See [examples/curl.sh](examples/curl.sh).

### Sticky sessions and intent

On any `auto*` route, a successful pick is **pinned for 1 hour** so follow-ups stay on the same model and can hit the provider's prompt cache.

Session key, in order: `X-Router-Session` header, else the OpenAI `user` field, else a hash of the system prompt and first user message. Send `X-Router-Sticky: off` to opt out for one request (the pin is left in place). If the pinned model fails or lacks a capability needed later (vision, tools, or context), the router falls back and re-pins.

### Response headers

| Header | Meaning |
|---|---|
| `X-Router-Model`, `X-Router-Provider` | The model that actually served the call |
| `X-Router-Route` | `explicit` or the auto mode |
| `X-Router-Intent` | On `auto*` routes: `chat`, `code`, or `reasoning` |
| `X-Router-Sticky` | On `auto*` routes: `hit`, `new`, or `off` |
| `X-Router-Est-Cost-USD` | Estimated provider cost |
| `X-Router-Cost-USD` | Provider-reported cost (image URL responses) |
| `X-Router-Usage` | Calls used today / daily limit |
| `X-Router-Project`, `X-Router-Memory-Entries`, `X-Router-Memory-Role` | Project memory that was injected |
| `X-Router-Note` | Routing notes (for example a fallback) |

## Image generation

`POST /v1/images/generations` is OpenAI-compatible and proxies to xAI Grok Imagine (`grok-imagine-image-2.0`). **You need your own xAI API key** in `X-XAI-Key` (or `X-Provider-Key` starting with `xai-`). Without that header the router returns 400 and does not call xAI.

Each requested image counts as one call toward your daily limit. You pay xAI directly. Temporary image URLs should be downloaded promptly. Deferred jobs and storage uploads are not supported through the router. See the [docs](https://model-router.lee-anthony57.workers.dev/docs) for fields and list prices.

## Plans

**Free** (available now): 100 routed calls per day, 20 projects, 2,000 memory entries per project. Limits reset at 00:00 UTC. Over the limit returns HTTP 429. Demo calls are not counted. Provider token costs are billed by the provider, not by Model Router.

**Pro:** coming soon. Pricing is not finalized; checkout is not open yet. Free keys and projects will carry over.

## Examples

Copy [`.env.example`](.env.example) to `.env` and fill in keys (never commit `.env`).

| File | What it shows |
|---|---|
| [examples/curl.sh](examples/curl.sh) | Health, demo, `auto` chat, route preview, sticky session, usage, image-route validation (no xAI spend) |
| [examples/chat.py](examples/chat.py) | Python `openai` SDK with `base_url`, auto routing, sticky + intent headers |
| [examples/chat.mjs](examples/chat.mjs) | Node `openai` SDK with `baseURL` |
| [examples/multi_agent_sync.py](examples/multi_agent_sync.py) | Two agents sharing memory, a task lock, and a handoff over the MCP HTTP API |
| [examples/mcp.cursor.json](examples/mcp.cursor.json) | Cursor MCP config for `/mcp` |
| [examples/mcp.claude-desktop.json](examples/mcp.claude-desktop.json) | Claude Desktop-style MCP config for `/mcp` |

```bash
# curl
export ROUTER_KEY=rk_YOUR_KEY OPENAI_API_KEY=sk-YOUR_OPENAI_KEY GROQ_API_KEY=gsk_YOUR_GROQ_KEY
bash examples/curl.sh

# Python
pip install -r examples/requirements.txt
python examples/chat.py
python examples/multi_agent_sync.py

# Node
cd examples && npm install && node chat.mjs
```

The same memory, task locks, and sync log are also available over REST (`/v1/projects/...`). Full reference: [docs](https://model-router.lee-anthony57.workers.dev/docs).

## License

[MIT](LICENSE) for the examples in this repo only. Model Router itself is a hosted service; this repo does not include its source.
