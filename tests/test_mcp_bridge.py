from types import SimpleNamespace

from mcp_bridge import mcp_tool_to_ollama, tool_result_text


def test_mcp_tool_to_ollama_maps_tool_fields():
    tool = SimpleNamespace(
        name='get_weather',
        description='Current weather for a city',
        inputSchema={
            'type': 'object',
            'properties': {'city': {'type': 'string'}},
            'required': ['city'],
        },
    )

    assert mcp_tool_to_ollama(tool) == {
        'type': 'function',
        'function': {
            'name': 'get_weather',
            'description': 'Current weather for a city',
            'parameters': {
                'type': 'object',
                'properties': {'city': {'type': 'string'}},
                'required': ['city'],
            },
        },
    }


def test_tool_result_text_joins_text_blocks():
    result = SimpleNamespace(content=[
        SimpleNamespace(text='Weather in Berlin'),
        SimpleNamespace(text='Humidity is 91%'),
    ])

    assert tool_result_text(result) == 'Weather in Berlin\nHumidity is 91%'


def test_tool_result_text_skips_blocks_without_text():
    result = SimpleNamespace(content=[
        SimpleNamespace(text='kept'),
        SimpleNamespace(blob=b'image'),
        SimpleNamespace(text='also kept'),
    ])

    assert tool_result_text(result) == 'kept\nalso kept'


def test_tool_result_text_is_empty_when_there_are_no_blocks():
    assert tool_result_text(SimpleNamespace(content=[])) == ''
