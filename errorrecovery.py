#!/usr/bin/env python3
"""
ErrorRecovery - Intelligent Error Detection and Recovery System

A Q-Mode tool for Team Brain that automatically detects error patterns and
executes recovery strategies. Learns from successful recoveries to improve
future handling.

Features:
- Error pattern recognition (regex-based matching)
- Automatic retry with exponential backoff
- Configurable fallback strategies
- Persistent learning (remembers what worked)
- Integration with Team Brain tools (SynapseLink, AgentHealth)

Author: Forge (Team Brain)
For: Logan Smith / Metaphy LLC
Version: 1.0.0
Date: January 2026
License: MIT
"""

import argparse
import json
import hashlib
import re
import sys
import time
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# ============== CONSTANTS ==============
VERSION = "1.0.0"
DEFAULT_DATA_DIR = Path.home() / ".errorrecovery"
DEFAULT_PATTERNS_FILE = DEFAULT_DATA_DIR / "patterns.json"
DEFAULT_LEARNINGS_FILE = DEFAULT_DATA_DIR / "learnings.json"
DEFAULT_HISTORY_FILE = DEFAULT_DATA_DIR / "history.json"

# Retry defaults
DEFAULT_MAX_RETRIES = 3
DEFAULT_INITIAL_DELAY = 1.0  # seconds
DEFAULT_MAX_DELAY = 60.0     # seconds
DEFAULT_BACKOFF_FACTOR = 2.0


class RecoveryStrategy(Enum):
    """Available recovery strategies."""
    RETRY = "retry"              # Retry with same parameters
    RETRY_MODIFIED = "retry_modified"  # Retry with adjusted parameters
    FALLBACK = "fallback"        # Try alternative approach
    SKIP = "skip"                # Skip and continue
    ESCALATE = "escalate"        # Escalate to human/higher agent
    ABORT = "abort"              # Stop execution


class Severity(Enum):
    """Error severity levels."""
    LOW = "low"           # Minor issue, recoverable
    MEDIUM = "medium"     # Significant but recoverable
    HIGH = "high"         # Critical, needs attention
    CRITICAL = "critical" # Requires immediate escalation


@dataclass
class ErrorPattern:
    """Represents a known error pattern."""
    pattern_id: str
    name: str
    regex: str
    message_contains: Optional[List[str]] = None
    error_types: Optional[List[str]] = None  # Exception class names
    severity: str = "medium"
    default_strategy: str = "retry"
    description: str = ""
    recovery_hints: Optional[List[str]] = None
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    match_count: int = 0
    success_count: int = 0

    def matches(self, error_text: str, error_type: Optional[str] = None) -> bool:
        """Check if this pattern matches the given error."""
        # Check regex pattern
        if self.regex:
            try:
                if re.search(self.regex, error_text, re.IGNORECASE):
                    return True
            except re.error:
                pass
        
        # Check message contains
        if self.message_contains:
            for phrase in self.message_contains:
                if phrase.lower() in error_text.lower():
                    return True
        
        # Check error type
        if self.error_types and error_type:
            if error_type in self.error_types:
                return True
        
        return False


@dataclass
class RecoveryAttempt:
    """Records a recovery attempt."""
    attempt_id: str
    pattern_id: Optional[str]
    error_text: str
    error_type: Optional[str]
    strategy_used: str
    success: bool
    duration_ms: float
    retry_count: int
    modifications: Optional[Dict[str, Any]] = None
    fallback_used: Optional[str] = None
    notes: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Learning:
    """Records what worked for specific error patterns."""
    learning_id: str
    pattern_id: str
    error_signature: str  # Hash of error for deduplication
    successful_strategy: str
    modifications_applied: Optional[Dict[str, Any]]
    success_rate: float
    attempt_count: int
    last_success: str
    notes: Optional[str] = None


