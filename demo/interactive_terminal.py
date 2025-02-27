"""
Example demonstrating interactive usage of ExtraTerminal.
This example shows how to:
- Check terminal availability
- Select sessions interactively
- Read screen content
- Send commands
- Handle errors properly
"""

import time
import sys
from py_troya_connect import ExtraTerminal, ExtraTerminalError

def display_menu():
    """Display interactive menu options"""
    print("\nTROYA Terminal Interface")
    print("=" * 30)
    print("1. Read screen content")
    print("2. Send command")
    print("3. System status")
    print("4. Exit")
    return input("\nSelect option (1-4): ").strip()

def main():
    # Check terminal availability
    print("Checking EXTRA terminal availability...")
    available_types = ExtraTerminal.detect_terminal_type()
    
    if not available_types:
        print("Error: EXTRA terminal emulation software not found!")
        sys.exit(1)
    
    try:
        # Interactive session selection
        session_choice = ExtraTerminal.select_session()
        
        # Connect using context manager
        with ExtraTerminal(session_choice) as terminal:
            print(f"\nConnected to session {session_choice}")
            
            while True:
                choice = display_menu()
                
                if choice == "1":
                    # Demonstrate screen reading
                    print("\nCurrent Screen Content:")
                    print("-" * 80)
                    content = terminal.read_screen()
                    print("\n".join(content))
                    print("-" * 80)
                
                elif choice == "2":
                    # Demonstrate command sending
                    command = input("Enter command (e.g. CLEAR, or command{TAB}value): ")
                    terminal.send_command(command)
                    
                    # Show result after small delay
                    time.sleep(1)
                    print("\nScreen after command:")
                    print("-" * 80)
                    print("\n".join(terminal.read_screen()))
                    print("-" * 80)
                
                elif choice == "3":
                    # Show system diagnostic info
                    status = terminal.check_system_status()
                    print("\nSystem Status:")
                    print("-" * 80)
                    for key, value in status.items():
                        print(f"{key}: {value}")
                    print("-" * 80)
                
                elif choice == "4":
                    print("Exiting...")
                    break
                
                else:
                    print("Invalid option, please try again.")

    except ExtraTerminalError as e:
        print(f"Terminal Error: {e}")
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
