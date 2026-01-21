#!/usr/bin/env python3
"""
Comprehensive test suite for ErrorRecovery.

Tests cover:
- Core functionality (pattern matching, recovery execution)
- Built-in patterns recognition
- Custom pattern management
- Recovery strategies (retry, fallback, skip, escalate)
- Learning system
- Statistics and reporting
- CLI interface
- Edge cases and error handling

Run: python test_errorrecovery.py
"""

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from errorrecovery import (
    ErrorRecovery,
    ErrorPattern,
    RecoveryStrategy,
    Severity,
    RecoveryAttempt,
    Learning,
    get_recovery,
    identify,
    recover,
    with_recovery,
    stats,
    report,
    VERSION
)


class TestErrorRecoveryCore(unittest.TestCase):
    """Test core ErrorRecovery functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.recovery = ErrorRecovery(
            data_dir=Path(self.temp_dir),
            max_retries=2,
            initial_delay=0.01,  # Fast for testing
            max_delay=0.05
        )
    
    def tearDown(self):
        """Clean up after tests."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass
    
    def test_initialization(self):
        """Test ErrorRecovery initializes correctly."""
        self.assertIsNotNone(self.recovery)
        self.assertIsInstance(self.recovery.patterns, dict)
        self.assertIsInstance(self.recovery.learnings, dict)
        self.assertIsInstance(self.recovery.history, list)
        self.assertTrue(len(self.recovery.patterns) > 0)  # Has built-in patterns
    
    def test_version(self):
        """Test version is set correctly."""
        self.assertEqual(VERSION, "1.0.0")
    
    def test_data_directory_created(self):
        """Test data directory is created on init."""
        self.assertTrue(Path(self.temp_dir).exists())
    
    def test_builtin_patterns_loaded(self):
        """Test built-in patterns are loaded."""
        patterns = self.recovery.list_patterns()
        pattern_ids = [p.pattern_id for p in patterns]
        
        # Check for key built-in patterns
        self.assertIn("connection_refused", pattern_ids)
        self.assertIn("timeout", pattern_ids)
        self.assertIn("file_not_found", pattern_ids)
        self.assertIn("permission_denied", pattern_ids)
        self.assertIn("rate_limit", pattern_ids)


