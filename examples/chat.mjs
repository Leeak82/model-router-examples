#!/usr/bin/env node
// Chat Completions via the official OpenAI Node SDK, pointed at Model Router.
//   export ROUTER_KEY=rk_YOUR_KEY
//   export OPENAI_API_KEY=sk-YOUR_OPENAI_KEY   // and/or GROQ_API_KEY=gsk_YOUR_GROQ_KEY
//   cd examples && npm install && node chat.mjs

import OpenAI from "openai";

const baseURL = (process.env.BASE || "https://model-router.lee-anthony57.workers.dev") + "/v1";
const apiKey = process.env.ROUTER_KEY;
if (!apiKey) {
  console.error("Set ROUTER_KEY to your rk_… key (see the README)");
  process.exit(1);
}

const defaultHeaders = {};
if (process.env.OPENAI_API_KEY) defaultHeaders["X-OpenAI-Key"] = process.env.OPENAI_API_KEY;
if (process.env.GROQ_API_KEY) defaultHeaders["X-Groq-Key"] = process.env.GROQ_API_KEY;
if (!Object.keys(defaultHeaders).length) {
  console.error("Set OPENAI_API_KEY and/or GROQ_API_KEY");
  process.exit(1);
}

const client = new OpenAI({ baseURL, apiKey, defaultHeaders });

function printHeaders(response) {
  const names = [
    "x-router-model",
    "x-router-provider",
    "x-router-route",
    "x-router-intent",
    "x-router-sticky",
    "x-router-est-cost-usd",
    "x-router-usage",
  ];
  for (const n of names) {
    const v = response.headers.get(n);
    if (v) console.log(`  ${n}: ${v}`);
  }
}

const raw1 = await client.chat.completions
  .create({
    model: "auto",
    max_tokens: 128,
    messages: [{ role: "user", content: "Say the word hello." }],
  })
  .withResponse();

console.log("== auto chat");
console.log("assistant:", (raw1.data.choices[0].message.content || "").trim());
printHeaders(raw1.response);

const session = "node-example-" + Date.now();
const t1 = await client.chat.completions
  .create(
    {
      model: "auto",
      max_tokens: 128,
      messages: [{ role: "user", content: "Write a one-line Python hello function. Reply OK." }],
    },
    { headers: { "X-Router-Session": session } },
  )
  .withResponse();

console.log("\n== sticky session");
console.log(
  "turn 1:",
  (t1.data.choices[0].message.content || "").trim(),
  "|",
  t1.response.headers.get("x-router-model"),
  t1.response.headers.get("x-router-sticky"),
);

const t2 = await client.chat.completions
  .create(
    {
      model: "auto",
      max_tokens: 128,
      messages: [{ role: "user", content: "Thanks, one word." }],
    },
    { headers: { "X-Router-Session": session } },
  )
  .withResponse();

console.log(
  "turn 2:",
  (t2.data.choices[0].message.content || "").trim(),
  "|",
  t2.response.headers.get("x-router-model"),
  t2.response.headers.get("x-router-sticky"),
);
