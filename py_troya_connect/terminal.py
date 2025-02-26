import win32com.client
import pythoncom
import time
from typing import Optional, Dict, Any
from enum import Enum

class TerminalType(Enum):
    EXTRA = "EXTRA.System"
    HIS = "MSHISServer.Session"
    NETMANAGE = "NetManage.Connection.1"

class ExtraTerminalError(Exception):
    """Base exception class for ExtraTerminal errors."""
    def __init__(self, message: str, error_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code or 0
        self.details = details or {}
        super().__init__(self.format_error())
    
    def format_error(self) -> str:
        """Format error message with details"""
        error_msg = f"[Error {self.error_code}] {self.message}"
        if self.details:
            error_msg += "\nDetails:"
            for key, value in self.details.items():
                error_msg += f"\n- {key}: {value}"
        return error_msg

class ConnectionError(ExtraTerminalError):
    """Raised when connection to terminal fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 1001, details)

class SessionError(ExtraTerminalError):
    """Raised when session operations fail"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 1002, details)

class TerminalBusyError(ExtraTerminalError):
    """Raised when terminal is busy"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 1003, details)

class CommandError(ExtraTerminalError):
    """Raised when command execution fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 1004, details)

class ExtraTerminal:
    """
    A Python interface to interact with Attachmate Extra Terminal sessions via COM API.
    
    Args:
        session_name (str): Name of the Extra session to connect to.
    """
    
    def __init__(self, session_name: str, terminal_type: TerminalType = TerminalType.EXTRA):
        pythoncom.CoInitialize()
        self.timeout = 10000
        self.counter = 0
        self.terminal_type = terminal_type
        
        try:
            if terminal_type == TerminalType.EXTRA:
                self.extra_app = win32com.client.Dispatch(TerminalType.EXTRA.value)
            elif terminal_type == TerminalType.HIS:
                self.extra_app = win32com.client.Dispatch(TerminalType.HIS.value)
            elif terminal_type == TerminalType.NETMANAGE:
                self.extra_app = win32com.client.Dispatch(TerminalType.NETMANAGE.value)
            
            print(f"Successfully created {terminal_type.value} object: {self.extra_app}")
            
            # Modified session handling for different terminal types
            if terminal_type == TerminalType.EXTRA:
                # List available sessions first
                sessions = self.list_available_sessions()
                print(f"Available sessions: {sessions}")
                
                if not sessions:
                    raise SessionError("No sessions available")
                
                # Try to get session by index if session_name is numeric
                try:
                    session_index = int(session_name)
                    self.session = self.extra_app.Sessions(session_index)
                except ValueError:
                    # If session_name is not numeric, try to find by name
                    found = False
                    for i in range(1, self.extra_app.Sessions.Count + 1):
                        session = self.extra_app.Sessions(i)
                        if session.Name == session_name:
                            self.session = session
                            found = True
                            break
                    if not found:
                        raise SessionError(
                            f"Session not found",
                            {"name": session_name, "available": [s['name'] for s in sessions]}
                        )
            elif terminal_type == TerminalType.HIS:
                self.session = self.extra_app.OpenSession(session_name)
            elif terminal_type == TerminalType.NETMANAGE:
                self.session = self.extra_app.Sessions.Item(session_name)
            
            print(f"Successfully connected to session: {self.session.Name}")
            self.screen = self.session.Screen
            self.connected = True
            
        except pythoncom.com_error as e:
            hr, msg, exc, arg = e.args
            raise ConnectionError(
                f"Failed to initialize {terminal_type.value}",
                {"hr": hr, "msg": msg, "source": exc, "arg": arg}
            )
        except Exception as e:
            raise ConnectionError(f"Unexpected error", {"error": str(e)})

    def list_available_sessions(self):
        """List all available Extra terminal sessions"""
        try:
            sessions = []
            for i in range(1, self.extra_app.Sessions.Count + 1):
                session = self.extra_app.Sessions(i)
                sessions.append({
                    'index': i,
                    'name': session.Name,
                    'connected': session.Connected
                })
            return sessions
        except pythoncom.com_error as e:
            return f"Failed to list sessions: {self._format_com_error(e)}"

    def _format_com_error(self, error):
        """Format COM error details for better diagnosis"""
        hr, msg, exc, arg = error.args
        return f"Code: {hr}, Message: {msg}, Source: {exc}, Param: {arg}"

    def check_system_status(self):
        """Diagnostic method to check system status"""
        try:
            versions = {
                'Extra Version': self.extra_app.Version,
                'Session Count': self.extra_app.Sessions.Count,
                'Available Sessions': [sess.Name for sess in self.extra_app.Sessions]
            }
            return versions
        except pythoncom.com_error as e:
            return f"Failed to get system status: {self._format_com_error(e)}"

    def connect(self):
        """Connect to the terminal session with appropriate protocol."""
        if not self.connected:
            try:
                if self.terminal_type == TerminalType.HIS:
                    self.session.Connect()
                    self.session.WaitForConnect(30)  # 30 second timeout
                elif self.terminal_type == TerminalType.NETMANAGE:
                    self.session.Connect()
                    self.session.WaitReady(30000)  # 30 second timeout
                else:
                    self.session.Connect()
                self.connected = True
            except pythoncom.com_error as e:
                raise ConnectionError(f"Connection failed: {e}") from e
 
    def disconnect(self):
        """Safe disconnect handling"""
        try:
            if hasattr(self, 'connected') and self.connected:
                self.connected = False
        except Exception as e:
            print(f"Disconnect warning: {str(e)}")

    def is_connected(self):
        """Check if the session is connected."""
        return self.session.Connected
 
    def wait_for_ready(self, timeout: int = 30) -> bool:
        """Wait until terminal is ready"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if self.screen.OIA.XStatus != 5:
                    return True
                time.sleep(0.1)
            except Exception as e:
                raise TerminalBusyError(
                    "Failed to check terminal status",
                    {"error": str(e), "elapsed": time.time() - start_time}
                )
        raise TerminalBusyError(
            "Terminal busy timeout",
            {"timeout": timeout, "last_status": getattr(self.screen.OIA, 'XStatus', None)}
        )

    def send_keys(self, keys: str) -> None:
        """Send keystrokes to the terminal"""
        if not self.is_connected():
            raise ConnectionError("Not connected to terminal")
        try:
            self.screen.SendKeys(keys)
            if not self.wait_for_ready():
                raise CommandError("Terminal not ready after sending keys")
        except pythoncom.com_error as e:
            hr, msg, exc, arg = e.args
            raise CommandError(
                "Failed to send keys",
                {"keys": keys, "hr": hr, "msg": msg}
            )
 
    def read_screen(self, strip_whitespace: bool = False):
        """
        Read the entire terminal screen using GetStringEx
        
        Args:
            strip_whitespace (bool): If True, returns list of stripped lines. If False, returns raw screen content.
                                   Defaults to True.
        
        Returns:
            Union[List[str], str]: List of lines if strip_whitespace is True, raw string if False
        """
        try:
            # Wait for terminal to be ready
            if not self.wait_for_ready():
                raise TerminalBusyError("Terminal not ready for reading")
                
            # Use 24x80 as default terminal size
            response = self.screen.GetStringEx(0, 0, 32, 80, 120, 0, 0, 0)
            response = response[:2560]  # 32 rows * 80 columns
            
            if strip_whitespace:
                screen_text = []
                for i in range(0, len(response), 80):
                    line = response[i:i+80].rstrip()
                    screen_text.append(line)
                return screen_text
            else:
                return response
                
        except Exception as e:
            raise CommandError(f"Read screen failed: {str(e)}") from e
 
    def wait_for_text(self, text, timeout=30, interval=0.5):
        """Wait until specified text appears on the screen."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                screen_text = self.read_screen()
                for line in screen_text:
                    if text in line:
                        return True
                # Check OIA status
                if hasattr(self.screen, 'OIA') and self.screen.OIA.XStatus != 0:
                    self.counter += 1
                    if self.counter > self.timeout:
                        return False
            except Exception:
                pass
            time.sleep(interval)
        return False
 
    @staticmethod
    def select_session():
        """Interactive method to select a session"""
        try:
            # Create temporary instance just to list sessions
            temp_app = win32com.client.Dispatch("EXTRA.System")
            sessions = []
            
            print("\nAvailable Sessions:")
            print("------------------")
            
            for i in range(1, temp_app.Sessions.Count + 1):
                session = temp_app.Sessions(i)
                sessions.append({
                    'index': i,
                    'name': session.Name,
                    'connected': session.Connected
                })
                status = "Connected" if session.Connected else "Disconnected"
                print(f"{i}. {session.Name} ({status})")
            
            while True:
                choice = input("\nSelect session (enter number): ").strip()
                try:
                    session_index = int(choice)
                    if 1 <= session_index <= len(sessions):
                        return str(session_index)
                    else:
                        print("Invalid session number. Please try again.")
                except ValueError:
                    print("Please enter a valid number.")
                    
        except Exception as e:
            print(f"Error listing sessions: {str(e)}")
            return "1"  # Default to first session if error occurs

    def format_command(self, command):
        """Format command with proper terminal key entries"""
        # Replace common commands with their terminal equivalents
        replacements = {
            '{ENTER}': '<ENTER>',
            '{TAB}': '<TAB>',
            '{CLEAR}': '<CLEAR>',
            '{PA1}': '<PA1>',
            '{PA2}': '<PA2>',
            '{PA3}': '<PA3>',
            '{RESET}': '<RESET>',
            'ENTER': '<ENTER>',
            'TAB': '<TAB>',
            'CLEAR': '<CLEAR>',
            'PA1': '<PA1>',
            'PA2': '<PA2>',
            'PA3': '<PA3>',
            'RESET': '<RESET>'
        }
        
        for old, new in replacements.items():
            command = command.replace(old, new)
        
        # Ensure command ends with <ENTER> if not present
        if not command.strip().endswith('<ENTER>'):
            command = command.strip() + ' <ENTER>'
            
        return command

    def send_command(self, command):
        """Send formatted command to terminal"""
        formatted_command = self.format_command(command)
        print(f"Sending formatted command: {formatted_command}")
        self.send_keys(formatted_command)
        return formatted_command

    def __enter__(self):
        self.connect()
        return self
 
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        try:
            pythoncom.CoUninitialize()
        except Exception as e:
            print(f"CoUninitialize warning: {str(e)}")
 
    @staticmethod
    def detect_terminal_type():
        """Detect available terminal emulation software"""
        terminal_types = []
        
        for terminal_type in TerminalType:
            try:
                win32com.client.Dispatch(terminal_type.value)
                terminal_types.append(terminal_type)
            except:
                continue
        
        return terminal_types

