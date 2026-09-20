import uuid

import pytest

from src.services.realtime_service import ConnectionManager


@pytest.mark.asyncio
async def test_websocket_ticket_is_single_use() -> None:
    manager = ConnectionManager()
    user_id = uuid.uuid4()

    ticket = await manager.issue_ticket(user_id)

    assert await manager.consume_ticket(ticket) == user_id
    assert await manager.consume_ticket(ticket) is None


@pytest.mark.asyncio
async def test_invalid_websocket_ticket_is_rejected() -> None:
    manager = ConnectionManager()

    assert await manager.consume_ticket("not-a-valid-ticket") is None
