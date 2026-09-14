import pytest

from recipe_agents import api


class DisconnectedRequest:
    async def is_disconnected(self) -> bool:
        return True


@pytest.mark.asyncio
async def test_trace_stream_has_a_short_renewable_lease(monkeypatch) -> None:
    monkeypatch.setattr(api, "TRACE_STREAM_LEASE_SECONDS", 0.0)

    response = await api.stream_trace("session_123", DisconnectedRequest(), None)
    chunks = [chunk async for chunk in response.body_iterator]

    assert chunks == ["retry: 250\n\n"]
    assert response.headers["cache-control"] == "no-cache"
