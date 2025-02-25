# py-troya-connect

A Python interface for Attachmate Extra Terminal sessions.

## Installation

```bash
pip install py-troya-connect
```

## Usage

```python
from py_troya_connect import ExtraTerminal

# Try basic operations
# Connect to a session
with ExtraTerminal("1") as terminal:
    # Send a command
    terminal.send_command("your command")
    
    # Read screen content
    screen_content = terminal.read_screen()
    for line in screen_content:
        print(line)
        
    # Wait for specific text
    if terminal.wait_for_text("Expected text", timeout=30):
        print("Text found!")
```

## Features

- Connect to Extra Terminal sessions
- Send commands
- Read screen content
- Wait for specific text to appear
- List available sessions

## Requirements

- Windows OS
- Attachmate Extra! Terminal
- Python 3.6+
- pywin32

## License

MIT License
