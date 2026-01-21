# ErrorRecovery - Integration Plan

**Goal:** 100% Utilization & Compliance across Team Brain  
**Target Date:** 1 week from deployment  
**Owner:** Forge (Team Brain Orchestrator)  
**Version:** 1.0

---

## 🎯 INTEGRATION GOALS

This document outlines how ErrorRecovery integrates with:
1. Team Brain agents (Forge, Atlas, Clio, Nexus, Bolt)
2. Existing Team Brain tools
3. BCH (Beacon Command Hub) - if applicable
4. Logan's workflows

| Goal | Target | Metric |
|------|--------|--------|
| AI Agent Adoption | 100% | 5/5 agents using |
| Tool Integration | 5+ tools | Connected to major tools |
| Error Auto-Resolution | 60%+ | Errors resolved without human help |
| Daily Usage | 10+ recoveries | Logged recovery attempts |

---

## 📦 BCH INTEGRATION

### Overview

ErrorRecovery provides robust error handling for BCH backend services. While not directly exposed via BCH chat interface (it's infrastructure), it powers recovery behind the scenes.

### Backend Integration

**File:** `app/utils/recovery.py`

```python
import sys
sys.path.append("C:/Users/logan/OneDrive/Documents/AutoProjects/ErrorRecovery")
from errorrecovery import ErrorRecovery, RecoveryStrategy

# BCH-configured recovery instance
bch_recovery = ErrorRecovery(
    data_dir="D:/BEACON_HQ/BCH/recovery_data",
    max_retries=3,
    initial_delay=1.0,
    auto_learn=True
)

# Decorator for BCH routes
def with_recovery(fallback=None):
    return bch_recovery.wrap(fallback=fallback)
```

**Usage in Routes:**

```python
# In app/routes/api.py
from app.utils.recovery import with_recovery

@router.post("/api/process")
@with_recovery(fallback=fallback_handler)
async def process_request(data: ProcessRequest):
    # Auto-recovery enabled!
    result = await process_data(data)
    return {"status": "success", "result": result}
```

### Monitoring Dashboard (Future)

When BCH dashboard is complete:
- Recovery statistics widget
- Recent recovery attempts
- Pattern match rates
- Success/failure visualization

---

## 🤖 AI AGENT INTEGRATION

### Integration Matrix

| Agent | Primary Use Case | Integration Method | Priority |
|-------|------------------|-------------------|----------|
| **Forge** | Orchestration error handling | Python API + wrap decorator | HIGH |
| **Atlas** | Tool building recovery | Python API + custom patterns | HIGH |
| **Clio** | Service monitoring recovery | CLI + Python API | HIGH |
| **Nexus** | Cross-platform operations | Python API | MEDIUM |
| **Bolt** | Task execution recovery | Python API | MEDIUM |

---

### Agent-Specific Workflows

#### Forge (Orchestrator / Reviewer)

**Primary Use Case:** Handle errors during task orchestration and review

**Integration Steps:**
1. Import ErrorRecovery at session start
2. Wrap orchestration functions with recovery
3. Use `on_failure` to escalate via Synapse

**Example Workflow:**

```python
from errorrecovery import ErrorRecovery
from synapselink import quick_send

recovery = ErrorRecovery()

def escalate_to_logan(error):
    """Escalate unrecoverable errors."""
    quick_send(
        "LOGAN",
        "Orchestration Error - Needs Review",
        f"Error: {error}\nForge attempted recovery but failed.",
        priority="HIGH"
    )

@recovery.wrap(on_failure=escalate_to_logan)
def orchestrate_task(task_spec):
    """Orchestrate a task with auto-recovery."""
    # Parse task
    # Assign to agents
    # Monitor progress
    return result

# Usage
orchestrate_task({"task": "Build new tool", "agent": "ATLAS"})
```

**When to Use:**
- Assigning tasks to agents
- Coordinating multi-agent work
- Reviewing tool submissions
- Processing Synapse messages

---

#### Atlas (Executor / Builder)

**Primary Use Case:** Recover from errors during tool development

**Integration Steps:**
1. Add recovery to Holy Grail automation
2. Create custom patterns for build errors
3. Use fallback functions for critical operations

**Example Workflow:**

```python
from errorrecovery import ErrorRecovery

recovery = ErrorRecovery()

# Add custom pattern for test failures
recovery.add_pattern(
    pattern_id="test_failure",
    name="Test Suite Failure",
    regex=r"FAILED|AssertionError|test.*fail",
    severity="medium",
    default_strategy="retry_modified",
    recovery_hints=["Check test logic", "Verify test data"]
)

@recovery.wrap
def run_test_suite(test_file):
    """Run tests with auto-recovery."""
    import subprocess
    result = subprocess.run(
        ["python", test_file],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Tests failed: {result.stderr}")
    return result.stdout

# Usage in Holy Grail
run_test_suite("test_errorrecovery.py")
```

**When to Use:**
- Running test suites
- Building tools
- GitHub operations
- File operations

---

#### Clio (Linux / Ubuntu Agent)

**Primary Use Case:** Service monitoring and recovery

**Integration Steps:**
1. Install ErrorRecovery in Ubuntu environment
2. Add to service monitoring scripts
3. Use CLI for quick diagnostics

**Example Workflow:**

```bash
# Check if a service is responding
errorrecovery identify "ConnectionRefusedError: Connection refused"

# In Python script
```

```python
from errorrecovery import ErrorRecovery

recovery = ErrorRecovery()

@recovery.wrap
def check_service(host, port):
    """Check if service is responding."""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((host, port))
    sock.close()
    if result != 0:
        raise ConnectionRefusedError(f"Service not responding: {host}:{port}")
    return True

# Monitor BCH backend
check_service("localhost", 8000)
```

**Platform Considerations:**
- Works identically on Linux/Ubuntu
- Data stored in `~/.errorrecovery/`
- CLI available after pip install

---

#### Nexus (Multi-Platform Agent)

**Primary Use Case:** Cross-platform error handling

**Integration Steps:**
1. Use ErrorRecovery for platform-specific operations
2. Add patterns for platform-specific errors
3. Test on Windows, Linux, macOS

**Example Workflow:**

```python
from errorrecovery import ErrorRecovery
import platform

recovery = ErrorRecovery()

@recovery.wrap
def platform_operation():
    """Operation that varies by platform."""
    if platform.system() == "Windows":
        # Windows-specific code
        pass
    elif platform.system() == "Linux":
        # Linux-specific code
        pass
    return result

# Cross-platform file operations
@recovery.wrap
def read_config():
    from pathlib import Path
    config_path = Path.home() / ".myapp" / "config.json"
    return config_path.read_text()
```

**Cross-Platform Notes:**
- All paths use `pathlib` for compatibility
- No platform-specific dependencies
- Consistent behavior across systems

---

#### Bolt (Free Executor)

**Primary Use Case:** Recover from errors during task execution

**Integration Steps:**
1. Wrap task execution functions
2. Use simple retry strategy (minimize complexity)
3. Report failures via Synapse

**Example Workflow:**

```python
from errorrecovery import recover

def execute_task(task):
    """Execute a task assigned by Forge."""
    # Task execution logic
    pass

# Simple function-based recovery
success, result = recover(execute_task, assigned_task)

if success:
    print(f"Task complete: {result}")
else:
    # Report failure via Synapse
    from synapselink import quick_send
    quick_send("FORGE", "Task Failed", f"Error: {result}")
```

**Cost Considerations:**
- ErrorRecovery itself is FREE (zero dependencies, local)
- Reduces failed task iterations (saves API tokens)
- Prevents wasted sessions on recoverable errors

---

## 🔗 INTEGRATION WITH OTHER TEAM BRAIN TOOLS

### With AgentHealth

**Correlation Use Case:** Monitor agent health during recovery attempts

**Integration Pattern:**

```python
from errorrecovery import ErrorRecovery
from agenthealth import AgentHealth

recovery = ErrorRecovery()
health = AgentHealth()

@recovery.wrap
def monitored_operation(agent_name):
    """Operation with health monitoring."""
    health.heartbeat(agent_name, status="working")
    
    # Do work...
    result = process_data()
    
    health.heartbeat(agent_name, status="idle")
    return result

# If recovery fails, log to health
def on_failure(error):
    health.log_error("ATLAS", str(error))

@recovery.wrap(on_failure=on_failure)
def critical_operation():
    pass
```

---

### With SynapseLink

**Notification Use Case:** Alert team about recovery events

**Integration Pattern:**

```python
from errorrecovery import ErrorRecovery
from synapselink import quick_send

recovery = ErrorRecovery()

def notify_recovery_failure(error):
    """Notify team when recovery fails."""
    quick_send(
        "FORGE,LOGAN",
        f"Recovery Failed",
        f"Error: {error}\n"
        f"Recovery attempted but failed.\n"
        f"Manual intervention may be required.",
        priority="HIGH"
    )

@recovery.wrap(on_failure=notify_recovery_failure)
def critical_task():
    # Critical operation
    pass
```

---

### With SessionReplay

**Debugging Use Case:** Record recovery attempts for later analysis

**Integration Pattern:**

```python
from errorrecovery import ErrorRecovery
from sessionreplay import SessionReplay

recovery = ErrorRecovery()
replay = SessionReplay()

def operation_with_replay(data):
    """Operation with full session recording."""
    session_id = replay.start_session("ATLAS", task="Data processing")
    
    try:
        replay.log_input(session_id, f"Processing: {data}")
        
        @recovery.wrap
        def do_work():
            # Work that might fail
            return process(data)
        
        result = do_work()
        
        replay.log_output(session_id, f"Result: {result}")
        replay.end_session(session_id, status="COMPLETED")
        return result
        
    except Exception as e:
        replay.log_error(session_id, str(e))
        replay.end_session(session_id, status="FAILED")
        raise
```

---

### With TaskQueuePro

**Task Management Use Case:** Retry failed tasks with recovery

**Integration Pattern:**

```python
from errorrecovery import ErrorRecovery, recover
from taskqueuepro import TaskQueuePro

recovery = ErrorRecovery()
queue = TaskQueuePro()

def process_task_with_recovery(task_id):
    """Process a task with automatic recovery."""
    task = queue.get_task(task_id)
    
    # Mark in progress
    queue.start_task(task_id)
    
    try:
        # Execute with recovery
        success, result = recover(execute_task, task.data)
        
        if success:
            queue.complete_task(task_id, result=str(result))
        else:
            queue.fail_task(task_id, error=str(result))
            
    except Exception as e:
        queue.fail_task(task_id, error=str(e))
```

---

### With ContextCompressor

**Token Optimization Use Case:** Compress large error messages

**Integration Pattern:**

```python
from errorrecovery import ErrorRecovery
from contextcompressor import ContextCompressor

recovery = ErrorRecovery()
compressor = ContextCompressor()

def notify_with_compressed_error(error):
    """Send compressed error for large error messages."""
    error_text = str(error)
    
    if len(error_text) > 1000:
        compressed = compressor.compress_text(
            error_text,
            query="error summary",
            method="summary"
        )
        error_text = compressed.compressed_text
    
    # Send compressed error via Synapse
    from synapselink import quick_send
    quick_send("FORGE", "Recovery Failed", error_text)

@recovery.wrap(on_failure=notify_with_compressed_error)
def large_operation():
    pass
```

---

### With TokenTracker

**Cost Tracking Use Case:** Monitor recovery overhead

**Integration Pattern:**

```python
from errorrecovery import ErrorRecovery
from tokentracker import TokenTracker

recovery = ErrorRecovery()
tracker = TokenTracker()

@recovery.wrap
def tracked_operation():
    """Operation with token tracking."""
    # Estimate tokens for operation
    tracker.log_usage(
        agent="ATLAS",
        model="claude-sonnet",
        input_tokens=100,
        output_tokens=50,
        task="Operation with recovery"
    )
    
    # Do work
    return result
```

---

## 🚀 ADOPTION ROADMAP

### Phase 1: Core Adoption (Week 1)

**Goal:** All agents aware and can use basic features

**Steps:**
1. [x] Tool deployed to GitHub
2. [ ] Quick-start guides sent via Synapse
3. [ ] Each agent tests basic workflow
4. [ ] Feedback collected

**Success Criteria:**
- All 5 agents have used ErrorRecovery at least once
- No blocking issues reported

### Phase 2: Integration (Week 2-3)

**Goal:** Integrated into daily workflows

**Steps:**
1. [ ] Add to agent startup routines
2. [ ] Create integration examples with existing tools
3. [ ] Add custom patterns for common Team Brain errors
4. [ ] Monitor usage patterns

**Success Criteria:**
- Used daily by at least 3 agents
- Integration examples tested with 5+ tools

### Phase 3: Optimization (Week 4+)

**Goal:** Optimized and fully adopted

**Steps:**
1. [ ] Collect efficiency metrics
2. [ ] Implement v1.1 improvements based on feedback
3. [ ] Create advanced workflow examples
4. [ ] Share learnings across Team Brain

**Success Criteria:**
- 60%+ error auto-resolution rate
- Measurable time savings documented
- v1.1 improvements identified

---

## 📊 SUCCESS METRICS

**Adoption Metrics:**
- Number of agents using tool: Target 5/5
- Daily usage count: Target 10+ recoveries/day
- Integration with other tools: Target 5+ tools

**Efficiency Metrics:**
- Errors auto-resolved: Target 60%+
- Time saved per recovery: Estimate 5-10 minutes
- Manual intervention reduction: Target 50%+

**Quality Metrics:**
- Bug reports: Track and fix
- Feature requests: Prioritize for v1.1
- User satisfaction: Qualitative feedback

---

## 🛠️ TECHNICAL INTEGRATION DETAILS

### Import Paths

```python
# Standard import
from errorrecovery import ErrorRecovery

# Specific imports
from errorrecovery import (
    ErrorRecovery,
    RecoveryStrategy,
    identify,
    recover,
    stats,
    report
)
```

### Configuration Integration

**Config File:** `~/.errorrecovery/` (auto-created)

**Shared Config with Other Tools:**

```json
{
  "errorrecovery": {
    "max_retries": 3,
    "initial_delay": 1.0,
    "auto_learn": true
  }
}
```

### Error Handling Integration

**Standardized Exit Codes:**
- 0: Success (or recovered successfully)
- 1: Recovery failed
- 2: Configuration error

### Logging Integration

**Log Format:** JSON (compatible with Team Brain standard)

**Log Location:** `~/.errorrecovery/history.json`

---

## 🔧 MAINTENANCE & SUPPORT

### Update Strategy

- Minor updates (v1.x): As needed for bug fixes
- Major updates (v2.0+): With team discussion
- Security patches: Immediate

### Support Channels

- GitHub Issues: Bug reports and feature requests
- Synapse: Team Brain discussions
- Direct to Forge: Complex integration issues

### Known Limitations

- Learning system requires multiple encounters for pattern
- Custom patterns need manual addition
- No GUI (CLI and Python API only)

---

## 📚 ADDITIONAL RESOURCES

- Main Documentation: [README.md](README.md)
- Examples: [EXAMPLES.md](EXAMPLES.md)
- Quick Reference: [CHEAT_SHEET.txt](CHEAT_SHEET.txt)
- Quick Start Guides: [QUICK_START_GUIDES.md](QUICK_START_GUIDES.md)
- Integration Examples: [INTEGRATION_EXAMPLES.md](INTEGRATION_EXAMPLES.md)
- GitHub: https://github.com/DonkRonk17/ErrorRecovery

---

**Last Updated:** January 2026  
**Maintained By:** Forge (Team Brain)  
**For:** Logan Smith / Metaphy LLC
