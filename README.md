# Tool Agent Demo - AI with Tool Chaining

A simplified demonstration of AI tool chaining for Hackforge. This minimal CLI shows how AI assistants can use external tools to perform complex tasks through multi-round conversations.

## Features

- 🤖 **OpenAI Integration** - Connects to OpenAI API for intelligent responses
- 🛠️ **Tool Calling** - AI can call external tools to get real-time information
- 🔗 **Tool Chaining** - Multiple rounds of tool usage for complex tasks
- 📊 **Round Management** - Simple round limits with progress indicators
- 💬 **Interactive CLI** - Command-line interface with stdin support
- ⚙️ **Simple Configuration** - JSON-based configuration

## Included Tools

1. **File Reader** - Read and analyze text files
2. **Web Search** - Search the web using DuckDuckGo (ddgs)
3. **Web Fetch** - Fetch and extract content from web pages
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
python tool-agent.py

# Single message mode
python tool-agent.py "Read the README.md file and summarize it"

# Using stdin
echo "Calculate 25 * 4 + 10" | python tool-agent.py

# Custom config file
python tool-agent.py --config my-config.json "Search for AI news"
```

## Demo Examples

### Example 1: File Analysis
```bash
> Read the config.json file and explain the settings
🔄 Round 1/5: Thinking...
🔄 Round 1/5: Executing tools...
  🛠️  file_reader: config.json
🔄 Round 2/5: Thinking...
✅ Complete!

The config.json file contains these settings:
- Model: gpt-3.5-turbo
- Temperature: 0.7 (moderate creativity)
- Max rounds: 5 (limits conversation rounds)
- System prompt: Guides the AI to use tools helpfully
```

### Example 2: Tool Chaining
```bash
> Read the README.md file and then search for recent updates about this project
🔄 Round 1/5: Thinking...
🔄 Round 1/5: Executing tools...
  🛠️  file_reader: README.md
🔄 Round 2/5: Thinking...
🔄 Round 2/5: Executing tools...
  🛠️  web_search: Pinloom CLI updates 2024
🔄 Round 3/5: Thinking...
✅ Complete!

Based on the README and web search, here's what I found...
```

### Example 3: Calculation + Analysis
```bash
> Calculate the total lines in this directory and then search for similar projects
🔄 Round 1/5: Thinking...
🔄 Round 1/5: Executing tools...
  🛠️  calculator: 25 + 42 + 18
🔄 Round 2/5: Thinking...
🔄 Round 2/5: Executing tools...
  🛠️  web_search: AI CLI tool chaining projects
🔄 Round 3/5: Thinking...
✅ Complete!

The total is 85 lines. Here are similar projects I found...
```

## Configuration

Edit `config.json` to customize the demo:

```json
{
  "model": "gpt-3.5-turbo",           // OpenAI model to use
  "temperature": 0.7,                  // 0.0 = deterministic, 1.0 = creative
  "system_prompt": "You are...",       // AI behavior instructions
  "max_rounds": 5                      // Maximum conversation rounds
}
```

### Alternative Models
```json
{
  "model": "gpt-4",
  "temperature": 0.5,
  "system_prompt": "You are an expert AI assistant...",
  "max_rounds": 8
}
```

### Custom OpenAI-Compatible Endpoints
```json
{
  "model": "claude-3-haiku",
  "temperature": 0.7,
  "system_prompt": "You are Claude...",
  "max_rounds": 5
}
```

## Tech Talk Talking Points

### 1. Tool Calling Architecture
- Show how the AI receives tool schemas
- Demonstrate function calling with parameters
- Explain the request/response cycle

### 2. Round Management
- Demonstrate multi-round conversations
- Show progress indicators
- Explain loop detection and safety

### 3. Tool Chaining
- Show how tools can be used sequentially
- Demonstrate how AI synthesizes results
- Explain the power of combining tools

### 4. Security & Safety
- Path validation in file reader
- Input sanitization in calculator
- Round limits to prevent infinite loops

## File Structure

```
demo/
├── tool-agent.py    # Main script (300 lines)
├── config.json        # Configuration file
└── README.md          # This file
```

All functionality is contained in the single `tool-agent.py` file for easy portability and understanding.

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

## Extending the Demo

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

Then add it to the tools dictionary in `PinloomDemo.__init__()`.

## License

This demo is for educational purposes. Feel free to use and modify for your tech talks and presentations.
