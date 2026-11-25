# Example files

Put your keys in the environment (see `../.env.example`). Never commit real keys.

- `curl.sh` — bash + curl (no extra packages except `jq`)
- `chat.py` — official `openai` Python SDK (`pip install -r requirements.txt`)
- `chat.mjs` — official `openai` Node SDK (`npm install` in this folder)
- `multi_agent_sync.py` — two agents coordinating over `POST /mcp` (calls curl; Python urllib is blocked by this host)
- `mcp.cursor.json` — copy the `mcpServers` block into `~/.cursor/mcp.json` or `.cursor/mcp.json`
- `mcp.claude-desktop.json` — same shape for Claude Desktop (`claude_desktop_config.json`) and other clients that speak Streamable HTTP MCP with custom headers

Claude Code:

```bash
claude mcp add --transport http model-router https://model-router.lee-anthony57.workers.dev/mcp \
  --header "Authorization: Bearer rk_YOUR_KEY" \
  --header "X-Project-Id: my-app" \
  --header "X-Agent-Name: claude-code"
```

If a client only supports local stdio MCP servers, bridge with:

```bash
npx mcp-remote https://model-router.lee-anthony57.workers.dev/mcp --header "Authorization: Bearer rk_YOUR_KEY"
```