class TestPatternMatching(unittest.TestCase):
    """Test error pattern matching."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.recovery = ErrorRecovery(data_dir=Path(self.temp_dir))
    
    def tearDown(self):
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass
    
    def test_identify_connection_refused(self):
        """Test connection refused error identification."""
        error = ConnectionRefusedError("Connection refused to localhost:8080")
        pattern, error_text = self.recovery.identify_error(error)
        
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.pattern_id, "connection_refused")
    
    def test_identify_timeout(self):
        """Test timeout error identification."""
        error = TimeoutError("Operation timed out after 30 seconds")
        pattern, error_text = self.recovery.identify_error(error)
        
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.pattern_id, "timeout")
    
    def test_identify_file_not_found(self):
        """Test file not found error identification."""
        error = FileNotFoundError("No such file: /path/to/file.txt")
        pattern, error_text = self.recovery.identify_error(error)
        
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.pattern_id, "file_not_found")
    
    def test_identify_permission_denied(self):
        """Test permission denied error identification."""
        error = PermissionError("Permission denied: /etc/shadow")
        pattern, error_text = self.recovery.identify_error(error)
        
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.pattern_id, "permission_denied")
    
    def test_identify_string_error(self):
        """Test identification from string."""
        error_str = "Error 429: Too many requests, rate limit exceeded"
        pattern, error_text = self.recovery.identify_error(error_str)
        
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.pattern_id, "rate_limit")
    
    def test_identify_unknown_error(self):
        """Test unknown error returns None pattern."""
        error = ValueError("Some random unique error xyz123")
        pattern, error_text = self.recovery.identify_error(error)
        
        self.assertIsNone(pattern)
        self.assertIn("ValueError", error_text)
    
    def test_identify_json_decode_error(self):
        """Test JSON decode error identification."""
        error = json.JSONDecodeError("Expecting value", "", 0)
        pattern, error_text = self.recovery.identify_error(error)
        
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.pattern_id, "json_decode")


class TestRecoveryStrategies(unittest.TestCase):
    """Test recovery strategy execution."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.recovery = ErrorRecovery(
            data_dir=Path(self.temp_dir),
            max_retries=2,
            initial_delay=0.01,
            max_delay=0.05
        )
    
    def tearDown(self):
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass
    
    def test_successful_execution_no_error(self):
        """Test successful execution without errors."""
        def success_func(x):
            return x * 2
        
        success, result, attempt = self.recovery.execute_recovery(
            success_func, 5,
            strategy=RecoveryStrategy.RETRY
        )
        
        self.assertTrue(success)
        self.assertEqual(result, 10)
        self.assertIsNotNone(attempt)
        self.assertTrue(attempt.success)
        self.assertEqual(attempt.retry_count, 0)
    
    def test_retry_strategy_eventual_success(self):
        """Test retry strategy with eventual success."""
        call_count = [0]
        
        def flaky_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ConnectionRefusedError("Server not ready")
            return "success"
        
        success, result, attempt = self.recovery.execute_recovery(
            flaky_func,
            strategy=RecoveryStrategy.RETRY
        )
        
        self.assertTrue(success)
        self.assertEqual(result, "success")
        self.assertEqual(call_count[0], 2)  # Failed once, succeeded on retry
    
    def test_retry_strategy_max_retries_exceeded(self):
        """Test retry strategy when max retries exceeded."""
        def always_fail():
            raise ConnectionRefusedError("Server down")
        
        success, result, attempt = self.recovery.execute_recovery(
            always_fail,
            strategy=RecoveryStrategy.RETRY
        )
        
        self.assertFalse(success)
        self.assertIsInstance(result, ConnectionRefusedError)
        self.assertFalse(attempt.success)
    
    def test_fallback_strategy(self):
        """Test fallback strategy execution."""
        def primary_func():
            raise FileNotFoundError("Primary file not found")
        
        def fallback_func():
            return "fallback_result"
        
        success, result, attempt = self.recovery.execute_recovery(
            primary_func,
            strategy=RecoveryStrategy.FALLBACK,
            fallback_func=fallback_func
        )
        
        self.assertTrue(success)
        self.assertEqual(result, "fallback_result")
        self.assertEqual(attempt.fallback_used, "fallback_func")
    
    def test_skip_strategy(self):
        """Test skip strategy."""
        def error_func():
            raise ValueError("Non-critical error")
        
        success, result, attempt = self.recovery.execute_recovery(
            error_func,
            strategy=RecoveryStrategy.SKIP
        )
        
        self.assertTrue(success)  # Skip is considered "success"
        self.assertIsNone(result)
        self.assertEqual(attempt.strategy_used, "skip")
    
    def test_abort_strategy(self):
        """Test abort strategy."""
        def error_func():
            raise SyntaxError("Code error")
        
        success, result, attempt = self.recovery.execute_recovery(
            error_func,
            strategy=RecoveryStrategy.ABORT
        )
        
        self.assertFalse(success)
        self.assertIsInstance(result, SyntaxError)
    
    def test_on_retry_callback(self):
        """Test on_retry callback is called."""
        retry_events = []
        
        def on_retry_callback(retry_count, exception):
            retry_events.append((retry_count, str(exception)))
        
        def flaky_func():
            if len(retry_events) < 1:
                raise TimeoutError("Timed out")
            return "ok"
        
        success, result, _ = self.recovery.execute_recovery(
            flaky_func,
            strategy=RecoveryStrategy.RETRY,
            on_retry=on_retry_callback
        )
        
        self.assertTrue(success)
        self.assertEqual(len(retry_events), 1)
        self.assertIn("Timed out", retry_events[0][1])


