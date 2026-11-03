import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault('WEATHER_API_KEY', 'test-key')

import httpx
import pytest

import mcp_server
from mcp_server import get_weather

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FakeAsyncClient:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.url = None
        self.params = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None):
        self.url = url
        self.params = params
        if self.error is not None:
            raise self.error
        return self.response


def weather_response(status_code, payload=None):
    return httpx.Response(
        status_code,
        json=payload or {},
        request=httpx.Request('GET', mcp_server.URL),
    )


def test_server_requires_api_key():
    env = os.environ.copy()
    env.pop('WEATHER_API_KEY', None)
    result = subprocess.run(
        [sys.executable, '-c', 'import mcp_server'],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert 'API_KEY is not set' in result.stderr


async def test_get_weather_tool_is_registered():
    tools = await mcp_server.mcp.list_tools()

    assert [tool.name for tool in tools] == ['get_weather']


async def test_get_weather_returns_forecast(monkeypatch):
    client = FakeAsyncClient(response=weather_response(200, {
        'name': 'Berlin',
        'sys': {'country': 'DE'},
        'main': {'temp': 4.47, 'humidity': 91},
        'wind': {'speed': 2.57},
    }))
    monkeypatch.setattr(mcp_server.httpx, 'AsyncClient', lambda timeout: client)

    text = await get_weather('Berlin')

    assert client.url == mcp_server.URL
    assert client.params == {
        'appid': mcp_server.WEATHER_API_KEY,
        'q': 'Berlin',
        'units': 'metric',
    }
    assert text == (
        'Weather in Berlin (DE): '
        'temperature is 4.47°C'
        'speed of wind: 2.57 kph, Humidity is 91%'
    )


async def test_get_weather_reports_unknown_city(monkeypatch):
    client = FakeAsyncClient(response=weather_response(400, {'cod': '400', 'message': 'Nothing to geocode'}))
    monkeypatch.setattr(mcp_server.httpx, 'AsyncClient', lambda timeout: client)

    assert await get_weather('Nowhere') == 'Nowhere is not a recognized city'


async def test_get_weather_reports_network_error(monkeypatch):
    client = FakeAsyncClient(error=httpx.ConnectError('offline'))
    monkeypatch.setattr(mcp_server.httpx, 'AsyncClient', lambda timeout: client)

    assert await get_weather('Berlin') == 'Could not reach the weather service to check Berlin'


async def test_get_weather_raises_on_http_error(monkeypatch):
    client = FakeAsyncClient(response=weather_response(401, {'message': 'Invalid API key'}))
    monkeypatch.setattr(mcp_server.httpx, 'AsyncClient', lambda timeout: client)

    with pytest.raises(httpx.HTTPStatusError):
        await get_weather('Berlin')
