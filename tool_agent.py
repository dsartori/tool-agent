"""
ToolAgent Demo - CLI for AI with Tool Chaining
========================================================

A minimal demonstration of AI tool chaining for Hackforge.
Features: OpenAI integration, tool calls, round management, stdin input.
"""

import json
import sys
import os
from simple_tool import FileReaderTool, WebSearchTool, WebFetchTool, CalculatorTool
from typing import Dict, List, Any, Optional
try:
    from openai import OpenAI
except ImportError:
    print("Error: openai package not found. Install with: pip install openai")
    sys.exit(1)


class ToolAgent:
    """Main class for ToolAgent CLI."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.client = OpenAI(
            api_key=os.environ.get("LLM_API_KEY"),
            base_url=os.environ.get("LLM_BASE_URL")
        )
        
        # Initialize tools
        self.tools = {
            "file_reader": FileReaderTool(),
            "web_search": WebSearchTool(),
            "web_fetch": WebFetchTool(),
            "calculator": CalculatorTool()
        }
        
        # Round management
        self.max_rounds = self.config.get("max_rounds", 5)
        self.current_round = 0
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Config file '{config_path}' not found, using defaults")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in config file: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "model": "moonshotai/Kimi-K2-Instruct",
            "temperature": 0.7,
            "system_prompt": "You are a helpful AI assistant with access to tools. Use tools when helpful to provide accurate, current information. If you have already provided a complete answer and no new information is available, respond with exactly '' to signal completion. Do not repeat the same answer multiple times."
,
            "max_rounds": 5
        }
    
    def _show_progress(self, round_num: int, message: str):
        """Show progress indicator."""
        print(f"🔄 Round {round_num}/{self.max_rounds}: {message}")
    
    
    def _execute_tool_calls(self, tool_calls: List[Dict]) -> List[Dict[str, Any]]:
        """Execute tool calls and return results."""
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.get("function", {}).get("name")
            arguments_str = tool_call.get("function", {}).get("arguments", "{}")
            
            try:
                arguments = json.loads(arguments_str)
            except json.JSONDecodeError:
                arguments = {}
            
            if tool_name not in self.tools:
                results.append({
                    "tool_call_id": tool_call.get("id"),
                    "name": tool_name,
                    "content": f"Error: Tool '{tool_name}' not found"
                })
                continue
            
            # Execute the tool
            tool = self.tools[tool_name]
            tool_result = tool.execute(arguments)
            
            print(f"  🛠️  {tool_name}: {arguments.get('path', arguments.get('query', arguments.get('expression', 'executing')))}")
            
            results.append({
                "tool_call_id": tool_call.get("id"),
                "name": tool_name,
                "content": tool_result
            })
        
        return results
    
    def chat(self, message: str) -> str:
        """Main chat function with tool chaining."""
        # Prepare messages
        messages = [
            {"role": "system", "content": self.config["system_prompt"]},
            {"role": "user", "content": message}
        ]
        
        tool_schemas = [tool.get_schema() for tool in self.tools.values()]
        
        for round_num in range(1, self.max_rounds + 1):
            self.current_round = round_num
            
            self._show_progress(round_num, "Thinking...")
            
            try:
                # Call OpenAI Chat Completions API with tool support
                response = self.client.chat.completions.create(
                    model=self.config["model"],           # AI model to use (e.g., gpt-4, gpt-3.5-turbo)
                    messages=messages,                    # Conversation history as list of message dicts
                    temperature=self.config["temperature"], # Randomness (0.0-2.0, lower = more deterministic)
                    tools=tool_schemas,                   # Available tools in OpenAI function calling format
                    tool_choice="auto"                    # Let AI decide whether to call tools ("auto", "none", or specific tool)
                )
            except Exception as e:
                return f"Error calling OpenAI API: {str(e)}"
            
            # Extract the first choice from the response
            # choices is a list of response alternatives (usually just one)
            choice = response.choices[0]
            
            # Get the message object containing the AI's response
            # message contains content, role, and potentially tool_calls
            message_obj = choice.message
            
            # Add assistant response to messages
            assistant_message = {
                "role": "assistant",
                "content": message_obj.content or ""
            }
            
            # Check if the AI wants to call any tools
            # tool_calls is a list of ToolCall objects when the AI decides to use tools
            if hasattr(message_obj, 'tool_calls') and message_obj.tool_calls:
                # Convert tool_calls to the expected format for message history
                # Each tool_call has: id, type, and function (name + arguments)
                assistant_message["tool_calls"] = [
                    {
                        "id": tc.id,           # Unique identifier for this tool call
                        "type": tc.type,       # Always "function" for function calls
                        "function": {
                            "name": tc.function.name,        # Name of the function to call
                            "arguments": tc.function.arguments # JSON string of arguments
                        }
                    }
                    for tc in message_obj.tool_calls
                ]
                
                messages.append(assistant_message)
                
                # Execute tools
                self._show_progress(round_num, "Executing tools...")
                tool_results = self._execute_tool_calls(assistant_message["tool_calls"])
                
                # Add tool results to messages
                for result in tool_results:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": result["tool_call_id"],
                        "name": result["name"],
                        "content": result["content"]
                    })
                
                # Continue to next round
                continue
            else:
                # No tool calls
                messages.append(assistant_message)
                print(f"🤖 Response: {message_obj.content}")
                if not message_obj.content:
                    # Only terminate if there's literally no content
                    return "No response"
        
        # Max rounds reached
        final_content = assistant_message.get("content", "")
        if final_content:
            return final_content + f"\n\n⚠️  Maximum rounds ({self.max_rounds}) reached."
        else:
            return f"⚠️  Maximum rounds ({self.max_rounds}) reached. No final response generated."
    
    def run_interactive(self):
        """Run interactive CLI mode."""
        print("🤖 ToolAgent Demo - AI with Tool Chaining")
        print("Type 'quit' to exit, 'help' for available tools")
        print(f"📊 Max rounds: {self.max_rounds}")
        print()
        
        while True:
            try:
                message = input("> ").strip()
                
                if message.lower() in ['quit', 'exit']:
                    print("👋 Goodbye!")
                    break
                
                if message.lower() == 'help':
                    print("\n🛠️  Available Tools:")
                    for name, tool in self.tools.items():
                        print(f"  • {name}: {tool.description}")
                    print()
                    continue
                
                if message:
                    print()
                    response = self.chat(message)
                    print(f"\n{response}\n")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                break