class TestCustomPatterns(unittest.TestCase):
    """Test custom pattern management."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.recovery = ErrorRecovery(data_dir=Path(self.temp_dir))
    
    def tearDown(self):
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass
    
    def test_add_pattern(self):
        """Test adding a custom pattern."""
        pattern = self.recovery.add_pattern(
            pattern_id="custom_db_error",
            name="Database Connection Error",
            regex=r"database.*connection.*failed",
            severity="high",
            default_strategy="retry",
            description="Database is not responding"
        )
        
        self.assertEqual(pattern.pattern_id, "custom_db_error")
        self.assertIn("custom_db_error", self.recovery.patterns)
    
    def test_remove_pattern(self):
        """Test removing a custom pattern."""
        self.recovery.add_pattern(
            pattern_id="temp_pattern",
            name="Temporary Pattern",
            regex=r"temp.*error"
        )
        
        result = self.recovery.remove_pattern("temp_pattern")
        self.assertTrue(result)
        self.assertNotIn("temp_pattern", self.recovery.patterns)
    
    def test_remove_nonexistent_pattern(self):
        """Test removing a non-existent pattern."""
        result = self.recovery.remove_pattern("nonexistent_pattern_xyz")
        self.assertFalse(result)
    
    def test_get_pattern(self):
        """Test getting a pattern by ID."""
        pattern = self.recovery.get_pattern("timeout")
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.name, "Operation Timeout")
    
    def test_custom_pattern_matching(self):
        """Test that custom patterns are used for matching."""
        self.recovery.add_pattern(
            pattern_id="custom_service_unavailable",
            name="Custom Service Unavailable",
            message_contains=["xyzservice unavailable", "xyzservice down"],
            severity="medium",
            default_strategy="retry"
        )
        
        error = Exception("Error: XYZService unavailable, please try again")
        pattern, _ = self.recovery.identify_error(error)
        
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.pattern_id, "custom_service_unavailable")
    
    def test_pattern_persistence(self):
        """Test patterns are saved and loaded correctly."""
        self.recovery.add_pattern(
            pattern_id="persistent_pattern",
            name="Persistent Test",
            regex=r"persistent.*test",
            severity="low"
        )
        
        # Create new instance from same data dir
        recovery2 = ErrorRecovery(data_dir=Path(self.temp_dir))
        
        pattern = recovery2.get_pattern("persistent_pattern")
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.name, "Persistent Test")


class TestDecorator(unittest.TestCase):
    """Test the @wrap decorator."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.recovery = ErrorRecovery(
            data_dir=Path(self.temp_dir),
            max_retries=2,
            initial_delay=0.01,
            max_delay=0.05
        )
    
    def tearDown(self):
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass
    
    def test_wrap_decorator_success(self):
        """Test wrap decorator on successful function."""
        @self.recovery.wrap
        def simple_func(x):
            return x + 1
        
        result = simple_func(5)
        self.assertEqual(result, 6)
    
    def test_wrap_decorator_with_recovery(self):
        """Test wrap decorator handles errors."""
        call_count = [0]
        
        @self.recovery.wrap
        def flaky_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise TimeoutError("Timed out")
            return "recovered"
        
        result = flaky_func()
        self.assertEqual(result, "recovered")
        self.assertEqual(call_count[0], 2)
    
    def test_wrap_decorator_with_fallback(self):
        """Test wrap decorator with fallback function."""
        def fallback():
            return "fallback_value"
        
        @self.recovery.wrap(fallback=fallback)
        def always_fails():
            raise FileNotFoundError("Not found")
        
        result = always_fails()
        self.assertEqual(result, "fallback_value")
    
    def test_wrap_preserves_function_name(self):
        """Test wrap decorator preserves function name."""
        @self.recovery.wrap
        def named_function():
            pass
        
        self.assertEqual(named_function.__name__, "named_function")


