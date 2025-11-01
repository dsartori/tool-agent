# Tool Agent Demo - AI with Tool Chaining

A simple demonstration of AI tool chaining for Hackforge. This minimal CLI shows how AI agents use external tools to perform complex tasks through multi-round conversations.

## Features

- 🤖 **LLM Integration** - Connects to any OpenAI-compatible API
- 🛠️ **Tool Calling** - AI can call external tools to get real-time information
- 🔗 **Tool Chaining** - Multiple rounds of tool usage for complex tasks
- 📊 **Round Management** - Simple round limits with progress indicators
- 💬 **Interactive CLI** - Command-line interface with stdin support

## Included Tools

1. **File Reader** - Read and analyze text files
2. **Web Search** - Search the web 
3. **Web Fetch** - Fetch and extract web content
4. **Calculator** - Perform mathematical calculations

## Quick Start

### 1. Prerequisites

```bash
# Install Python 3.8+ if not already installed
python --version

# Install required packages
pip install openai ddgs beautifulsoup4 requests
```

### 2. Set up API Key

```bash
# Set your OpenAI API key
export LLM_API_KEY="your-api-key-here"

# Optional: Use a different OpenAI-compatible endpoint
export LLM_BASE_URL="https://api.openai.com/v1"
```

### 3. Run the Demo

```bash
# Interactive mode (default)
python main.py

# Single message mode
python main.py "Read the README.md file and summarize it"

# Using stdin
echo "Calculate 25 * 4 + 10" | python main.py

# Custom config file
python main.py --config my-config.json "Search for AI news"
```


## Configuration

Edit `config.json` to customize the demo:

```json
{
  "model": "gpt-3.5-turbo",           // LLM to use
  "temperature": 0.7,                  // 0.0 = deterministic, 1.0 = creative
  "system_prompt": "You are...",       // AI behavior instructions
  "max_rounds": 5                      // Maximum conversation rounds
}
```

## File Structure

```
tool-agent/
├── main.py              # Main entry point
├── tool_agent.py         # ToolAgent class
├── simple_tool.py       # Base tool class and implementations
├── validate_tools.py   # Validation utilities
├── config.json          # Configuration file
└── README.md            # Documentation
```

All functionality is contained in the modular files shown above.

## Command Reference

### Interactive Commands
- `help` - Show available tools
- `quit` or `exit` - Exit the demo
- Any text - Send message to AI

### Command Line Options
```bash
python tool-agent.py [OPTIONS] [MESSAGE]

Options:
  --config FILE    Configuration file (default: config.json)
  --help           Show help message

Arguments:
  MESSAGE         Single message to process (optional)
```

### Input Methods
1. **Interactive** - Default mode, type messages directly
2. **Argument** - Pass message as command line argument
3. **Stdin** - Pipe input from other commands
4. **File** - Redirect file content to stdin

## Using as a Module

Importing ToolAgent as a library in other programs:

```python
from tool_agent import ToolAgent
from simple_tool import FileReaderTool, WebSearchTool

# Create agent instance
agent = ToolAgent("config.json")

# Use programmatically
response = agent.chat("Search for Python tutorials")
print(response)

# Access tools directly
file_tool = FileReaderTool()
content = file_tool.execute({"path": "example.txt"})
```

## Extending the Demo

### Limitations

This demo is intentionally minimal. Be aware of these limitations:

- Tool Reliability: No retries or fallbacks if a tool fails. 
- Security: No input validation or rate limiting.
- Cost Control: No token or cost tracking. 
- Configuration: Tools are hard-coded. 
- Observability: No logging or metrics. 

### Adding Tools

To add new tools, create a class inheriting from `SimpleTool`:

```python
class MyTool(SimpleTool):
    def __init__(self):
        super().__init__("my_tool", "Description of my tool")
    
    def execute(self, arguments):
        # Implement your tool logic here
        return "Tool result"
    
    def get_schema(self):
        # Define the tool schema for the AI
        return {
            "type": "function",
            "function": {
                "name": "my_tool",
                "description": "Description of my tool",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string", "description": "Parameter description"}
                    },
                    "required": ["param1"]
                }
            }
        }
```

Then add it to the tools dictionary in `ToolAgent.__init__()`.

## License

MIT
