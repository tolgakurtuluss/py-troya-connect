import unittest
from unittest.mock import MagicMock, patch
import pythoncom
from py_troya_connect.terminal import (
    ExtraTerminal,
    ExtraTerminalError,
    ConnectionError,
    SessionError,
    TerminalBusyError,
    CommandError
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

    @patch('builtins.input', return_value='1')
    def test_select_session_interactive(self, mock_input):
        """Test interactive session selection"""
        result = ExtraTerminal.select_session()
        self.assertEqual(result, "1")

if __name__ == '__main__':
    unittest.main(verbosity=2)