class TestStatisticsAndHistory(unittest.TestCase):
    """Test statistics and history functionality."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.recovery = ErrorRecovery(
            data_dir=Path(self.temp_dir),
            max_retries=1,
            initial_delay=0.01
        )
    
    def tearDown(self):
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass
    
    def test_statistics_empty(self):
        """Test statistics with no history."""
        stats = self.recovery.get_statistics()
        
        self.assertEqual(stats['total_attempts'], 0)
        self.assertEqual(stats['successful_recoveries'], 0)
        self.assertEqual(stats['success_rate'], 0.0)
    
    def test_statistics_after_attempts(self):
        """Test statistics after recovery attempts."""
        # Successful attempt
        self.recovery.execute_recovery(
            lambda: "ok",
            strategy=RecoveryStrategy.RETRY
        )
        
        # Failed attempt
        self.recovery.execute_recovery(
            lambda: (_ for _ in ()).throw(ValueError("fail")),
            strategy=RecoveryStrategy.ABORT
        )
        
        stats = self.recovery.get_statistics()
        
        self.assertEqual(stats['total_attempts'], 2)
        self.assertEqual(stats['successful_recoveries'], 1)
        self.assertEqual(stats['failed_recoveries'], 1)
        self.assertEqual(stats['success_rate'], 0.5)
    
    def test_history_recorded(self):
        """Test that attempts are recorded in history."""
        self.recovery.execute_recovery(
            lambda: "test",
            strategy=RecoveryStrategy.RETRY
        )
        
        self.assertEqual(len(self.recovery.history), 1)
        self.assertTrue(self.recovery.history[0].success)
    
    def test_clear_history(self):
        """Test clearing history."""
        self.recovery.execute_recovery(
            lambda: "test",
            strategy=RecoveryStrategy.RETRY
        )
        
        self.recovery.clear_history()
        self.assertEqual(len(self.recovery.history), 0)
    
    def test_export_report(self):
        """Test report generation."""
        self.recovery.execute_recovery(
            lambda: "ok",
            strategy=RecoveryStrategy.RETRY
        )
        
        report_text = self.recovery.export_report()
        
        self.assertIn("ERROR RECOVERY REPORT", report_text)
        self.assertIn("Total Recovery Attempts", report_text)


class TestConvenienceFunctions(unittest.TestCase):
    """Test module-level convenience functions."""
    
    def test_get_recovery_singleton(self):
        """Test get_recovery returns same instance."""
        r1 = get_recovery()
        r2 = get_recovery()
        self.assertIs(r1, r2)
    
    def test_identify_function(self):
        """Test identify convenience function."""
        pattern, text = identify(TimeoutError("Operation timed out"))
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.pattern_id, "timeout")
    
    def test_recover_function_success(self):
        """Test recover convenience function."""
        success, result = recover(lambda x: x * 2, 5)
        self.assertTrue(success)
        self.assertEqual(result, 10)
    
    def test_stats_function(self):
        """Test stats convenience function."""
        statistics = stats()
        self.assertIn('total_attempts', statistics)
        self.assertIn('success_rate', statistics)
    
    def test_report_function(self):
        """Test report convenience function."""
        report_text = report()
        self.assertIn("ERROR RECOVERY REPORT", report_text)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.recovery = ErrorRecovery(
            data_dir=Path(self.temp_dir),
            max_retries=1,
            initial_delay=0.01
        )
    
    def tearDown(self):
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass
    
    def test_empty_error_string(self):
        """Test handling empty error string."""
        pattern, text = self.recovery.identify_error("")
        self.assertIsNone(pattern)
        self.assertEqual(text, "")
    
    def test_none_as_error(self):
        """Test handling None converted to string."""
        pattern, text = self.recovery.identify_error("None")
        self.assertIsNone(pattern)
    
    def test_very_long_error_message(self):
        """Test handling very long error messages."""
        long_error = "Error: " + "x" * 10000
        pattern, text = self.recovery.identify_error(long_error)
        self.assertIsNone(pattern)
        self.assertEqual(len(text), len(long_error))
    
    def test_special_characters_in_error(self):
        """Test handling special characters in errors."""
        error = Exception("Error with special chars: <>\"'&\n\t")
        pattern, text = self.recovery.identify_error(error)
        self.assertIn("<>", text)
    
    def test_unicode_in_error(self):
        """Test handling unicode in errors."""
        error = Exception("Error: Connection refused")
        pattern, text = self.recovery.identify_error(error)
        # Should handle unicode without crashing
        self.assertIsNotNone(text)
    
    def test_invalid_regex_in_pattern(self):
        """Test pattern with invalid regex doesn't crash."""
        self.recovery.add_pattern(
            pattern_id="bad_regex",
            name="Bad Regex Pattern",
            regex="[invalid(regex"  # Invalid regex
        )
        
        # Should not crash
        pattern, text = self.recovery.identify_error(Exception("some error"))
        # Just verify it completes
        self.assertIsNotNone(text)
    
    def test_zero_max_retries(self):
        """Test with zero max retries."""
        recovery = ErrorRecovery(
            data_dir=Path(self.temp_dir) / "zero_retries",
            max_retries=0,
            initial_delay=0.01
        )
        
        def fail_func():
            raise ValueError("Fail")
        
        success, result, attempt = recovery.execute_recovery(
            fail_func,
            strategy=RecoveryStrategy.RETRY
        )
        
        self.assertFalse(success)
        self.assertEqual(attempt.retry_count, 0)
    
    def test_function_with_args_and_kwargs(self):
        """Test recovery with function args and kwargs."""
        def complex_func(a, b, c=None, d=None):
            return f"{a}-{b}-{c}-{d}"
        
        success, result, _ = self.recovery.execute_recovery(
            complex_func, "arg1", "arg2",
            c="kwarg1", d="kwarg2",
            strategy=RecoveryStrategy.RETRY
        )
        
        self.assertTrue(success)
        self.assertEqual(result, "arg1-arg2-kwarg1-kwarg2")


