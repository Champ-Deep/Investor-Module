from datetime import date

import asyncpg
import pytest

from cadence.config import get_settings


@pytest.fixture
def settings():
    return get_settings()


@pytest.fixture
def today():
    # The seed universe is built relative to this fixed date.
    return date(2026, 6, 3)


@pytest.fixture
async def conn():
    s = get_settings()
    c = await asyncpg.connect(dsn=s.database_url)
    try:
        yield c
    finally:
        await c.close()
