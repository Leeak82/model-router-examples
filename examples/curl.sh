#!/usr/bin/env bash
# Model Router curl examples. Requires ROUTER_KEY and at least one of OPENAI_API_KEY / GROQ_API_KEY.
# Keys are read from the environment and never printed.
#   export ROUTER_KEY=rk_YOUR_KEY OPENAI_API_KEY=sk-YOUR_OPENAI_KEY GROQ_API_KEY=gsk_YOUR_GROQ_KEY
#   bash examples/curl.sh
set -euo pipefail
BASE="${BASE:-https://model-router.lee-anthony57.workers.dev}"
: "${ROUTER_KEY:?Set ROUTER_KEY to your rk_… key (see the README)}"
if [ -z "${OPENAI_API_KEY:-}" ] && [ -z "${GROQ_API_KEY:-}" ]; then
  echo "Set OPENAI_API_KEY and/or GROQ_API_KEY" >&2
  exit 1
fi

AUTH=( -H "Authorization: Bearer ${ROUTER_KEY}" )
KEYS=()
[ -n "${OPENAI_API_KEY:-}" ] && KEYS+=( -H "X-OpenAI-Key: ${OPENAI_API_KEY}" )
[ -n "${GROQ_API_KEY:-}" ] && KEYS+=( -H "X-Groq-Key: ${GROQ_API_KEY}" )
J=( -H "Content-Type: application/json" )
hdr() { grep -i "^$1:" "$2" | head -1 | tr -d '\r'; }

echo "== health"
curl -sS "$BASE/health"
echo

echo "== free-demo (no router or provider key needed)"
curl -sS "$BASE/v1/chat/completions" "${J[@]}" \
  -d '{"model":"free-demo","messages":[{"role":"user","content":"ping"}]}' | jq -r .model,.choices[0].message.content
echo

echo "== auto chat (tiny completion; max_tokens=128 leaves room if the model reasons first)"
code=$(curl -sS "$BASE/v1/chat/completions" -D /tmp/mr-ex-h1 -o /tmp/mr-ex-b1 -w "%{http_code}" "${AUTH[@]}" "${KEYS[@]}" "${J[@]}" \
  -d '{"model":"auto","max_tokens":128,"messages":[{"role":"user","content":"Say the word hello."}]}')
content=$(jq -r '.choices[0].message.content // empty' /tmp/mr-ex-b1 | tr '
' ' ' | sed 's/[[:space:]]*$//')
if [ -z "$content" ]; then content=$(jq -r '.error.message // "(empty content, finish=" + (.choices[0].finish_reason // "?") + ")"' /tmp/mr-ex-b1); fi
echo "HTTP $code  $content"
hdr X-Router-Model /tmp/mr-ex-h1
hdr X-Router-Provider /tmp/mr-ex-h1
hdr X-Router-Route /tmp/mr-ex-h1
hdr X-Router-Intent /tmp/mr-ex-h1
hdr X-Router-Sticky /tmp/mr-ex-h1
hdr X-Router-Est-Cost-USD /tmp/mr-ex-h1
hdr X-Router-Usage /tmp/mr-ex-h1
echo

echo "== preview routing (no model call, no usage)"
curl -sS "$BASE/v1/route?model=auto&prompt=Write+a+Python+regex+function" "${AUTH[@]}" "${KEYS[@]}" \
  | jq '{route,intent,intent_tier,candidates:[.candidates[].model]}'
echo

echo "== sticky session: first call pins, second call should hit"
SESS="example-$(date +%s)"
curl -sS "$BASE/v1/chat/completions" -D /tmp/mr-ex-h2 -o /tmp/mr-ex-b2 "${AUTH[@]}" "${KEYS[@]}" "${J[@]}" \
  -H "X-Router-Session: $SESS" \
  -d '{"model":"auto","max_tokens":128,"messages":[{"role":"user","content":"Write a one-line Python hello function. Reply OK."}]}'
echo "turn 1: $(hdr X-Router-Model /tmp/mr-ex-h2)  $(hdr X-Router-Sticky /tmp/mr-ex-h2)  $(hdr X-Router-Intent /tmp/mr-ex-h2)"
curl -sS "$BASE/v1/chat/completions" -D /tmp/mr-ex-h3 -o /tmp/mr-ex-b3 "${AUTH[@]}" "${KEYS[@]}" "${J[@]}" \
  -H "X-Router-Session: $SESS" \
  -d '{"model":"auto","max_tokens":128,"messages":[{"role":"user","content":"Thanks, one word."}]}'
echo "turn 2: $(hdr X-Router-Model /tmp/mr-ex-h3)  $(hdr X-Router-Sticky /tmp/mr-ex-h3)  $(hdr X-Router-Intent /tmp/mr-ex-h3)"
echo

echo "== usage today"
curl -sS "$BASE/v1/usage" "${AUTH[@]}" | jq '{plan,used,limit,remaining,est_cost_usd}'
echo

echo "== image route without an xAI key (should be 400, no spend)"
code=$(curl -sS -o /tmp/mr-ex-img -w "%{http_code}" "$BASE/v1/images/generations" "${AUTH[@]}" "${J[@]}" \
  -d '{"prompt":"a red cube","n":1,"quality":"low","resolution":"1k"}')
echo "HTTP $code  $(jq -r '.error.message // .' /tmp/mr-ex-img | head -c 200)"
echo
echo "Done. To generate an image you need X-XAI-Key and an xAI account; this script does not call xAI."
rm -f /tmp/mr-ex-h1 /tmp/mr-ex-b1 /tmp/mr-ex-h2 /tmp/mr-ex-b2 /tmp/mr-ex-h3 /tmp/mr-ex-b3 /tmp/mr-ex-img