class ErrorRecovery:
    """
    Intelligent error recovery system with pattern matching and learning.
    
    Example:
        >>> recovery = ErrorRecovery()
        >>> 
        >>> @recovery.wrap
        >>> def risky_function():
        ...     # Code that might fail
        ...     pass
        >>> 
        >>> result = risky_function()  # Auto-recovery enabled
    """
    
    def __init__(
        self,
        data_dir: Optional[Path] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        initial_delay: float = DEFAULT_INITIAL_DELAY,
        max_delay: float = DEFAULT_MAX_DELAY,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
        auto_learn: bool = True
    ):
        """
        Initialize ErrorRecovery system.
        
        Args:
            data_dir: Directory for storing patterns, learnings, history
            max_retries: Maximum retry attempts
            initial_delay: Initial delay between retries (seconds)
            max_delay: Maximum delay between retries (seconds)
            backoff_factor: Multiplier for exponential backoff
            auto_learn: Whether to automatically learn from recoveries
        """
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.auto_learn = auto_learn
        
        # Load data
        self.patterns: Dict[str, ErrorPattern] = {}
        self.learnings: Dict[str, Learning] = {}
        self.history: List[RecoveryAttempt] = []
        
        self._load_patterns()
        self._load_learnings()
        self._load_history()
        
        # Initialize with built-in patterns
        self._init_builtin_patterns()
    
    def _init_builtin_patterns(self):
        """Initialize built-in error patterns."""
        builtin = [
            ErrorPattern(
                pattern_id="connection_refused",
                name="Connection Refused",
                regex=r"connection\s*refused|ECONNREFUSED|WinError 10061",
                message_contains=["connection refused", "Connection refused"],
                error_types=["ConnectionRefusedError", "OSError"],
                severity="medium",
                default_strategy="retry",
                description="Server or service is not accepting connections",
                recovery_hints=[
                    "Check if server is running",
                    "Verify port number is correct",
                    "Check firewall rules"
                ]
            ),
            ErrorPattern(
                pattern_id="timeout",
                name="Operation Timeout",
                regex=r"timed?\s*out|TimeoutError|deadline exceeded|ETIMEDOUT",
                message_contains=["timeout", "timed out"],
                error_types=["TimeoutError", "asyncio.TimeoutError"],
                severity="medium",
                default_strategy="retry_modified",
                description="Operation took too long to complete",
                recovery_hints=[
                    "Increase timeout value",
                    "Check network connectivity",
                    "Reduce operation scope"
                ]
            ),
            ErrorPattern(
                pattern_id="file_not_found",
                name="File Not Found",
                regex=r"file\s*not\s*found|No such file|ENOENT|FileNotFoundError",
                message_contains=["file not found", "no such file"],
                error_types=["FileNotFoundError"],
                severity="medium",
                default_strategy="fallback",
                description="Requested file does not exist",
                recovery_hints=[
                    "Check file path is correct",
                    "Verify file hasn't been moved/deleted",
                    "Create file if appropriate"
                ]
            ),
            ErrorPattern(
                pattern_id="permission_denied",
                name="Permission Denied",
                regex=r"permission\s*denied|access\s*denied|EACCES|PermissionError",
                message_contains=["permission denied", "access denied"],
                error_types=["PermissionError"],
                severity="high",
                default_strategy="escalate",
                description="Insufficient permissions for operation",
                recovery_hints=[
                    "Check file/directory permissions",
                    "Run with elevated privileges if appropriate",
                    "Contact administrator"
                ]
            ),
            ErrorPattern(
                pattern_id="memory_error",
                name="Memory Error",
                regex=r"out\s*of\s*memory|MemoryError|memory allocation|heap",
                message_contains=["memory", "heap"],
                error_types=["MemoryError"],
                severity="high",
                default_strategy="retry_modified",
                description="Insufficient memory for operation",
                recovery_hints=[
                    "Process data in smaller chunks",
                    "Free up memory before retry",
                    "Increase available memory"
                ]
            ),
            ErrorPattern(
                pattern_id="rate_limit",
                name="Rate Limited",
                regex=r"rate\s*limit|too\s*many\s*requests|429|throttl",
                message_contains=["rate limit", "too many requests", "throttled"],
                severity="low",
                default_strategy="retry",
                description="API rate limit exceeded",
                recovery_hints=[
                    "Wait before retrying",
                    "Implement exponential backoff",
                    "Reduce request frequency"
                ]
            ),
            ErrorPattern(
                pattern_id="json_decode",
                name="JSON Decode Error",
                regex=r"JSONDecodeError|json\.decoder|Expecting value|Invalid JSON",
                message_contains=["json", "decode", "parse error"],
                error_types=["json.JSONDecodeError", "JSONDecodeError"],
                severity="medium",
                default_strategy="skip",
                description="Failed to parse JSON data",
                recovery_hints=[
                    "Validate JSON syntax",
                    "Check for encoding issues",
                    "Handle empty responses"
                ]
            ),
            ErrorPattern(
                pattern_id="network_unreachable",
                name="Network Unreachable",
                regex=r"network\s*(is\s*)?unreachable|ENETUNREACH|no route|DNS",
                message_contains=["network unreachable", "no route"],
                error_types=["OSError"],
                severity="high",
                default_strategy="retry",
                description="Network connectivity issue",
                recovery_hints=[
                    "Check network connection",
                    "Verify DNS resolution",
                    "Check VPN/proxy settings"
                ]
            ),
            ErrorPattern(
                pattern_id="disk_full",
                name="Disk Full",
                regex=r"disk\s*full|no\s*space|ENOSPC|disk quota",
                message_contains=["disk full", "no space left", "quota"],
                severity="critical",
                default_strategy="escalate",
                description="Insufficient disk space",
                recovery_hints=[
                    "Free up disk space",
                    "Clean temporary files",
                    "Extend storage"
                ]
            ),
            ErrorPattern(
                pattern_id="auth_error",
                name="Authentication Error",
                regex=r"auth.*fail|401|unauthorized|invalid\s*(token|credential|api\s*key)",
                message_contains=["authentication", "unauthorized", "invalid token"],
                severity="high",
                default_strategy="escalate",
                description="Authentication or authorization failure",
                recovery_hints=[
                    "Verify credentials",
                    "Refresh authentication token",
                    "Check API key validity"
                ]
            ),
            ErrorPattern(
                pattern_id="import_error",
                name="Import Error",
                regex=r"ImportError|ModuleNotFoundError|No module named",
                message_contains=["import error", "no module named"],
                error_types=["ImportError", "ModuleNotFoundError"],
                severity="high",
                default_strategy="fallback",
                description="Failed to import required module",
                recovery_hints=[
                    "Install missing package",
                    "Check Python path",
                    "Verify package name"
                ]
            ),
            ErrorPattern(
                pattern_id="syntax_error",
                name="Syntax Error",
                regex=r"SyntaxError|invalid syntax|unexpected (token|EOF)",
                error_types=["SyntaxError"],
                severity="high",
                default_strategy="abort",
                description="Invalid Python syntax",
                recovery_hints=[
                    "Check code for typos",
                    "Verify parentheses/brackets match",
                    "Review recent changes"
                ]
            ),
        ]
        
        for pattern in builtin:
            if pattern.pattern_id not in self.patterns:
                self.patterns[pattern.pattern_id] = pattern
    
    def _load_patterns(self):
        """Load patterns from file."""
        patterns_file = self.data_dir / "patterns.json"
        if patterns_file.exists():
            try:
                data = json.loads(patterns_file.read_text(encoding='utf-8'))
                for p_data in data.get('patterns', []):
                    pattern = ErrorPattern(**p_data)
                    self.patterns[pattern.pattern_id] = pattern
            except (json.JSONDecodeError, TypeError) as e:
                print(f"[!] Warning: Could not load patterns: {e}")
    
    def _save_patterns(self):
        """Save patterns to file."""
        patterns_file = self.data_dir / "patterns.json"
        data = {
            'version': VERSION,
            'updated': datetime.now().isoformat(),
            'patterns': [asdict(p) for p in self.patterns.values()]
        }
        patterns_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
    
    def _load_learnings(self):
        """Load learnings from file."""
        learnings_file = self.data_dir / "learnings.json"
        if learnings_file.exists():
            try:
                data = json.loads(learnings_file.read_text(encoding='utf-8'))
                for l_data in data.get('learnings', []):
                    learning = Learning(**l_data)
                    self.learnings[learning.learning_id] = learning
            except (json.JSONDecodeError, TypeError) as e:
                print(f"[!] Warning: Could not load learnings: {e}")
    
    def _save_learnings(self):
        """Save learnings to file."""
        learnings_file = self.data_dir / "learnings.json"
        data = {
            'version': VERSION,
            'updated': datetime.now().isoformat(),
            'learnings': [asdict(l) for l in self.learnings.values()]
        }
        learnings_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
    
    def _load_history(self):
        """Load recovery history from file."""
        history_file = self.data_dir / "history.json"
        if history_file.exists():
            try:
                data = json.loads(history_file.read_text(encoding='utf-8'))
                for h_data in data.get('history', []):
                    attempt = RecoveryAttempt(**h_data)
                    self.history.append(attempt)
            except (json.JSONDecodeError, TypeError) as e:
                print(f"[!] Warning: Could not load history: {e}")
    
    def _save_history(self):
        """Save recovery history to file."""
        history_file = self.data_dir / "history.json"
        # Keep only last 1000 entries
        recent_history = self.history[-1000:]
        data = {
            'version': VERSION,
            'updated': datetime.now().isoformat(),
            'history': [asdict(h) for h in recent_history]
        }
        history_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
    
    def _error_signature(self, error_text: str) -> str:
        """Generate a signature for an error for deduplication."""
        # Normalize error text
        normalized = re.sub(r'\b\d+\b', 'N', error_text)  # Replace numbers
        normalized = re.sub(r'0x[0-9a-fA-F]+', 'ADDR', normalized)  # Replace addresses
        normalized = re.sub(r'[\\/][^\\/\s]+[\\/]', '/', normalized)  # Normalize paths
        normalized = normalized.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
    
    def identify_error(self, error: Union[Exception, str]) -> Tuple[Optional[ErrorPattern], str]:
        """
        Identify an error using pattern matching.
        
        Args:
            error: Exception object or error string
            
        Returns:
            Tuple of (matching pattern or None, error text)
        """
        if isinstance(error, Exception):
            error_text = f"{type(error).__name__}: {str(error)}"
            error_type = type(error).__name__
        else:
            error_text = str(error)
            error_type = None
        
        # Check all patterns for a match
        for pattern in self.patterns.values():
            if pattern.matches(error_text, error_type):
                return pattern, error_text
        
        return None, error_text
    
    def get_recovery_strategy(
        self,
        error: Union[Exception, str],
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[RecoveryStrategy, Optional[ErrorPattern], Dict[str, Any]]:
        """
        Determine the best recovery strategy for an error.
        
        Args:
            error: The error to recover from
            context: Optional context about the operation
            
        Returns:
            Tuple of (strategy, pattern if matched, suggestions dict)
        """
        pattern, error_text = self.identify_error(error)
        error_sig = self._error_signature(error_text)
        
        suggestions = {
            'error_text': error_text,
            'error_signature': error_sig,
            'hints': [],
            'modifications': {}
        }
        
        # Check learnings first
        for learning in self.learnings.values():
            if learning.error_signature == error_sig:
                if learning.success_rate > 0.7:
                    suggestions['learned'] = True
                    suggestions['modifications'] = learning.modifications_applied or {}
                    suggestions['hints'].append(
                        f"Previously successful strategy: {learning.successful_strategy}"
                    )
                    return (
                        RecoveryStrategy(learning.successful_strategy),
                        pattern,
                        suggestions
                    )
        
        # Use pattern-based strategy
        if pattern:
            pattern.match_count += 1
            suggestions['hints'] = pattern.recovery_hints or []
            suggestions['severity'] = pattern.severity
            
            # Strategy-specific modifications
            strategy = RecoveryStrategy(pattern.default_strategy)
            
            if strategy == RecoveryStrategy.RETRY_MODIFIED:
                if "timeout" in pattern.pattern_id.lower():
                    suggestions['modifications'] = {'timeout_multiplier': 2.0}
                elif "memory" in pattern.pattern_id.lower():
                    suggestions['modifications'] = {'chunk_size_divisor': 2}
            
            return strategy, pattern, suggestions
        
        # Default to retry for unknown errors
        suggestions['hints'].append("Unknown error pattern - using default retry strategy")
        return RecoveryStrategy.RETRY, None, suggestions
    
    def execute_recovery(
        self,
        func: Callable,
        *args,
        strategy: RecoveryStrategy = RecoveryStrategy.RETRY,
        fallback_func: Optional[Callable] = None,
        on_retry: Optional[Callable[[int, Exception], None]] = None,
        modifications: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Tuple[bool, Any, Optional[RecoveryAttempt]]:
        """
        Execute a function with recovery handling.
        
        Args:
            func: Function to execute
            *args: Arguments for the function
            strategy: Recovery strategy to use
            fallback_func: Alternative function if primary fails
            on_retry: Callback for retry events (retry_count, exception)
            modifications: Parameters to modify on retry
            **kwargs: Keyword arguments for the function
            
        Returns:
            Tuple of (success, result or exception, recovery attempt record)
        """
        start_time = time.time()
        attempt_id = f"attempt_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        retries = 0
        last_error: Optional[Exception] = None
        modifications = modifications or {}
        
        while retries <= self.max_retries:
            try:
                # Apply modifications if this is a retry
                modified_kwargs = kwargs.copy()
                if retries > 0 and modifications:
                    for key, modifier in modifications.items():
                        if key in modified_kwargs:
                            if isinstance(modifier, (int, float)):
                                modified_kwargs[key] = modified_kwargs[key] * modifier
                
                result = func(*args, **modified_kwargs)
                
                # Success!
                duration = (time.time() - start_time) * 1000
                attempt = RecoveryAttempt(
                    attempt_id=attempt_id,
                    pattern_id=None,
                    error_text="",
                    error_type=None,
                    strategy_used=strategy.value,
                    success=True,
                    duration_ms=duration,
                    retry_count=retries,
                    modifications=modifications if retries > 0 else None
                )
                
                self.history.append(attempt)
                if self.auto_learn:
                    self._save_history()
                
                return True, result, attempt
                
            except Exception as e:
                last_error = e
                error_text = f"{type(e).__name__}: {str(e)}"
                error_type = type(e).__name__
                
                # Identify error pattern
                pattern, _ = self.identify_error(e)
                
                if on_retry:
                    on_retry(retries, e)
                
                # Handle based on strategy
                if strategy == RecoveryStrategy.ABORT:
                    break
                elif strategy == RecoveryStrategy.SKIP:
                    duration = (time.time() - start_time) * 1000
                    attempt = RecoveryAttempt(
                        attempt_id=attempt_id,
                        pattern_id=pattern.pattern_id if pattern else None,
                        error_text=error_text,
                        error_type=error_type,
                        strategy_used="skip",
                        success=True,  # Skip is "successful" as it continues
                        duration_ms=duration,
                        retry_count=retries,
                        notes="Skipped error as per strategy"
                    )
                    self.history.append(attempt)
                    return True, None, attempt
                elif strategy == RecoveryStrategy.ESCALATE:
                    break  # Exit retry loop, will escalate
                elif strategy == RecoveryStrategy.FALLBACK and fallback_func:
                    try:
                        result = fallback_func(*args, **kwargs)
                        duration = (time.time() - start_time) * 1000
                        attempt = RecoveryAttempt(
                            attempt_id=attempt_id,
                            pattern_id=pattern.pattern_id if pattern else None,
                            error_text=error_text,
                            error_type=error_type,
                            strategy_used="fallback",
                            success=True,
                            duration_ms=duration,
                            retry_count=retries,
                            fallback_used=fallback_func.__name__
                        )
                        self.history.append(attempt)
                        
                        # Learn from successful fallback
                        if self.auto_learn and pattern:
                            self._record_learning(pattern, "fallback", None)
                        
                        return True, result, attempt
                    except Exception as fallback_error:
                        last_error = fallback_error
                        break
                
                # Retry strategies
                if retries < self.max_retries:
                    retries += 1
                    delay = min(
                        self.initial_delay * (self.backoff_factor ** (retries - 1)),
                        self.max_delay
                    )
                    time.sleep(delay)
                else:
                    break
        
        # All retries exhausted - failure
        duration = (time.time() - start_time) * 1000
        pattern, _ = self.identify_error(last_error) if last_error else (None, "")
        
        attempt = RecoveryAttempt(
            attempt_id=attempt_id,
            pattern_id=pattern.pattern_id if pattern else None,
            error_text=str(last_error) if last_error else "Unknown error",
            error_type=type(last_error).__name__ if last_error else None,
            strategy_used=strategy.value,
            success=False,
            duration_ms=duration,
            retry_count=retries,
            modifications=modifications if modifications else None
        )
        
        self.history.append(attempt)
        if self.auto_learn:
            self._save_history()
        
        return False, last_error, attempt
    
    def _record_learning(
        self,
        pattern: ErrorPattern,
        successful_strategy: str,
        modifications: Optional[Dict[str, Any]]
    ):
        """Record a successful recovery as a learning."""
        error_sig = pattern.pattern_id
        learning_id = f"learn_{error_sig}"
        
        if learning_id in self.learnings:
            # Update existing learning
            learning = self.learnings[learning_id]
            learning.attempt_count += 1
            learning.success_rate = (
                (learning.success_rate * (learning.attempt_count - 1) + 1.0)
                / learning.attempt_count
            )
            learning.last_success = datetime.now().isoformat()
        else:
            # Create new learning
            learning = Learning(
                learning_id=learning_id,
                pattern_id=pattern.pattern_id,
                error_signature=error_sig,
                successful_strategy=successful_strategy,
                modifications_applied=modifications,
                success_rate=1.0,
                attempt_count=1,
                last_success=datetime.now().isoformat()
            )
            self.learnings[learning_id] = learning
        
        pattern.success_count += 1
        self._save_learnings()
        self._save_patterns()
    
    def wrap(
        self,
        func: Optional[Callable] = None,
        *,
        fallback: Optional[Callable] = None,
        strategy: Optional[RecoveryStrategy] = None,
        on_failure: Optional[Callable[[Exception], Any]] = None
    ):
        """
        Decorator to wrap a function with automatic error recovery.
        
        Args:
            func: Function to wrap (used when called without parens)
            fallback: Fallback function if primary fails
            strategy: Recovery strategy (auto-detected if None)
            on_failure: Callback when recovery fails
            
        Example:
            >>> @recovery.wrap
            >>> def my_function():
            ...     pass
            
            >>> @recovery.wrap(fallback=alternative_func)
            >>> def my_other_function():
            ...     pass
        """
        def decorator(fn: Callable):
            def wrapper(*args, **kwargs):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    # Get recovery strategy
                    rec_strategy, pattern, suggestions = self.get_recovery_strategy(e)
                    if strategy:
                        rec_strategy = strategy
                    
                    # Attempt recovery
                    success, result, attempt = self.execute_recovery(
                        fn,
                        *args,
                        strategy=rec_strategy,
                        fallback_func=fallback,
                        modifications=suggestions.get('modifications'),
                        **kwargs
                    )
                    
                    if success:
                        return result
                    elif on_failure:
                        return on_failure(result if isinstance(result, Exception) else e)
                    else:
                        raise result if isinstance(result, Exception) else e
            
            wrapper.__name__ = fn.__name__
            wrapper.__doc__ = fn.__doc__
            return wrapper
        
        # Handle @recovery.wrap vs @recovery.wrap()
        if func is not None:
            return decorator(func)
        return decorator
    
    def add_pattern(
        self,
        pattern_id: str,
        name: str,
        regex: Optional[str] = None,
        message_contains: Optional[List[str]] = None,
        error_types: Optional[List[str]] = None,
        severity: str = "medium",
        default_strategy: str = "retry",
        description: str = "",
        recovery_hints: Optional[List[str]] = None
    ) -> ErrorPattern:
        """
        Add a custom error pattern.
        
        Args:
            pattern_id: Unique identifier for the pattern
            name: Human-readable name
            regex: Regex pattern to match
            message_contains: Phrases to match in error message
            error_types: Exception class names to match
            severity: Error severity (low, medium, high, critical)
            default_strategy: Default recovery strategy
            description: Description of the error
            recovery_hints: Hints for manual recovery
            
        Returns:
            The created ErrorPattern
        """
        pattern = ErrorPattern(
            pattern_id=pattern_id,
            name=name,
            regex=regex or "",
            message_contains=message_contains,
            error_types=error_types,
            severity=severity,
            default_strategy=default_strategy,
            description=description,
            recovery_hints=recovery_hints
        )
        
        self.patterns[pattern_id] = pattern
        self._save_patterns()
        return pattern
    
    def remove_pattern(self, pattern_id: str) -> bool:
        """Remove a custom error pattern."""
        if pattern_id in self.patterns:
            del self.patterns[pattern_id]
            self._save_patterns()
            return True
        return False
    
    def get_pattern(self, pattern_id: str) -> Optional[ErrorPattern]:
        """Get a pattern by ID."""
        return self.patterns.get(pattern_id)
    
    def list_patterns(self) -> List[ErrorPattern]:
        """List all error patterns."""
        return list(self.patterns.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get recovery statistics."""
        total_attempts = len(self.history)
        successful = sum(1 for h in self.history if h.success)
        
        # Pattern statistics
        pattern_stats = {}
        for pattern in self.patterns.values():
            pattern_stats[pattern.pattern_id] = {
                'name': pattern.name,
                'match_count': pattern.match_count,
                'success_count': pattern.success_count,
                'success_rate': (
                    pattern.success_count / pattern.match_count
                    if pattern.match_count > 0 else 0.0
                )
            }
        
        # Strategy statistics
        strategy_counts = {}
        for h in self.history:
            strat = h.strategy_used
            if strat not in strategy_counts:
                strategy_counts[strat] = {'total': 0, 'success': 0}
            strategy_counts[strat]['total'] += 1
            if h.success:
                strategy_counts[strat]['success'] += 1
        
        return {
            'total_attempts': total_attempts,
            'successful_recoveries': successful,
            'failed_recoveries': total_attempts - successful,
            'success_rate': successful / total_attempts if total_attempts > 0 else 0.0,
            'patterns': pattern_stats,
            'strategies': strategy_counts,
            'learnings_count': len(self.learnings)
        }
    
    def clear_history(self, older_than_days: Optional[int] = None):
        """Clear recovery history."""
        if older_than_days:
            cutoff = datetime.now() - timedelta(days=older_than_days)
            self.history = [
                h for h in self.history
                if datetime.fromisoformat(h.timestamp) > cutoff
            ]
        else:
            self.history = []
        self._save_history()
    
    def export_report(self, output_path: Optional[Path] = None) -> str:
        """Export a comprehensive recovery report."""
        stats = self.get_statistics()
        
        lines = [
            "=" * 70,
            "ERROR RECOVERY REPORT",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 70,
            "",
            "SUMMARY",
            "-" * 40,
            f"Total Recovery Attempts: {stats['total_attempts']}",
            f"Successful Recoveries:   {stats['successful_recoveries']}",
            f"Failed Recoveries:       {stats['failed_recoveries']}",
            f"Overall Success Rate:    {stats['success_rate']:.1%}",
            f"Total Learnings:         {stats['learnings_count']}",
            "",
            "PATTERNS",
            "-" * 40,
        ]
        
        for pid, pstats in stats['patterns'].items():
            if pstats['match_count'] > 0:
                lines.append(
                    f"  {pstats['name']}: "
                    f"{pstats['match_count']} matches, "
                    f"{pstats['success_rate']:.1%} success"
                )
        
        lines.extend([
            "",
            "STRATEGIES",
            "-" * 40,
        ])
        
        for strat, scounts in stats['strategies'].items():
            rate = scounts['success'] / scounts['total'] if scounts['total'] > 0 else 0
            lines.append(f"  {strat}: {scounts['total']} uses, {rate:.1%} success")
        
        lines.extend([
            "",
            "=" * 70,
        ])
        
        report = "\n".join(lines)
        
        if output_path:
            Path(output_path).write_text(report, encoding='utf-8')
        
        return report


# ============== CONVENIENCE FUNCTIONS ==============

# Default instance
_default_instance: Optional[ErrorRecovery] = None


def get_recovery() -> ErrorRecovery:
    """Get the default ErrorRecovery instance."""
    global _default_instance
    if _default_instance is None:
        _default_instance = ErrorRecovery()
    return _default_instance


def identify(error: Union[Exception, str]) -> Tuple[Optional[ErrorPattern], str]:
    """Identify an error using the default instance."""
    return get_recovery().identify_error(error)


def recover(
    func: Callable,
    *args,
    fallback: Optional[Callable] = None,
    **kwargs
) -> Tuple[bool, Any]:
    """
    Execute a function with automatic error recovery.
    
    Example:
        >>> success, result = recover(risky_operation, arg1, arg2)
        >>> if success:
        ...     print(f"Result: {result}")
    """
    recovery = get_recovery()
    
    try:
        result = func(*args, **kwargs)
        return True, result
    except Exception as e:
        strategy, pattern, suggestions = recovery.get_recovery_strategy(e)
        success, result, _ = recovery.execute_recovery(
            func, *args,
            strategy=strategy,
            fallback_func=fallback,
            modifications=suggestions.get('modifications'),
            **kwargs
        )
        return success, result


def with_recovery(fallback: Optional[Callable] = None):
    """
    Decorator for automatic error recovery.
    
    Example:
        >>> @with_recovery(fallback=alternative_func)
        >>> def my_function():
        ...     pass
    """
    return get_recovery().wrap(fallback=fallback)


def stats() -> Dict[str, Any]:
    """Get recovery statistics."""
    return get_recovery().get_statistics()


def report(output_path: Optional[str] = None) -> str:
    """Generate and optionally save a recovery report."""
    path = Path(output_path) if output_path else None
    return get_recovery().export_report(path)


# ============== CLI INTERFACE ==============

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='ErrorRecovery - Intelligent Error Detection and Recovery',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s identify "ConnectionRefusedError: Connection refused"
  %(prog)s patterns                     # List all patterns
  %(prog)s stats                        # Show recovery statistics
  %(prog)s report                       # Generate full report
  %(prog)s history --recent 10          # Show recent recovery attempts
  %(prog)s add-pattern myerr "My Error" --regex "my.*error"

For more information: https://github.com/DonkRonk17/ErrorRecovery
        """
    )
    
    parser.add_argument(
        '--version', action='version',
        version=f'%(prog)s {VERSION}'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # identify command
    identify_parser = subparsers.add_parser(
        'identify', help='Identify an error pattern'
    )
    identify_parser.add_argument('error', help='Error message to identify')
    
    # patterns command
    patterns_parser = subparsers.add_parser(
        'patterns', help='List all error patterns'
    )
    patterns_parser.add_argument(
        '--json', action='store_true', help='Output as JSON'
    )
    
    # stats command
    stats_parser = subparsers.add_parser(
        'stats', help='Show recovery statistics'
    )
    stats_parser.add_argument(
        '--json', action='store_true', help='Output as JSON'
    )
    
    # report command
    report_parser = subparsers.add_parser(
        'report', help='Generate recovery report'
    )
    report_parser.add_argument(
        '-o', '--output', help='Output file path'
    )
    
    # history command
    history_parser = subparsers.add_parser(
        'history', help='Show recovery history'
    )
    history_parser.add_argument(
        '--recent', type=int, default=10, help='Number of recent entries'
    )
    history_parser.add_argument(
        '--clear', action='store_true', help='Clear history'
    )
    history_parser.add_argument(
        '--older-than', type=int, help='Clear entries older than N days'
    )
    
    # add-pattern command
    add_parser = subparsers.add_parser(
        'add-pattern', help='Add a custom error pattern'
    )
    add_parser.add_argument('pattern_id', help='Unique pattern ID')
    add_parser.add_argument('name', help='Pattern name')
    add_parser.add_argument('--regex', help='Regex pattern')
    add_parser.add_argument('--contains', nargs='+', help='Message contains phrases')
    add_parser.add_argument(
        '--strategy', default='retry',
        choices=['retry', 'retry_modified', 'fallback', 'skip', 'escalate', 'abort'],
        help='Default recovery strategy'
    )
    add_parser.add_argument(
        '--severity', default='medium',
        choices=['low', 'medium', 'high', 'critical'],
        help='Error severity'
    )
    add_parser.add_argument('--description', default='', help='Pattern description')
    
    # remove-pattern command
    remove_parser = subparsers.add_parser(
        'remove-pattern', help='Remove a custom error pattern'
    )
    remove_parser.add_argument('pattern_id', help='Pattern ID to remove')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    recovery = ErrorRecovery()
    
    if args.command == 'identify':
        pattern, error_text = recovery.identify_error(args.error)
        if pattern:
            print(f"[OK] Identified: {pattern.name}")
            print(f"    Pattern ID: {pattern.pattern_id}")
            print(f"    Severity:   {pattern.severity}")
            print(f"    Strategy:   {pattern.default_strategy}")
            if pattern.description:
                print(f"    Description: {pattern.description}")
            if pattern.recovery_hints:
                print("    Recovery hints:")
                for hint in pattern.recovery_hints:
                    print(f"      - {hint}")
        else:
            print("[!] No matching pattern found")
            print(f"    Error: {error_text}")
        return 0
    
    elif args.command == 'patterns':
        patterns = recovery.list_patterns()
        if args.json:
            print(json.dumps([asdict(p) for p in patterns], indent=2))
        else:
            print(f"Error Patterns ({len(patterns)} total)")
            print("-" * 60)
            for p in sorted(patterns, key=lambda x: x.severity, reverse=True):
                status = f"[{p.match_count} matches]" if p.match_count > 0 else ""
                print(f"  {p.pattern_id}: {p.name} ({p.severity}) {status}")
                if p.description:
                    print(f"    {p.description}")
        return 0
    
    elif args.command == 'stats':
        statistics = recovery.get_statistics()
        if args.json:
            print(json.dumps(statistics, indent=2))
        else:
            print("Recovery Statistics")
            print("-" * 40)
            print(f"Total Attempts:  {statistics['total_attempts']}")
            print(f"Successful:      {statistics['successful_recoveries']}")
            print(f"Failed:          {statistics['failed_recoveries']}")
            print(f"Success Rate:    {statistics['success_rate']:.1%}")
            print(f"Learnings:       {statistics['learnings_count']}")
        return 0
    
    elif args.command == 'report':
        output = recovery.export_report(args.output)
        if args.output:
            print(f"[OK] Report saved to: {args.output}")
        else:
            print(output)
        return 0
    
    elif args.command == 'history':
        if args.clear:
            recovery.clear_history(older_than_days=args.older_than)
            print("[OK] History cleared")
            return 0
        
        recent = recovery.history[-args.recent:]
        if not recent:
            print("No recovery history")
            return 0
        
        print(f"Recent Recovery Attempts ({len(recent)} of {len(recovery.history)})")
        print("-" * 70)
        for attempt in reversed(recent):
            status = "[OK]" if attempt.success else "[X]"
            print(f"{status} {attempt.timestamp[:19]} | "
                  f"Strategy: {attempt.strategy_used} | "
                  f"Retries: {attempt.retry_count}")
            if attempt.error_text:
                error_preview = attempt.error_text[:60]
                if len(attempt.error_text) > 60:
                    error_preview += "..."
                print(f"    Error: {error_preview}")
        return 0
    
    elif args.command == 'add-pattern':
        pattern = recovery.add_pattern(
            pattern_id=args.pattern_id,
            name=args.name,
            regex=args.regex,
            message_contains=args.contains,
            default_strategy=args.strategy,
            severity=args.severity,
            description=args.description
        )
        print(f"[OK] Added pattern: {pattern.pattern_id}")
        return 0
    
    elif args.command == 'remove-pattern':
        if recovery.remove_pattern(args.pattern_id):
            print(f"[OK] Removed pattern: {args.pattern_id}")
            return 0
        else:
            print(f"[X] Pattern not found: {args.pattern_id}")
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
