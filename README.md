# Recipe Agents Learning Lab

This deliberately small project shows a complete agentic loop:

1. A FastAPI endpoint accepts a natural-language prompt.
2. A Strands orchestrator must call a deterministic availability tool.
3. It routes supported requests to either a coffee or soup expert agent.
4. The expert returns a recipe and normalized ingredient quantities.
5. A deterministic pricing tool looks up fixed prices and totals the recipe.
6. The orchestrator returns one Pydantic-validated result per requested item.
7. A live trace page shows model turns, context, exposed reasoning blocks,
   tool schemas, tool inputs/results, token usage, stop reasons, and timings.

The application uses your local Ollama instance; no AWS account is needed.
"AWS Strands" is the SDK and can use several model providers, including Ollama.

## Quick start

Python 3.11 or newer is required by the current Strands SDK. With `uv`:

```bash
cp .env.example .env
uv sync
uv run uvicorn recipe_agents.api:app --reload --port 8000
```

Then open:

- API documentation: <http://localhost:8000/docs>
- live application traces: <http://localhost:8000/trace-ui>
- your existing raw Ollama Trace Lab: <http://localhost:8777/>

Try a request:

```bash
curl -s http://localhost:8000/recipes \
  -H 'content-type: application/json' \
  -d '{"prompt":"Give me a simple sweet latte recipe"}' | python -m json.tool
```

The response includes `X-Session-ID` and `X-Turn-ID` headers while the JSON body
wraps the four fields for each requested item in a `recipes` array. This makes
single- and multi-item requests use the same predictable contract:

```json
{
  "recipes": [
    {"item": "coffee", "description": "...", "recipe": "...", "cost": "$0.42 USD"},
    {"item": "soup", "description": "...", "recipe": "...", "cost": "$2.18 USD"}
  ]
}
```

Try both experts in one request with `"Give me a latte and tomato soup"`.
Inspect the headers with `-i`, then
continue the same application session by putting that session ID in the body:

```bash
curl -i http://localhost:8000/recipes \
  -H 'content-type: application/json' \
  -d '{"prompt":"Now make it less sweet","session_id":"X_SESSION_ID_FROM_FIRST_RESPONSE"}'
```

## Expected behavior

The availability tool is intentionally rigid:

| normalized item | answer |
|---|---|
| `coffee` | `coffee:yes` |
| `soup` | `soup:yes` |
| anything else | `<item>:no` |

An unsupported request returns a normal JSON response with a short explanation
and no recipe or cost. Coffee and soup requests are delegated to the matching
expert. Ingredient prices are code, not model guesses, so the model cannot alter
the price table.

## Tracing and the limits of “inner thoughts”

`/trace-ui` watches newline-delimited JSON files written under `traces/`. Each
event contains `session_id`, `turn_id`, agent name, timestamp, and event-specific
data. Content capture can be disabled with `TRACE_CAPTURE_CONTENT=false`.
The browser's SSE connection renews every five seconds. That keeps live updates
continuous while allowing Uvicorn's `--reload` shutdown to finish promptly.

The right-side **Context growth by agent** chart plots provider-reported input
tokens for every model call across the selected session. Each point is labeled
with the change from that agent's previous call, so the orchestrator's growing
history is visually distinct from a newly invoked expert. While a call is still
running, its point is hollow and uses Strands' projected token count; it fills
in when Ollama returns the actual count. The graph stops at the event selected
in the middle column, emphasizes the current growth segment, and names completed
tools observed between the agent's two calls. Click a point to open that
model-call event in the inspector.

Above that graph, compact live gauges follow the selected trace position. They
show completed/started LLM calls and tools, cumulative input/output tokens,
cache-read share, latest time-to-first-token (TTFT), active work, and elapsed
time. Missing provider cache data is labeled `not reported` rather than shown as
zero. During a running step, the elapsed counter updates four times per second.

Within each Request, the center timeline uses one lane per agent. Every model
call shows its offset from the request start and its duration. Calls whose
start/end intervals overlap are assigned to the same timeline row, making
parallel expert work appear side by side; later calls move to the next row.
Keyboard navigation still follows the underlying event timestamps rather than
the visual column order. The two vertical dividers resize the guide, timeline,
and inspector panes by pointer drag or Left/Right while focused; the selected
widths are saved in browser local storage.

The trace records:

- exact system prompts and the full message window sent on each model call;
- exact tool JSON schemas, generated arguments, and returned payloads;
- model streaming events, complete assistant messages, and stop reasons;
- input/output/cache token counts reported by the provider;
- model latency, time to first streamed event, and individual tool duration;
- final structured output and errors.

Ollama reports ordinary input/output totals but does not currently report prompt
cache read/write counts through Strands. The trace keeps the cache keys with
`null` values and an explanatory note instead of pretending a missing count is
zero (a cache miss).

No application can reliably extract a model's private hidden chain-of-thought.
This project records only reasoning/thinking blocks the provider deliberately
returns. It never invents a rationale when one was not exposed. For learning,
tool-selection decisions and intermediate results are usually the more useful,
reproducible evidence.

Your service on port 8777 identifies itself as **Ollama Trace Lab**. It traces a
raw `/api/chat` or `/v1/chat/completions` request submitted through that UI. Its
`/api/trace` request format does not accept Strands tool schemas, so routing the
multi-agent app through it would remove the tool loop. Use it to examine an
isolated prompt/model call; use this project's trace UI for the complete agent
run.

This project sets Ollama `think=false`. With the installed Strands 1.55.1 native
Ollama adapter, Qwen's separate `thinking` stream is not mapped to Strands
reasoning events; leaving it enabled spends the output budget on empty mapped
text chunks. Trace Lab can display that provider-native stream. If a future
Strands provider emits standard reasoning blocks, this app's
`provider_reasoning_delta` event records them automatically.

Strands also emits standard OpenTelemetry spans. To send them to a real
OTLP/HTTP collector, set `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` to the collector's
trace-ingest URL (often `http://host:4318/v1/traces`). Port 8777 is not an OTLP
collector and should not be configured as that endpoint.

## Source map

- `api.py`: HTTP endpoints, session lookup, and trace UI.
- `agents.py`: specialist agents, tool definitions, and orchestrator prompt.
- `service.py`: one request/turn lifecycle and Pydantic validation.
- `tracing.py`: JSONL trace sink and Strands lifecycle hooks.
- `pricing.py`: deterministic ingredient price table and cost calculator.
- `schemas.py`: all public and internal data contracts.
- `prompts.py`: raw prompts in one place so they are easy to study.

## Run tests

```bash
uv run pytest
```

The unit tests do not need Ollama. An optional manual smoke test is:

```bash
uv run python scripts/smoke_test.py
```

## Useful learning experiments

Change one thing at a time, make a request, and compare the trace:

1. Make a tool description vague and observe tool selection.
2. Lower `MAX_AGENT_TURNS` and provoke a tool loop.
3. Ask for an unsupported item and verify that no expert is called.
4. Remove an ingredient price and observe the explicit `unknown` line item.
5. Disable history in `service.py` and compare the second turn's context.

## Production cautions

This is teaching code, not a production recipe service. Prompt and message
capture can contain sensitive data; disable it or add redaction before handling
real user content. JSONL files are process-local, session memory is in-process,
and there is no authentication, rate limiting, persistent database, or distributed
trace storage.
