# ErrorRecovery - Usage Examples

Quick navigation:
- [Example 1: Basic Decorator Usage](#example-1-basic-decorator-usage)
- [Example 2: Function-Based Recovery](#example-2-function-based-recovery)
- [Example 3: Recovery with Fallback](#example-3-recovery-with-fallback)
- [Example 4: Custom Error Handling](#example-4-custom-error-handling)
- [Example 5: Adding Custom Patterns](#example-5-adding-custom-patterns)
- [Example 6: Error Identification](#example-6-error-identification)
- [Example 7: Statistics and Reporting](#example-7-statistics-and-reporting)
- [Example 8: CLI Usage](#example-8-cli-usage)
- [Example 9: Integration with Team Brain Tools](#example-9-integration-with-team-brain-tools)
- [Example 10: Advanced Configuration](#example-10-advanced-configuration)

---

## Example 1: Basic Decorator Usage

**Scenario:** Wrap a network function that may fail with connection errors.

**Code:**
```python
from errorrecovery import ErrorRecovery

recovery = ErrorRecovery()

@recovery.wrap
def fetch_url(url):
    """Fetch data from a URL with auto-recovery."""
    import urllib.request
    with urllib.request.urlopen(url, timeout=10) as response:
        return response.read().decode('utf-8')

# Use it - errors are handled automatically!
try:
    data = fetch_url("https://example.com/api/data")
    print(f"Got {len(data)} bytes")
except Exception as e:
    print(f"Failed after recovery attempts: {e}")
```

**Expected Output (success case):**
```
Got 1256 bytes
```

**Expected Output (with recovery):**
```
[Connection refused, retrying in 1s...]
[Connection refused, retrying in 2s...]
Got 1256 bytes
```

**What You Learned:**
- The `@recovery.wrap` decorator adds automatic error recovery
- Known errors (connection refused, timeout) are retried automatically
- You don't need to write retry logic yourself

---

## Example 2: Function-Based Recovery

**Scenario:** Execute a risky function with recovery using the functional API.

**Code:**
```python
from errorrecovery import recover

def read_config_file(path):
    """Read configuration from a file."""
    with open(path, 'r') as f:
        return f.read()

# Execute with recovery
success, result = recover(read_config_file, "/etc/myapp/config.json")

if success:
    print(f"Config loaded: {result[:50]}...")
else:
    print(f"Failed to load config: {result}")
```

**Expected Output (file exists):**
```
Config loaded: {"setting1": "value1", "setting2": "va...
```

**Expected Output (file missing after retries):**
```
Failed to load config: FileNotFoundError: [Errno 2] No such file...
```

**What You Learned:**
- `recover()` returns `(success, result)` tuple
- If success is True, result is the function's return value
- If success is False, result is the exception that caused failure

---

## Example 3: Recovery with Fallback

**Scenario:** Try a primary function, fall back to an alternative if it fails.

**Code:**
```python
from errorrecovery import ErrorRecovery

recovery = ErrorRecovery()

def load_from_api():
    """Try to load data from remote API."""
    raise ConnectionRefusedError("API server is down")

def load_from_cache():
    """Load data from local cache as fallback."""
    return {"cached": True, "data": [1, 2, 3]}

@recovery.wrap(fallback=load_from_cache)
def get_data():
    return load_from_api()

# This will fail on primary but succeed with fallback
data = get_data()
print(f"Data: {data}")
```

**Expected Output:**
```
Data: {'cached': True, 'data': [1, 2, 3]}
```

**What You Learned:**
- Use `fallback=` to specify an alternative function
- Fallback is called if the primary function fails after all retries
- Fallback should return the same type as the primary function

---

## Example 4: Custom Error Handling

**Scenario:** Handle recovery failure with custom logic.

**Code:**
```python
from errorrecovery import ErrorRecovery

recovery = ErrorRecovery()

def on_failure_callback(error):
    """Called when recovery fails."""
    print(f"[ALERT] Recovery failed: {type(error).__name__}")
    # Send notification, log to file, etc.
    return {"error": str(error), "fallback": True}

@recovery.wrap(on_failure=on_failure_callback)
def critical_operation():
    """An operation that always fails for this example."""
    raise TimeoutError("Operation took too long")

# Execute - on_failure will be called
result = critical_operation()
print(f"Result: {result}")
```

**Expected Output:**
```
[ALERT] Recovery failed: TimeoutError
Result: {'error': 'Operation took too long', 'fallback': True}
```

**What You Learned:**
- `on_failure=` specifies a callback when recovery fails
- The callback receives the exception and can return a default value
- Use this for logging, notifications, or graceful degradation

---

## Example 5: Adding Custom Patterns

**Scenario:** Add a pattern for a custom error type specific to your application.

**Code:**
```python
from errorrecovery import ErrorRecovery

recovery = ErrorRecovery()

# Add a custom pattern for database errors
recovery.add_pattern(
    pattern_id="postgres_connection",
    name="PostgreSQL Connection Error",
    regex=r"could not connect to server|connection refused",
    message_contains=["psycopg2", "postgresql"],
    error_types=["psycopg2.OperationalError"],
    severity="high",
    default_strategy="retry",
    description="PostgreSQL database is not responding",
    recovery_hints=[
        "Check PostgreSQL service is running",
        "Verify connection string in config",
        "Check pg_hba.conf for access rules"
    ]
)

# Verify pattern was added
pattern = recovery.get_pattern("postgres_connection")
print(f"Added pattern: {pattern.name}")
print(f"Severity: {pattern.severity}")
print(f"Strategy: {pattern.default_strategy}")

# List all patterns
for p in recovery.list_patterns():
    print(f"  - {p.pattern_id}: {p.name}")
```

**Expected Output:**
```
Added pattern: PostgreSQL Connection Error
Severity: high
Strategy: retry
  - connection_refused: Connection Refused
  - timeout: Operation Timeout
  - postgres_connection: PostgreSQL Connection Error
  ...
```

**What You Learned:**
- Use `add_pattern()` to create custom error patterns
- Patterns can match by regex, message keywords, or exception types
- Custom patterns are persisted and loaded on restart

---

## Example 6: Error Identification

**Scenario:** Identify what type of error occurred and get recovery hints.

**Code:**
```python
from errorrecovery import identify

# Test various errors
errors = [
    ConnectionRefusedError("Connection refused to localhost:8080"),
    TimeoutError("Operation timed out after 30 seconds"),
    FileNotFoundError("No such file: /data/config.json"),
    PermissionError("Permission denied: /etc/shadow"),
    ValueError("Some random unique error xyz123"),
]

for error in errors:
    pattern, error_text = identify(error)
    
    print(f"\nError: {error}")
    if pattern:
        print(f"  Pattern: {pattern.name}")
        print(f"  Severity: {pattern.severity}")
        print(f"  Strategy: {pattern.default_strategy}")
        if pattern.recovery_hints:
            print(f"  Hints: {pattern.recovery_hints[0]}")
    else:
        print("  Pattern: Unknown (no match)")
```

**Expected Output:**
```
Error: Connection refused to localhost:8080
  Pattern: Connection Refused
  Severity: medium
  Strategy: retry
  Hints: Check if server is running

Error: Operation timed out after 30 seconds
  Pattern: Operation Timeout
  Severity: medium
  Strategy: retry_modified
  Hints: Increase timeout value

Error: No such file: /data/config.json
  Pattern: File Not Found
  Severity: medium
  Strategy: fallback
  Hints: Check file path is correct

Error: Permission denied: /etc/shadow
  Pattern: Permission Denied
  Severity: high
  Strategy: escalate
  Hints: Check file/directory permissions

Error: Some random unique error xyz123
  Pattern: Unknown (no match)
```

**What You Learned:**
- `identify()` matches errors against known patterns
- Returns `(pattern, error_text)` - pattern is None if no match
- Use this for debugging or building custom recovery logic

---

## Example 7: Statistics and Reporting

**Scenario:** Monitor recovery effectiveness with statistics and reports.

**Code:**
```python
from errorrecovery import ErrorRecovery

recovery = ErrorRecovery()

# Simulate some recovery attempts
def success_func():
    return "ok"

def fail_func():
    raise ValueError("Always fails")

# Run some operations
for _ in range(5):
    recovery.execute_recovery(success_func, strategy=recovery.RecoveryStrategy.RETRY)

for _ in range(2):
    recovery.execute_recovery(fail_func, strategy=recovery.RecoveryStrategy.ABORT)

# Get statistics
stats = recovery.get_statistics()
print(f"Total attempts: {stats['total_attempts']}")
print(f"Successful: {stats['successful_recoveries']}")
print(f"Failed: {stats['failed_recoveries']}")
print(f"Success rate: {stats['success_rate']:.1%}")

# Generate report
print("\n" + "="*50)
print(recovery.export_report())
```

**Expected Output:**
```
Total attempts: 7
Successful: 5
Failed: 2
Success rate: 71.4%

==================================================
======================================================================
ERROR RECOVERY REPORT
Generated: 2026-01-20 18:30:00
======================================================================

SUMMARY
----------------------------------------
Total Recovery Attempts: 7
Successful Recoveries:   5
Failed Recoveries:       2
Overall Success Rate:    71.4%
Total Learnings:         0

STRATEGIES
----------------------------------------
  retry: 5 uses, 100.0% success
  abort: 2 uses, 0.0% success

======================================================================
```

**What You Learned:**
- `get_statistics()` returns a dict with recovery metrics
- `export_report()` generates a formatted text report
- Use these to monitor error handling effectiveness

---

## Example 8: CLI Usage

**Scenario:** Use ErrorRecovery from the command line.

**Commands:**

```bash
# Identify an error
errorrecovery identify "ConnectionRefusedError: Connection refused"
```

**Output:**
```
[OK] Identified: Connection Refused
    Pattern ID: connection_refused
    Severity:   medium
    Strategy:   retry
    Description: Server or service is not accepting connections
    Recovery hints:
      - Check if server is running
      - Verify port number is correct
      - Check firewall rules
```

```bash
# List all patterns
errorrecovery patterns
```

**Output:**
```
Error Patterns (12 total)
------------------------------------------------------------
  disk_full: Disk Full (critical) 
  permission_denied: Permission Denied (high) 
  auth_error: Authentication Error (high) 
  connection_refused: Connection Refused (medium) [3 matches]
  timeout: Operation Timeout (medium) [5 matches]
  ...
```

```bash
# Show statistics
errorrecovery stats
```

**Output:**
```
Recovery Statistics
----------------------------------------
Total Attempts:  28
Successful:      24
Failed:          4
Success Rate:    85.7%
Learnings:       5
```

```bash
# Add custom pattern
errorrecovery add-pattern my_api_error "My API Error" \
    --regex "MyAPI.*failed" \
    --strategy retry \
    --severity medium
```

**Output:**
```
[OK] Added pattern: my_api_error
```

**What You Learned:**
- CLI provides quick access to all features
- Use `identify` to diagnose errors
- Use `stats` to monitor effectiveness
- Use `add-pattern` to add custom patterns

---

## Example 9: Integration with Team Brain Tools

**Scenario:** Combine ErrorRecovery with SynapseLink, AgentHealth, and SessionReplay.

**Code:**
```python
import sys
sys.path.append("C:/Users/logan/OneDrive/Documents/AutoProjects")

from errorrecovery import ErrorRecovery
from synapselink import quick_send
from agenthealth import AgentHealth
from sessionreplay import SessionReplay

# Initialize all tools
recovery = ErrorRecovery()
health = AgentHealth()
replay = SessionReplay()

def on_failure(error):
    """Notify team and log to health system."""
    # Alert via Synapse
    quick_send(
        "FORGE",
        "Recovery Failed",
        f"Agent: ATLAS\nError: {error}\nNeeds attention!",
        priority="HIGH"
    )
    # Log to health
    health.log_error("ATLAS", str(error))
    return None

@recovery.wrap(on_failure=on_failure)
def process_data(data_path):
    """Process data with full recovery and monitoring."""
    # Log to session replay
    session_id = replay.start_session("ATLAS", task="Data processing")
    
    try:
        # Heartbeat to AgentHealth
        health.heartbeat("ATLAS", status="processing")
        
        # Do work (might fail)
        with open(data_path, 'r') as f:
            result = f.read()
        
        # Success!
        replay.log_output(session_id, f"Processed {len(result)} bytes")
        replay.end_session(session_id, status="COMPLETED")
        health.heartbeat("ATLAS", status="idle")
        
        return result
        
    except Exception as e:
        replay.log_error(session_id, str(e))
        replay.end_session(session_id, status="FAILED")
        raise

# Execute with full Team Brain integration
result = process_data("/path/to/data.json")
```

**What You Learned:**
- ErrorRecovery integrates seamlessly with Team Brain tools
- Use `on_failure` to trigger notifications via SynapseLink
- Combine with AgentHealth for monitoring
- Use SessionReplay for debugging failed operations

---

## Example 10: Advanced Configuration

**Scenario:** Configure ErrorRecovery for specific use cases.

**Code:**
```python
from errorrecovery import ErrorRecovery, RecoveryStrategy
from pathlib import Path

# High-throughput configuration (fast retries)
fast_recovery = ErrorRecovery(
    data_dir=Path.home() / ".myapp" / "recovery",
    max_retries=2,           # Fewer retries
    initial_delay=0.1,       # 100ms initial delay
    max_delay=1.0,           # Max 1 second
    backoff_factor=1.5,      # Gentle backoff
    auto_learn=True
)

# Robust configuration (patient retries)
robust_recovery = ErrorRecovery(
    max_retries=10,          # Many retries
    initial_delay=5.0,       # 5 second initial delay
    max_delay=300.0,         # Up to 5 minutes
    backoff_factor=2.0,      # Double each time
    auto_learn=True
)

# Use appropriate recovery for different operations
@fast_recovery.wrap
def quick_api_call():
    """Fast operation that should fail quickly."""
    pass

@robust_recovery.wrap  
def slow_batch_job():
    """Long-running job that can wait for resources."""
    pass

# Manual control over strategy
def custom_operation():
    # Determine strategy based on context
    if is_critical:
        strategy = RecoveryStrategy.ESCALATE
    elif has_fallback:
        strategy = RecoveryStrategy.FALLBACK
    else:
        strategy = RecoveryStrategy.RETRY_MODIFIED
    
    success, result, attempt = fast_recovery.execute_recovery(
        my_function,
        strategy=strategy,
        fallback_func=alternative_function,
        modifications={'timeout_multiplier': 2.0}
    )
    
    print(f"Strategy used: {attempt.strategy_used}")
    print(f"Retries: {attempt.retry_count}")
    print(f"Duration: {attempt.duration_ms:.1f}ms")
```

**What You Learned:**
- Create multiple ErrorRecovery instances for different use cases
- Configure timing parameters for your specific needs
- Use `execute_recovery()` for manual control over strategy
- Pass `modifications` to adjust parameters on retry

---

## Summary

| Example | Key Concept |
|---------|-------------|
| 1 | Basic decorator pattern |
| 2 | Function-based recovery with success/result |
| 3 | Fallback functions for graceful degradation |
| 4 | Custom error handling with callbacks |
| 5 | Adding domain-specific error patterns |
| 6 | Error identification and hints |
| 7 | Statistics and reporting |
| 8 | CLI for quick operations |
| 9 | Team Brain tool integration |
| 10 | Advanced configuration options |

---

**For more information:**
- [README.md](README.md) - Full documentation
- [CHEAT_SHEET.txt](CHEAT_SHEET.txt) - Quick reference
- [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md) - Team Brain integration

**Questions?** Open an issue on GitHub or message via Synapse!
