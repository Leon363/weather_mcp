def mcp_tool_to_ollama(tool):
    return {
        'type': 'function',
        'function': {
            'name': tool.name,
            'description': tool.description,
            'parameters': tool.input_schema,
        }
    }

def tool_result_text(result):
    return '\n'.join(block.text for block in result.content if hasattr(block, 'text'))