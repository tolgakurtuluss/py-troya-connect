# py-troya-connect

'py-troya-connect' is a Python framework for interacting with Attachmate Extra! X-treme based Troya terminal sessions.

## Installation

```bash
pip install py-troya-connect
```

## Quick Start

```python
from py_troya_connect import ExtraTerminal

# Interactive session selection
session = ExtraTerminal.select_session()
terminal = ExtraTerminal(session)
terminal.connect()

# Basic screen operations
screen_content = terminal.read_screen()
print(screen_content)

terminal.disconnect()
```

## Key Features

### Session Management

```python
# List all available sessions
terminal = ExtraTerminal("1")
sessions = terminal.list_available_sessions()
for session in sessions:
    print(f"Session {session['index']}: {session['name']} - {'Connected' if session['connected'] else 'Disconnected'}")

# Interactive session selection
session = ExtraTerminal.select_session()
terminal = ExtraTerminal(session)
```

### Terminal Operations

```python
with ExtraTerminal("1") as terminal:
    # Send command with automatic formatting
    terminal.send_command("CLEAR")  # Automatically adds <ENTER>
    
    # Send complex commands with special keys
    terminal.send_command("USER123{TAB}PASS456{ENTER}")
    
    # Read screen content
    screen = terminal.read_screen(strip_whitespace=True)
    print(screen)
    
    # Wait for specific text to appear
    if terminal.wait_for_text("READY", timeout=30):
        terminal.send_command("NEXT_COMMAND")
```

### Output Management

```python
from py_troya_connect import ExtraTerminal

# Basic connection
terminal = ExtraTerminal("1")  # Connect to first session
terminal.connect()

# Send a command and read response
terminal.send_command("A10JANISTESB")

# First option : Bulk output
screen = terminal.read_screen(strip_whitespace=True)
print(screen)

# Second option : Stripped by row output
screen = terminal.read_screen(strip_whitespace=False)
print(screen)

'strip_whitespace (bool): If True, returns list of stripped lines. If False, returns raw screen content. Defaults to True.'
```

### Error Handling

```python
from py_troya_connect import ExtraTerminalError, ConnectionError, SessionError

try:
    terminal = ExtraTerminal("1")
    terminal.connect()
except ConnectionError as e:
    print(f"Connection failed: {e.message}")
    print(f"Error code: {e.error_code}")
    print(f"Details: {e.details}")
except SessionError as e:
    print(f"Session error: {e.message}")
```

### System Diagnostics

```python
# Check terminal status
terminal = ExtraTerminal("1")
status = terminal.check_system_status()

print(f"Extra Version: {status['Extra Version']}")
print(f"Total Sessions: {status['Session Count']}")
print(f"Available Sessions: {', '.join(status['Available Sessions'])}")
```

### Interactive Usage

```python
# Built-in interactive mode
if __name__ == "__main__":
    session = ExtraTerminal.select_session()
    with ExtraTerminal(session) as terminal:
        while True:
            command = input("Enter command (or 'exit'): ")
            if command.lower() == 'exit':
                break
            terminal.send_command(command)
            print(terminal.read_screen())
```

## Requirements

- Windows OS
- Attachmate Extra! X-treme terminal
- Python 3.6+
- pywin32

## License

MIT License
