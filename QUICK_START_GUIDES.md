# ErrorRecovery - Quick Start Guides

## 📖 ABOUT THESE GUIDES

Each Team Brain agent has a **5-minute quick-start guide** tailored to their role and workflows.

**Choose your guide:**
- [Forge (Orchestrator)](#-forge-quick-start)
- [Atlas (Executor)](#-atlas-quick-start)
- [Clio (Linux Agent)](#-clio-quick-start)
- [Nexus (Multi-Platform)](#-nexus-quick-start)
- [Bolt (Free Executor)](#-bolt-quick-start)

---

## 🔥 FORGE QUICK START

**Role:** Orchestrator / Reviewer  
**Time:** 5 minutes  
**Goal:** Use ErrorRecovery for task orchestration with automatic escalation

### Step 1: Installation Check

```python
# Verify ErrorRecovery is available
import sys
sys.path.append("C:/Users/logan/OneDrive/Documents/AutoProjects/ErrorRecovery")
from errorrecovery import ErrorRecovery

recovery = ErrorRecovery()
print(f"[OK] ErrorRecovery ready - {len(recovery.patterns)} patterns loaded")
```

Expected output:
```
[OK] ErrorRecovery ready - 12 patterns loaded
```

### Step 2: First Use - Orchestration with Recovery

```python
from errorrecovery import ErrorRecovery
from synapselink import quick_send

recovery = ErrorRecovery()

def escalate_error(error):
    """Escalate to Logan if recovery fails."""
    quick_send(
        "LOGAN",
        "Orchestration Error",
        f"Forge recovery failed:\n{error}",
        priority="HIGH"
    )
    return None

@recovery.wrap(on_failure=escalate_error)
def assign_task(task, agent):
    """Assign task to agent with recovery."""
    # Validate task
    if not task:
        raise ValueError("Task cannot be empty")
    
    # Send via Synapse
    quick_send(agent, "New Task", task)
    return {"status": "assigned", "agent": agent}

# Use it
result = assign_task("Build ErrorRecovery integration examples", "ATLAS")
print(f"Result: {result}")
```

### Step 3: Integration with Forge Workflows

**Use Case 1: Review Tool Submissions**

```python
@recovery.wrap
def review_tool(tool_path):
    """Review a tool submission with recovery."""
    # Check tests pass
    import subprocess
    result = subprocess.run(
        ["python", f"{tool_path}/test_*.py"],
        capture_output=True, text=True, shell=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Tests failed: {result.stderr}")
    return {"status": "approved", "tests": "passing"}
```

**Use Case 2: Coordinate Multi-Agent Work**

```python
@recovery.wrap
def coordinate_session(agents, task):
    """Start a collab session with recovery."""
    from collabsession import CollabSession
    session = CollabSession()
    session_id = session.start(task, participants=agents)
    return session_id
```

### Step 4: Common Forge Commands

```bash
# Check recovery statistics
errorrecovery stats

# View recent recovery attempts
errorrecovery history --recent 5

# Identify an error quickly
errorrecovery identify "Connection refused"
```

### Next Steps for Forge

1. Read [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md) - Forge section
2. Try [EXAMPLES.md](EXAMPLES.md) - Example 9 (Team Brain integration)
3. Add ErrorRecovery to orchestration workflows
4. Set up escalation paths for critical failures

---

## ⚡ ATLAS QUICK START

**Role:** Executor / Builder  
**Time:** 5 minutes  
**Goal:** Use ErrorRecovery during tool development and testing

### Step 1: Installation Check

```python
import sys
sys.path.append("C:/Users/logan/OneDrive/Documents/AutoProjects/ErrorRecovery")
from errorrecovery import ErrorRecovery, recover

recovery = ErrorRecovery()
print(f"[OK] ErrorRecovery v1.0 ready")
```

### Step 2: First Use - Wrap Build Operations

```python
from errorrecovery import ErrorRecovery

recovery = ErrorRecovery()

@recovery.wrap
def run_tests(test_file):
    """Run test suite with auto-recovery."""
    import subprocess
    result = subprocess.run(
        ["python", test_file],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Tests failed:\n{result.stderr}")
    return result.stdout

# Run tests with recovery
output = run_tests("test_errorrecovery.py")
print(f"Tests output: {output[:200]}...")
```

### Step 3: Add Custom Patterns for Build Errors

```python
# Add pattern for common build errors
recovery.add_pattern(
    pattern_id="git_push_failed",
    name="Git Push Failed",
    regex=r"git.*push.*failed|rejected|non-fast-forward",
    severity="medium",
    default_strategy="retry",
    recovery_hints=["Pull latest changes first", "Check remote exists"]
)

recovery.add_pattern(
    pattern_id="test_assertion",
    name="Test Assertion Failed",
    regex=r"AssertionError|assert.*failed|FAILED",
    severity="medium",
    default_strategy="skip",  # Skip failed test, continue
    recovery_hints=["Check test data", "Review assertion logic"]
)
```

### Step 4: Integration with Holy Grail

```python
# In Holy Grail automation
from errorrecovery import recover

def holy_grail_step(step_func, *args):
    """Execute a Holy Grail step with recovery."""
    success, result = recover(step_func, *args)
    
    if success:
        print(f"[OK] Step completed: {result}")
        return result
    else:
        print(f"[X] Step failed: {result}")
        # Log to session bookmark
        return None

# Usage
holy_grail_step(run_tests, "test_errorrecovery.py")
holy_grail_step(create_readme, tool_name)
holy_grail_step(git_push, repo_url)
```

### Next Steps for Atlas

1. Add ErrorRecovery to Holy Grail automation
2. Create custom patterns for common build errors
3. Use `recover()` for each automation step
4. Report patterns that should be built-in to Forge

---

## 🐧 CLIO QUICK START

**Role:** Linux / Ubuntu Agent  
**Time:** 5 minutes  
**Goal:** Use ErrorRecovery for service monitoring and CLI operations

### Step 1: Linux Installation

```bash
# Clone from GitHub (if not already available)
cd ~/AutoProjects
git clone https://github.com/DonkRonk17/ErrorRecovery.git
cd ErrorRecovery

# Install in editable mode
pip3 install -e .

# Verify
errorrecovery --version
```

Expected output:
```
errorrecovery 1.0.0
```

### Step 2: First Use - Service Monitoring

```python
from errorrecovery import ErrorRecovery

recovery = ErrorRecovery()

@recovery.wrap
def check_service(host, port):
    """Check if a service is responding."""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((host, port))
    sock.close()
    
    if result != 0:
        raise ConnectionRefusedError(f"Service not responding: {host}:{port}")
    
    return True

# Monitor BCH backend
if check_service("localhost", 8000):
    print("[OK] BCH backend is running")
```

### Step 3: CLI Operations with Recovery

```bash
# Identify errors from logs
errorrecovery identify "Error: Connection timed out"

# Check patterns available
errorrecovery patterns

# View recent issues
errorrecovery history --recent 10
```

### Step 4: Integration with Clio Workflows

**Service Health Check Script:**

```python
#!/usr/bin/env python3
"""Service health check with auto-recovery."""

from errorrecovery import ErrorRecovery, recover

recovery = ErrorRecovery()

services = [
    ("BCH Backend", "localhost", 8000),
    ("Database", "localhost", 5432),
    ("Redis", "localhost", 6379),
]

def check_service(name, host, port):
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((host, port))
    sock.close()
    if result != 0:
        raise ConnectionRefusedError(f"{name} not responding")
    return f"{name}: OK"

for name, host, port in services:
    success, result = recover(check_service, name, host, port)
    if success:
        print(f"[OK] {result}")
    else:
        print(f"[X] {name}: FAILED")
```

### Next Steps for Clio

1. Add health checks to cron jobs
2. Monitor BCH services with recovery
3. Use CLI for quick error diagnosis
4. Report Linux-specific patterns needed

---

## 🌐 NEXUS QUICK START

**Role:** Multi-Platform Agent  
**Time:** 5 minutes  
**Goal:** Use ErrorRecovery across Windows, Linux, and macOS

### Step 1: Platform Detection

```python
import platform
from errorrecovery import ErrorRecovery

recovery = ErrorRecovery()

print(f"Platform: {platform.system()}")
print(f"ErrorRecovery data: {recovery.data_dir}")
print(f"Patterns loaded: {len(recovery.patterns)}")
```

Expected output:
```
Platform: Windows  # or Linux, Darwin
ErrorRecovery data: C:\Users\user\.errorrecovery
Patterns loaded: 12
```

### Step 2: Cross-Platform Operations

```python
from errorrecovery import ErrorRecovery
from pathlib import Path

recovery = ErrorRecovery()

@recovery.wrap
def read_config():
    """Read config from platform-appropriate location."""
    config_path = Path.home() / ".myapp" / "config.json"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    
    return config_path.read_text()

# Works on any platform!
config = read_config()
```

### Step 3: Platform-Specific Considerations

**Windows:**
- Data stored in `C:\Users\<user>\.errorrecovery\`
- Use `pathlib` for paths (forward slashes work)

**Linux:**
- Data stored in `~/.errorrecovery/`
- Ensure proper permissions on data dir

**macOS:**
- Data stored in `~/.errorrecovery/`
- Same behavior as Linux

### Step 4: Common Nexus Commands

```bash
# Works identically on all platforms
errorrecovery stats
errorrecovery patterns
errorrecovery identify "FileNotFoundError: No such file"
```

### Next Steps for Nexus

1. Test on all target platforms
2. Report platform-specific issues
3. Add platform-specific patterns if needed
4. Document any behavioral differences

---

## 🆓 BOLT QUICK START

**Role:** Free Executor (Cline + Grok)  
**Time:** 5 minutes  
**Goal:** Use ErrorRecovery to reduce failed task iterations

### Step 1: Verify Free Access

```bash
# ErrorRecovery is 100% free - no API keys needed!
python -c "from errorrecovery import recover; print('[OK] Ready')"
```

### Step 2: Simple Task Recovery

```python
from errorrecovery import recover

def execute_task(task_data):
    """Execute a task assigned by Forge."""
    # Process task
    if not task_data:
        raise ValueError("Empty task")
    
    # Do the work...
    return f"Completed: {task_data['name']}"

# Execute with recovery - FREE!
success, result = recover(execute_task, {"name": "Build feature"})

if success:
    print(f"[OK] {result}")
else:
    print(f"[X] Failed: {result}")
```

### Step 3: Report Failures to Forge

```python
from errorrecovery import recover
from synapselink import quick_send

def execute_with_reporting(task):
    """Execute task and report failures."""
    success, result = recover(process_task, task)
    
    if not success:
        # Report to Forge
        quick_send(
            "FORGE",
            "Task Failed",
            f"Task: {task['name']}\nError: {result}",
            priority="NORMAL"
        )
    
    return success, result
```

### Step 4: Batch Processing

```python
from errorrecovery import recover

tasks = [task1, task2, task3, task4, task5]
results = []

for task in tasks:
    success, result = recover(process_task, task)
    
    if success:
        results.append(result)
    else:
        # Skip failed, continue with rest
        print(f"[!] Skipping failed task: {task['name']}")

print(f"Completed: {len(results)}/{len(tasks)} tasks")
```

### Next Steps for Bolt

1. Add recovery to all task execution
2. Use simple retry strategy (minimize complexity)
3. Report unrecoverable errors via Synapse
4. Track which errors are most common

---

## 📚 ADDITIONAL RESOURCES

**For All Agents:**
- Full Documentation: [README.md](README.md)
- Examples: [EXAMPLES.md](EXAMPLES.md)
- Integration Plan: [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md)
- Cheat Sheet: [CHEAT_SHEET.txt](CHEAT_SHEET.txt)

**Support:**
- GitHub Issues: https://github.com/DonkRonk17/ErrorRecovery/issues
- Synapse: Post in THE_SYNAPSE/active/
- Direct: Message Forge for complex issues

---

**Last Updated:** January 2026  
**Maintained By:** Forge (Team Brain)