# Example Usage
if __name__ == "__main__":
    try:
        print("Detecting available terminal types...")
        available_types = ExtraTerminal.detect_terminal_type()
        
        if not available_types:
            print("No supported terminal emulation software found!")
            exit(1)
            
        print("\nAvailable terminal types:")
        for i, t_type in enumerate(available_types, 1):
            print(f"{i}. {t_type.value}")
            
        type_choice = int(input("\nSelect terminal type (number): ")) - 1
        selected_type = available_types[type_choice]
        
        session_choice = ExtraTerminal.select_session()
        
        with ExtraTerminal(session_choice, selected_type) as term:
            print("\nSystem Status:", term.check_system_status())
            
            while True:
                print("\nOptions:")
                print("1. Read screen content")
                print("2. Send command")
                print("3. Exit")
                
                choice = input("\nSelect option (1-3): ").strip()
                
                if choice == "1":
                    print("\nCurrent screen content:")
                    print("-" * 80)
                    print("\n".join(term.read_screen()))
                    print("-" * 80)
                
                elif choice == "2":
                    command = input("Enter command: ")
                    term.send_command(command)
                    time.sleep(1)  # Add small delay
                    print("\nScreen after command:")
                    print("-" * 80)
                    print("\n".join(term.read_screen()))
                    print("-" * 80)
                
                elif choice == "3":
                    print("Exiting...")
                    break
                
                else:
                    print("Invalid option. Please try again.")
            
    except ExtraTerminalError as e:
        print(f"Error: {e}")

