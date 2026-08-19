# ClearGlassInc Agent SDK

A clean, modular Python framework for building tool-using LLM agents:
instructions + state + tool-calling (`Agent`), schema-described function
tools (`Tool`), short/long-term context (`Memory`), pluggable validation
(`Guardrails`), and provider-agnostic execution with sync/async/streaming
support (`Runner` + `LLMClient` adapters).

It ships with zero hard dependencies — provider SDKs (`openai`, `anthropic`)
and HTTP-based connectors (`httpx`) are optional extras, so the core package
installs and runs anywhere.

## Install

```bash
pip install -e .                 # core SDK only
pip install -e ".[openai]"       # + OpenAI client
pip install -e ".[anthropic]"    # + Anthropic client
pip install -e ".[http]"         # + GitHub/Slack/Outlook connectors
pip install -e ".[all]"          # everything
pip install -e ".[dev]"          # + pytest/ruff for development
```

## Quickstart

```python
from clearglassinc_sdk import Agent, Runner, tool
from clearglassinc_sdk.clients.openai_client import OpenAIClient

@tool(description="Adds two numbers")
def add(a: int, b: int) -> int:
    return a + b

agent = Agent(
    name="ClearGlassInc Agent",
    instructions="You are a high-performance, futuristic automation agent.",
)
agent.add_tool(add)

runner = Runner(agent, OpenAIClient(model="gpt-4o-mini"))
result = runner.run("What is 21 plus 21?")
print(result.output)
```

Swap `OpenAIClient` for `AnthropicClient` (`clearglassinc_sdk.clients.anthropic_client`)
to change providers — the `Agent`/`Runner`/`Tool` code above doesn't change.

Run the bundled examples (no API key required — they use a scripted
`FakeLLMClient`):

```bash
python examples/hello_agent.py
python examples/streaming_agent.py
python examples/advanced_agent.py   # tracing, schemas, retries, sessions, delegation
```

## Components

| Module | Purpose |
|---|---|
| `agent.py` | `Agent` — instructions, tools, guardrails, memory, schema, retry policy |
| `tools.py` | `Tool` / `@tool` — wrap functions with JSON-schema function-calling metadata |
| `memory.py` | `Memory` — bounded short-term history + pluggable `LongTermStore` |
| `guardrails.py` | `Guardrail` protocol + built-ins (`MaxLengthGuardrail`, `RegexBlocklistGuardrail`, `RequiredKeywordsGuardrail`) |
| `runner.py` | `Runner` — drives the tool-calling loop; sync/async, streaming/non-streaming |
| `tracing.py` | `Tracer`, `Span`, `Usage` + console/JSONL/in-memory exporters |
| `retry.py` | `RetryPolicy` — exponential backoff with jitter, transient-error classification |
| `structured.py` | `OutputSchema` — JSON-schema-constrained answers with a repair loop |
| `sessions.py` | `SessionStore` — in-memory and durable file-backed conversation persistence |
| `handoff.py` | `Handoff` / `build_supervisor` — multi-agent delegation (agent-as-tool) |
| `clients/base.py` | `LLMClient` — provider-agnostic contract (`complete`/`acomplete`/`stream`/`astream`) |
| `clients/openai_client.py` | OpenAI Chat Completions adapter (true token streaming) |
| `clients/anthropic_client.py` | Anthropic Messages adapter (true token streaming) |
| `connectors/` | `GitHubConnector`, `SlackConnector`, `OutlookConnector` — external systems as `Tool` lists |
| `server.py` | Deployable FastAPI app — `/run`, `/run/stream` (SSE), `/sessions`, `/traces` |
| `testing.py` | `FakeLLMClient`, `ChunkedFakeLLMClient`, `FlakyLLMClient` — offline LLM doubles |
| `cli.py` | `clearglassinc chat` / `clearglassinc version` |

## Streaming

```python
for chunk in runner.run_stream("Summarize the last deploy."):
    print(chunk.delta, end="", flush=True)
```

`arun_stream` is the async equivalent. Adapters that don't implement true
token streaming fall back to a single chunk carrying the full response, so
calling code never has to special-case providers.

## Guardrails

```python
from clearglassinc_sdk.guardrails import MaxLengthGuardrail, RegexBlocklistGuardrail

agent.output_guardrails = [
    MaxLengthGuardrail(max_chars=2000),
    RegexBlocklistGuardrail(patterns=[r"sk-[A-Za-z0-9]{20,}"]),  # e.g. leaked API keys
]
```

A failing guardrail raises `GuardrailViolation` from `Runner.run`/`arun` —
catch it at the call site to show a safe fallback message.

## Structured output

Constrain the final answer to a JSON schema. On a malformed reply the runner
feeds the validation error back to the model and retries, up to
`max_repair_attempts`.

