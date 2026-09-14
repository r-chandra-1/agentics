"""FastAPI transport for the recipe-agent learning lab."""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import AsyncIterator

import httpx
from fastapi import FastAPI, Header, HTTPException, Query, Response
from fastapi.responses import HTMLResponse, StreamingResponse

from recipe_agents.config import get_settings
from recipe_agents.schemas import HealthResponse, RecipeBatchResponse, RecipeRequest
from recipe_agents.service import RecipeService, RecipeServiceError
from recipe_agents.trace_ui import TRACE_UI_HTML
from recipe_agents.tracing import TraceRecorder, configure_otel


settings = get_settings()
configure_otel(settings.otel_exporter_otlp_traces_endpoint)
recorder = TraceRecorder(settings.trace_directory, settings.trace_capture_content)
service = RecipeService(settings, recorder)

app = FastAPI(
    title="Recipe Agents Learning Lab",
    version="0.2.0",
    description=(
        "A small observable Strands multi-agent system. Use POST /recipes, then open /trace-ui "
        "to study each model turn, context window, tool call, and metric."
    ),
)


@app.get("/health", response_model=HealthResponse, tags=["operations"])
async def health() -> HealthResponse:
    """Verify the configured Ollama server, not merely the web process."""

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{settings.ollama_host.rstrip('/')}/api/version")
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Ollama is unavailable: {exc}") from exc
    return HealthResponse(model=settings.ollama_model, ollama_host=settings.ollama_host)


@app.post("/recipes", response_model=RecipeBatchResponse, tags=["recipes"])
async def create_recipe(request: RecipeRequest, response: Response) -> RecipeBatchResponse:
    """Run one observable orchestration turn and return one result per requested item.

    Session metadata lives in response headers so it does not pollute the requested
    recipe batch. Send `X-Session-ID` back in the next request body's `session_id`
    to preserve conversation history.
    """

    try:
        result = await service.create_recipe(request.prompt, request.session_id)
    except RecipeServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    response.headers["X-Session-ID"] = result.session_id
    response.headers["X-Turn-ID"] = result.turn_id
    response.headers["X-Trace-URL"] = f"/trace-ui?session={result.session_id}"
    return result.response


@app.get("/traces", tags=["tracing"])
async def list_traces() -> list[dict]:
    """List local trace sessions, newest first."""

    return recorder.sessions()


def _valid_session_id(session_id: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,80}|unscoped", session_id):
        raise HTTPException(status_code=400, detail="Invalid session id.")
    return session_id


@app.get("/traces/{session_id}", tags=["tracing"])
async def read_trace(session_id: str, after: int = Query(default=0, ge=0)) -> list[dict]:
    """Read trace events as ordinary JSON (handy for curl and tests)."""

    return recorder.read(_valid_session_id(session_id), after)


@app.get("/traces/{session_id}/stream", tags=["tracing"])
async def stream_trace(
    session_id: str,
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
) -> StreamingResponse:
    """Tail a session via Server-Sent Events for the live browser view."""

    safe_id = _valid_session_id(session_id)
    try:
        start = int(last_event_id) + 1 if last_event_id is not None else 0
    except ValueError:
        start = 0

    async def event_source() -> AsyncIterator[str]:
        offset = start
        while True:
            batch = recorder.read(safe_id, offset)
            for event in batch:
                yield f"id: {offset}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
                offset += 1
            await asyncio.sleep(0.25)

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/trace-ui", response_class=HTMLResponse, include_in_schema=False)
async def trace_ui() -> str:
    """Serve the zero-build trace viewer."""

    return TRACE_UI_HTML