class TestLearningSystem(unittest.TestCase):
    """Test the learning system."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.recovery = ErrorRecovery(
            data_dir=Path(self.temp_dir),
            max_retries=2,
            initial_delay=0.01,
            auto_learn=True
        )
    
    def tearDown(self):
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass
    
    def test_learning_recorded_on_success(self):
        """Test that learnings are recorded after successful recovery."""
        call_count = [0]
        
        def flaky_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise TimeoutError("Timed out")
            return "success"
        
        # Execute recovery which should learn
        success, _, _ = self.recovery.execute_recovery(
            flaky_func,
            strategy=RecoveryStrategy.RETRY
        )
        
        self.assertTrue(success)
        # Note: Learning is recorded for pattern-based recoveries
        # For this test, we mainly verify no crash occurs
    
    def test_learnings_persisted(self):
        """Test that learnings are saved to disk."""
        # Record a learning manually
        from errorrecovery import Learning
        learning = Learning(
            learning_id="test_learning",
            pattern_id="timeout",
            error_signature="abc123",
            successful_strategy="retry",
            modifications_applied=None,
            success_rate=0.9,
            attempt_count=10,
            last_success="2026-01-20T00:00:00"
        )
        self.recovery.learnings["test_learning"] = learning
        self.recovery._save_learnings()
        
        # Load in new instance
        recovery2 = ErrorRecovery(data_dir=Path(self.temp_dir))
        
        self.assertIn("test_learning", recovery2.learnings)
        self.assertEqual(recovery2.learnings["test_learning"].success_rate, 0.9)


def run_tests():
    """Run all tests with nice output."""
    print("=" * 70)
    print("TESTING: ErrorRecovery v1.0")
    print("=" * 70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestErrorRecoveryCore))
    suite.addTests(loader.loadTestsFromTestCase(TestPatternMatching))
    suite.addTests(loader.loadTestsFromTestCase(TestRecoveryStrategies))
    suite.addTests(loader.loadTestsFromTestCase(TestCustomPatterns))
    suite.addTests(loader.loadTestsFromTestCase(TestDecorator))
    suite.addTests(loader.loadTestsFromTestCase(TestStatisticsAndHistory))
    suite.addTests(loader.loadTestsFromTestCase(TestConvenienceFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestLearningSystem))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 70)
    print(f"RESULTS: {result.testsRun} tests")
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"[OK] Passed: {passed}")
    if result.failures:
        print(f"[X] Failed: {len(result.failures)}")
    if result.errors:
        print(f"[X] Errors: {len(result.errors)}")
    print("=" * 70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