```python
from clearglassinc_sdk import OutputSchema

agent.output_schema = OutputSchema(
    name="triage",
    schema={
        "type": "object",
        "properties": {"severity": {"type": "string", "enum": ["low", "high"]}},
        "required": ["severity"],
    },
)

result = runner.run("Checkout returns 500 for all users.")
result.structured_output   # {"severity": "high"} — parsed and validated
result.repair_attempts     # how many corrections it took
```

## Tracing and token accounting

Every run emits a span tree (`run` → `step` → `llm`/`tool`/`guardrail`) with
timings, token usage, and errors.

```python
from clearglassinc_sdk import ConsoleExporter, InMemoryExporter, Runner, Tracer

collector = InMemoryExporter()
runner = Runner(agent, client, tracer=Tracer(exporters=[collector, ConsoleExporter()]))
result = runner.run("Where is order A-42?")

result.usage.to_dict()          # {'input_tokens': 120, 'output_tokens': 18, ...}
result.trace_id                 # correlate with your logs
collector.by_kind("tool")       # every tool call, with duration and errors
```

Ship traces anywhere by implementing `SpanExporter`, or use the built-in
`JSONLExporter(path=...)`.

## Retries

Transient provider failures (429s, 5xx, connection resets, timeouts) are
retried with exponential backoff and jitter; terminal errors (auth, bad
request) are raised immediately rather than burning the budget.

```python
from clearglassinc_sdk import RetryPolicy

agent.retry_policy = RetryPolicy(max_attempts=4, base_delay=0.5, max_delay=8.0)
```

## Sessions

Persist and resume conversations across processes.

```python
from clearglassinc_sdk import FileSessionStore, Runner

store = FileSessionStore(directory="./sessions")
runner = Runner(agent, client, session_store=store, session_id="user-42")
runner.run("My name is Desmond.")
# ...later, in a fresh process, with a brand-new Agent object:
Runner(Agent(...), client, session_store=store, session_id="user-42").run("What's my name?")
```

Swap in any backend by implementing the `SessionStore` protocol.

## Multi-agent delegation

Expose a specialist agent as a tool so a supervisor can route work to it.

```python
from clearglassinc_sdk import Handoff, build_supervisor

researcher = Agent(name="Researcher", instructions="You research topics deeply.")

supervisor = build_supervisor(
    name="Supervisor",
    instructions="You coordinate specialists.",
    handoffs=[Handoff(agent=researcher, llm_client=client)],
)
Runner(supervisor, client).run("How fast is the market growing?")
```

## Connectors

```python
from clearglassinc_sdk.connectors import GitHubConnector

github = GitHubConnector(token=os.environ["GITHUB_TOKEN"])
agent.add_tools(github.as_tools())
```

## Deploying

The SDK ships a FastAPI server and a container that runs it:

```bash
cd clearglassinc_sdk
docker compose up --build          # offline fake provider, no API key needed
curl localhost:8000/health
```

| Method | Path | Purpose |
|---|---|---|
| GET | `/health`, `/ready` | Liveness and readiness (open, for load balancers) |
| POST | `/run` | Run a turn — returns output, steps, usage, trace id |
| POST | `/run/stream` | Same, as Server-Sent Events |
| GET/DELETE | `/sessions[/{id}]` | Manage persisted conversations |
| GET | `/traces` | Recent spans, for debugging |

Set `CLEARGLASS_API_KEY` to require `Authorization: Bearer <key>` on every
mutating endpoint. With `CLEARGLASS_ENV=production` and no key set, the app
**refuses to start** rather than silently serving an unauthenticated agent.

Full configuration reference, deploy paths (Compose / registry / PaaS), and
the operational checklist are in [DEPLOY.md](DEPLOY.md).

## Testing

```bash
pip install -e ".[dev,server,all]"
pytest
```

160 tests, all offline — no network access or API keys needed. 18 of them
exercise the OpenAI/Anthropic translation layer against the real SDKs (with
dummy keys); they skip cleanly if you installed without the `all` extra.

To run everything CI runs — the lint/test matrix across each installed Python,
the examples, the CLI, and the container checks — without pushing:

```bash
./scripts/verify.sh              # every interpreter found
./scripts/verify.sh 3.11 3.12    # specific ones
```

It exits non-zero if any leg fails, so it's safe to gate on. When no Docker
daemon is reachable it falls back to exercising what the Dockerfile actually
does — wheel build, offline install, and the image's own `HEALTHCHECK` probe —
instead of skipping the container entirely. This is the fallback to reach for
whenever Actions can't run a change.
`Agent SDK CI` runs lint, the suite on Python 3.11 and 3.12, the examples, a
container build, and a live `/health` probe on every PR.

## CLI

```bash
export CLEARGLASS_PROVIDER=openai   # or anthropic; defaults to an offline fake client
export OPENAI_API_KEY=sk-...
clearglassinc chat
```
