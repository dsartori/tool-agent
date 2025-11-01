#!/usr/bin/env python3
"""
Main entry point for ToolAgent CLI.
"""

import sys
import argparse
from tool_agent import ToolAgent


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="ToolAgent Demo - AI with Tool Chaining")
    parser.add_argument("--config", default="config.json", help="Configuration file path")
    parser.add_argument("message", nargs="?", help="Message to send (if not provided, enters interactive mode)")
    
    args = parser.parse_args()
    
    # Create demo instance
    demo = ToolAgent(args.config)
    
    # Check if message provided via stdin
    if not sys.stdin.isatty():
        message = sys.stdin.read().strip()
        if message:
            response = demo.chat(message)
            print(response)
        else:
            print("Error: No input provided", file=sys.stderr)
            sys.exit(1)
    elif args.message:
        # Single message mode
        response = demo.chat(args.message)
        print(response)
    else:
        # Interactive mode
        demo.run_interactive()


if __name__ == "__main__":
    main()
