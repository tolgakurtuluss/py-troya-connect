import unittest
from unittest.mock import MagicMock, patch
import pythoncom # type: ignore
from py_troya_connect.terminal import (
    ExtraTerminal,
    ExtraTerminalError,
    ConnectionError,
    SessionError,
    TerminalBusyError,
    CommandError,
    TerminalType
)

class TestExtraTerminal(unittest.TestCase):
    @patch('win32com.client.Dispatch')
    def setUp(self, mock_dispatch):
        """Set up test environment before each test"""
        self.mock_session = MagicMock()
        self.mock_screen = MagicMock()
        self.mock_oia = MagicMock()
        self.mock_app = MagicMock()
        
        # Configure mock objects
        mock_dispatch.return_value = self.mock_app
        self.mock_app.Sessions.Count = 2
        self.mock_app.Sessions.return_value = self.mock_session
        self.mock_session.Screen = self.mock_screen
        self.mock_screen.OIA = self.mock_oia
        self.mock_oia.XStatus = 0  # Not busy
        
        # Create test instance
        self.terminal = ExtraTerminal("1")

    # Initialization Tests
    def test_initialization_success(self):
        """Test successful terminal initialization"""
        self.assertTrue(self.terminal.connected)
        self.assertEqual(self.terminal.session, self.mock_session)

    def test_initialization_no_sessions(self):
        """Test initialization with no available sessions"""
        self.mock_app.Sessions.Count = 0
        with self.assertRaises(SessionError) as context:
            ExtraTerminal("1")
        self.assertIn("No sessions available", str(context.exception))

    def test_initialization_session_not_found(self):
        """Test initialization with invalid session name"""
        with self.assertRaises(SessionError) as context:
            ExtraTerminal("NonexistentSession")
        self.assertIn("Session not found", str(context.exception))

    def test_initialization_invalid_terminal_type(self):
        """Test initialization with invalid terminal type"""
        invalid_type = MagicMock()
        invalid_type.value = "INVALID.System"
        with self.assertRaises(ConnectionError):
            ExtraTerminal("1", terminal_type=invalid_type)

    # Command Formatting Tests
    def test_format_command_variations(self):
        """Test command formatting with different inputs"""
        test_cases = [
            ("test", "test <ENTER>"),
            ("test{ENTER}", "test<ENTER>"),
            ("test{TAB}", "test<TAB>"),
            ("test{TAB}{ENTER}", "test<TAB><ENTER>"),
            ("test<ENTER>", "test<ENTER>"),  # Already formatted
        ]
        for input_cmd, expected in test_cases:
            with self.subTest(input_cmd=input_cmd):
                result = self.terminal.format_command(input_cmd)
                self.assertEqual(result, expected)

    def test_format_command_special_keys(self):
        """Test formatting commands with special keys"""
        test_cases = [
            ("CLEAR", "<CLEAR>"),
            ("test{PA1}", "test<PA1>"),
            ("test{PA2}", "test<PA2>"),
            ("test{PA3}", "test<PA3>"),
            ("test{RESET}", "test<RESET>"),
            ("test CLEAR PA1", "test <CLEAR> <PA1>"),
        ]
        for input_cmd, expected in test_cases:
            with self.subTest(input_cmd=input_cmd):
                result = self.terminal.format_command(input_cmd)
                self.assertEqual(result + " <ENTER>", result)

    # Command Execution Tests
    def test_send_command_success(self):
        """Test successful command sending"""
        self.mock_oia.XStatus = 0  # Terminal ready
        self.terminal.send_command("test")
        self.mock_screen.SendKeys.assert_called_once_with("test <ENTER>")

    def test_send_command_terminal_busy(self):
        """Test command sending when terminal is busy"""
        self.mock_oia.XStatus = 5  # Terminal busy
        with self.assertRaises(TerminalBusyError):
            self.terminal.send_command("test")

    def test_send_command_with_special_chars(self):
        """Test sending commands with special characters"""
        self.mock_oia.XStatus = 0
        special_commands = [
            "test<PA1>",
            "test<PA2>",
            "test<CLEAR>",
            "test<RESET>"
        ]
        for cmd in special_commands:
            with self.subTest(command=cmd):
                self.terminal.send_command(cmd)
                self.mock_screen.SendKeys.assert_called_with(f"{cmd} <ENTER>")

    # Screen Reading Tests
    def test_read_screen_success(self):
        """Test successful screen reading"""
        test_content = "test" * 480  # 24x80
        self.mock_screen.GetStringEx.return_value = test_content
        result = self.terminal.read_screen()
        self.assertEqual(len(result), 24)  # Should have 24 lines
        self.mock_screen.GetStringEx.assert_called_once()

    def test_read_screen_busy(self):
        """Test screen reading when terminal is busy"""
        self.mock_oia.XStatus = 5  # Terminal busy
        with self.assertRaises(TerminalBusyError):
            self.terminal.read_screen()

    def test_read_screen_with_strip_options(self):
        """Test screen reading with different strip options"""
        test_content = "  test  " * 480
        self.mock_screen.GetStringEx.return_value = test_content
        
        # Test with strip_whitespace=True
        result_stripped = self.terminal.read_screen(strip_whitespace=True)
        self.assertTrue(all(not line.endswith("  ") for line in result_stripped))
        
        # Test with strip_whitespace=False
        result_raw = self.terminal.read_screen(strip_whitespace=False)
        self.assertEqual(result_raw, test_content[:2560])

    # Wait Operations Tests
    def test_wait_for_text_success(self):
        """Test successful text waiting"""
        self.mock_screen.GetStringEx.return_value = "target text found" * 480
        result = self.terminal.wait_for_text("target text", timeout=1)
        self.assertTrue(result)

    def test_wait_for_text_timeout(self):
        """Test text waiting timeout"""
        self.mock_screen.GetStringEx.return_value = "no match here" * 480
        result = self.terminal.wait_for_text("target text", timeout=1)
        self.assertFalse(result)

    def test_wait_for_ready_success(self):
        """Test successful wait for ready state"""
        self.mock_oia.XStatus = 0
        self.assertTrue(self.terminal.wait_for_ready(timeout=1))

    def test_wait_for_ready_timeout(self):
        """Test timeout while waiting for ready state"""
        self.mock_oia.XStatus = 5
        with self.assertRaises(TerminalBusyError):
            self.terminal.wait_for_ready(timeout=1)

    # Connection Management Tests
    def test_context_manager(self):
        """Test context manager functionality"""
        with ExtraTerminal("1") as term:
            self.assertTrue(term.connected)
        # Should be disconnected after context
        self.assertFalse(term.connected)

    def test_connection_error_handling(self):
        """Test connection error handling"""
        self.mock_session.Connect.side_effect = pythoncom.com_error(0, "Test", "Test", 0)
        with self.assertRaises(ConnectionError):
            self.terminal.connect()

    def test_disconnect_handling(self):
        """Test disconnect behavior"""
        self.terminal.disconnect()
        self.assertFalse(self.terminal.connected)

    def test_reconnection_attempt(self):
        """Test reconnection after disconnect"""
        self.terminal.disconnect()
        self.terminal.connect()
        self.assertTrue(self.terminal.connected)

    # Session Management Tests
    @patch('builtins.input', return_value='1')
    def test_select_session_interactive(self, mock_input):
        """Test interactive session selection"""
        result = ExtraTerminal.select_session()
        self.assertEqual(result, "1")

    def test_list_available_sessions(self):
        """Test listing available sessions"""
        sessions = self.terminal.list_available_sessions()
        self.assertTrue(isinstance(sessions, list))
        self.assertTrue(all(isinstance(s, dict) for s in sessions))
        self.assertTrue(all('index' in s and 'name' in s and 'connected' in s 
                          for s in sessions))

    # Error Handling Tests
    def test_terminal_busy_error_details(self):
        """Test terminal busy error contains proper details"""
        self.mock_oia.XStatus = 5
        with self.assertRaises(TerminalBusyError) as context:
            self.terminal.wait_for_ready(timeout=1)
        self.assertIn('timeout', context.exception.details)
        self.assertIn('last_status', context.exception.details)

    def test_command_error_details(self):
        """Test command error contains proper details"""
        self.mock_screen.SendKeys.side_effect = pythoncom.com_error(0, "Test", "Test", 0)
        with self.assertRaises(CommandError) as context:
            self.terminal.send_command("test")
        self.assertIn('keys', context.exception.details)

    # System Status Tests
    def test_check_system_status(self):
        """Test system status check"""
        self.mock_app.Version = "1.0"
        status = self.terminal.check_system_status()
        self.assertIsInstance(status, dict)
        self.assertIn('Extra Version', status)
        self.assertIn('Session Count', status)
        self.assertIn('Available Sessions', status)

    # Cursor Operation Tests
    def test_move_to_success(self):
        """Test successful cursor movement"""
        self.mock_oia.XStatus = 0
        self.terminal.move_to(1, 1)
        self.mock_screen.MoveTo.assert_called_once_with(1, 1, 1)

    def test_move_to_with_page(self):
        """Test cursor movement with page parameter"""
        self.mock_oia.XStatus = 0
        self.terminal.move_to(5, 10, 2)
        self.mock_screen.MoveTo.assert_called_once_with(5, 10, 2)

    
    def test_move_to_terminal_busy(self):
        """Test cursor movement when terminal is busy"""
        self.mock_oia.XStatus = 5
        with self.assertRaises(TerminalBusyError):
            self.terminal.move_to(1, 1)

    def test_get_cursor_position(self):
        """Test getting cursor position"""
        self.mock_screen.CursorRow = 5
        self.mock_screen.CursorCol = 10
        self.mock_screen.CursorPage = 1
        
        position = self.terminal.get_cursor_position()
        self.assertEqual(position['row'], 5)
        self.assertEqual(position['col'], 10)
        self.assertEqual(position['page'], 1)

if __name__ == '__main__':
    unittest.main(verbosity=2)
