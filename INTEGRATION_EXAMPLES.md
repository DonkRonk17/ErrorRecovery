# ErrorRecovery - Integration Examples

## 🎯 INTEGRATION PHILOSOPHY

ErrorRecovery is designed to work seamlessly with other Team Brain tools. This document provides **copy-paste-ready code examples** for common integration patterns.

---

## 📚 TABLE OF CONTENTS

1. [Pattern 1: ErrorRecovery + AgentHealth](#pattern-1-errorrecovery--agenthealth)
2. [Pattern 2: ErrorRecovery + SynapseLink](#pattern-2-errorrecovery--synapselink)
3. [Pattern 3: ErrorRecovery + TaskQueuePro](#pattern-3-errorrecovery--taskqueuepro)
4. [Pattern 4: ErrorRecovery + SessionReplay](#pattern-4-errorrecovery--sessionreplay)
5. [Pattern 5: ErrorRecovery + ContextCompressor](#pattern-5-errorrecovery--contextcompressor)
6. [Pattern 6: ErrorRecovery + TokenTracker](#pattern-6-errorrecovery--tokentracker)
7. [Pattern 7: ErrorRecovery + CollabSession](#pattern-7-errorrecovery--collabsession)
8. [Pattern 8: ErrorRecovery + MemoryBridge](#pattern-8-errorrecovery--memorybridge)
9. [Pattern 9: Multi-Tool Workflow](#pattern-9-multi-tool-workflow)
10. [Pattern 10: Full Team Brain Stack](#pattern-10-full-team-brain-stack)

---

## Pattern 1: ErrorRecovery + AgentHealth

**Use Case:** Monitor agent health during recovery attempts

**Why:** Understand how errors affect agent performance

**Code:**

```python
import sys
sys.path.append("C:/Users/logan/OneDrive/Documents/AutoProjects")

from errorrecovery import ErrorRecovery
from agenthealth import AgentHealth

# Initialize both tools
recovery = ErrorRecovery()
health = AgentHealth()

def on_recovery_failure(error):
    """Log error to AgentHealth when recovery fails."""
    health.log_error("ATLAS", str(error))
    return None

@recovery.wrap(on_failure=on_recovery_failure)
def agent_task(data):
    """Task with health monitoring during recovery."""
    # Start health tracking
    health.heartbeat("ATLAS", status="working")
    
    # Do work (might fail and recover)
    result = process_data(data)
    
    # Report success
    health.heartbeat("ATLAS", status="idle")
    return result

# Usage
result = agent_task({"input": "test"})

# Check health stats
health_report = health.get_agent_status("ATLAS")
print(f"Agent status: {health_report}")
```

**Result:** Correlated health and recovery data for analysis

---

## Pattern 2: ErrorRecovery + SynapseLink

**Use Case:** Notify Team Brain when recovery events occur

**Why:** Keep team informed of errors automatically

**Code:**

```python
from errorrecovery import ErrorRecovery, identify
from synapselink import quick_send

recovery = ErrorRecovery()

def notify_recovery_failure(error):
    """Send Synapse notification when recovery fails."""
    # Identify error pattern
    pattern, error_text = identify(error)
    
    # Build message
    if pattern:
        message = (
            f"Error Type: {pattern.name}\n"
            f"Severity: {pattern.severity}\n"
            f"Details: {error_text[:200]}\n"
            f"Recovery Hints:\n"
        )
        for hint in (pattern.recovery_hints or [])[:3]:
            message += f"  - {hint}\n"
    else:
        message = f"Unknown error: {error_text[:300]}"
    
    # Send to appropriate recipients based on severity
    if pattern and pattern.severity == "critical":
        recipients = "FORGE,LOGAN"
        priority = "URGENT"
    elif pattern and pattern.severity == "high":
        recipients = "FORGE"
        priority = "HIGH"
    else:
        recipients = "FORGE"
        priority = "NORMAL"
    
    quick_send(
        recipients,
        f"Recovery Failed - {type(error).__name__}",
        message,
        priority=priority
    )
    
    return None

@recovery.wrap(on_failure=notify_recovery_failure)
def critical_operation():
    """Operation that notifies on failure."""
    # ... your code ...
    pass

# Usage
result = critical_operation()
```

**Result:** Team stays informed without manual status updates

---

## Pattern 3: ErrorRecovery + TaskQueuePro

**Use Case:** Process queued tasks with automatic recovery

**Why:** Tasks retry automatically instead of failing permanently

**Code:**

```python
from errorrecovery import ErrorRecovery, recover
from taskqueuepro import TaskQueuePro

recovery = ErrorRecovery()
queue = TaskQueuePro()

def process_queued_tasks():
    """Process all pending tasks with recovery."""
    pending = queue.get_pending()
    
    for task in pending:
        # Mark in progress
        queue.start_task(task.task_id)
        
        try:
            # Execute with recovery
            success, result = recover(
                execute_task,
                task.data
            )
            
            if success:
                queue.complete_task(
                    task.task_id,
                    result=str(result)
                )
            else:
                queue.fail_task(
                    task.task_id,
                    error=str(result)
                )
                
        except Exception as e:
            queue.fail_task(task.task_id, error=str(e))

def execute_task(data):
    """Actual task execution."""
    # Your task logic here
    return f"Processed: {data}"

# Process all tasks
process_queued_tasks()

# Check results
print(f"Completed: {len(queue.get_completed())}")
print(f"Failed: {len(queue.get_failed())}")
```

**Result:** Centralized task tracking with automatic recovery

---

## Pattern 4: ErrorRecovery + SessionReplay

**Use Case:** Record recovery attempts for debugging

**Why:** Replay failed sessions to understand what went wrong

**Code:**

```python
from errorrecovery import ErrorRecovery
from sessionreplay import SessionReplay

recovery = ErrorRecovery()
replay = SessionReplay()

def operation_with_full_recording(data):
    """Operation recorded for replay with recovery."""
    # Start session recording
    session_id = replay.start_session(
        "ATLAS",
        task=f"Processing {data.get('name', 'unknown')}"
    )
    
    try:
        # Log input
        replay.log_input(session_id, f"Input data: {data}")
        
        # Execute with recovery
        @recovery.wrap
        def inner_operation():
            # Your risky code here
            result = process(data)
            return result
        
        result = inner_operation()
        
        # Log success
        replay.log_output(session_id, f"Result: {result}")
        replay.end_session(session_id, status="COMPLETED")
        
        return result
        
    except Exception as e:
        # Log error
        replay.log_error(session_id, str(e))
        replay.end_session(session_id, status="FAILED")
        raise

# Usage
result = operation_with_full_recording({"name": "test"})

# Later, replay the session for debugging
# replay.replay_session(session_id)
```

**Result:** Full session replay available for debugging

---

## Pattern 5: ErrorRecovery + ContextCompressor

**Use Case:** Compress error information before sharing

**Why:** Large error traces waste tokens when reporting

**Code:**

```python
from errorrecovery import ErrorRecovery, identify
from contextcompressor import ContextCompressor
from synapselink import quick_send

recovery = ErrorRecovery()
compressor = ContextCompressor()

def notify_compressed_error(error):
    """Send compressed error notification."""
    error_text = str(error)
    
    # Compress if large
    if len(error_text) > 500:
        compressed = compressor.compress_text(
            error_text,
            query="error summary cause solution",
            method="extraction"
        )
        error_summary = compressed.compressed_text
        savings = compressed.estimated_token_savings
    else:
        error_summary = error_text
        savings = 0
    
    # Identify pattern for additional context
    pattern, _ = identify(error)
    
    message = f"Error Summary:\n{error_summary}\n"
    if pattern:
        message += f"\nPattern: {pattern.name}"
        if pattern.recovery_hints:
            message += f"\nHint: {pattern.recovery_hints[0]}"
    if savings > 0:
        message += f"\n\n[Compressed - saved ~{savings} tokens]"
    
    quick_send("FORGE", "Error Report", message)
    return None

@recovery.wrap(on_failure=notify_compressed_error)
def large_operation():
    """Operation with potentially large error output."""
    pass
```

**Result:** 50-70% token savings on error notifications

---

## Pattern 6: ErrorRecovery + TokenTracker

**Use Case:** Track recovery overhead costs

**Why:** Understand how much recovery costs in tokens

**Code:**

```python
from errorrecovery import ErrorRecovery, stats
from tokentracker import TokenTracker

recovery = ErrorRecovery()
tracker = TokenTracker()

def tracked_operation_with_recovery(operation_name, func, *args, **kwargs):
    """Execute operation with both recovery and token tracking."""
    
    # Estimate input tokens
    input_estimate = len(str(args)) // 4 + len(str(kwargs)) // 4
    
    # Execute with recovery
    @recovery.wrap
    def wrapped_func():
        return func(*args, **kwargs)
    
    result = wrapped_func()
    
    # Estimate output tokens
    output_estimate = len(str(result)) // 4 if result else 0
    
    # Get recovery stats
    recovery_stats = stats()
    
    # Log to tracker
    tracker.log_usage(
        agent="ATLAS",
        model="local",  # ErrorRecovery is free
        input_tokens=input_estimate,
        output_tokens=output_estimate,
        task=f"{operation_name} (recovery enabled)"
    )
    
    return result

# Usage
result = tracked_operation_with_recovery(
    "Data processing",
    process_data,
    input_file
)

# Check costs
budget = tracker.get_budget_status()
print(f"Budget used: ${budget['used']:.2f}")
```

**Result:** Full cost visibility including recovery overhead

---

## Pattern 7: ErrorRecovery + CollabSession

**Use Case:** Coordinate multi-agent work with shared recovery

**Why:** All agents in a session benefit from recovery

**Code:**

```python
from errorrecovery import ErrorRecovery
from collabsession import CollabSession

recovery = ErrorRecovery()
collab = CollabSession()

def collaborative_task_with_recovery(task_name, participants):
    """Run collaborative task with recovery for all agents."""
    
    # Start collaboration session
    session_id = collab.start_session(
        task_name,
        participants=participants
    )
    
    @recovery.wrap
    def agent_work(agent, subtask):
        """Each agent's work wrapped with recovery."""
        # Lock resource to prevent conflicts
        collab.lock_resource(session_id, subtask, agent)
        
        try:
            # Do the work
            result = execute_subtask(subtask)
            
            # Update session
            collab.update_status(session_id, agent, "completed")
            
            return result
        finally:
            collab.unlock_resource(session_id, subtask)
    
    # Execute all subtasks
    results = {}
    for agent, subtask in assign_subtasks(participants):
        results[agent] = agent_work(agent, subtask)
    
    # End session
    collab.end_session(session_id)
    
    return results

# Usage
results = collaborative_task_with_recovery(
    "Build new feature",
    ["FORGE", "ATLAS", "CLIO"]
)
```

**Result:** Safe concurrent work with recovery for all agents

---

## Pattern 8: ErrorRecovery + MemoryBridge

**Use Case:** Persist recovery learnings across sessions

**Why:** Share successful recovery strategies across agents

**Code:**

```python
from errorrecovery import ErrorRecovery, stats
from memorybridge import MemoryBridge

recovery = ErrorRecovery()
memory = MemoryBridge()

def sync_recovery_learnings():
    """Sync recovery learnings to MemoryBridge."""
    # Get current stats
    current_stats = stats()
    
    # Load existing shared learnings
    shared = memory.get(
        "errorrecovery_learnings",
        namespace="team_brain",
        default={"patterns": {}, "strategies": {}}
    )
    
    # Merge local learnings
    for pattern_id, pattern_stats in current_stats.get('patterns', {}).items():
        if pattern_stats['match_count'] > 0:
            if pattern_id not in shared['patterns']:
                shared['patterns'][pattern_id] = pattern_stats
            else:
                # Update with better success rate
                if pattern_stats['success_rate'] > shared['patterns'][pattern_id]['success_rate']:
                    shared['patterns'][pattern_id] = pattern_stats
    
    # Save back to shared memory
    memory.set(
        "errorrecovery_learnings",
        shared,
        namespace="team_brain",
        ttl=86400 * 7  # Keep for 7 days
    )
    
    memory.sync()
    
    return shared

# Sync learnings at end of session
shared_learnings = sync_recovery_learnings()
print(f"Shared {len(shared_learnings['patterns'])} pattern learnings")
```

**Result:** Recovery knowledge shared across all agents

---

## Pattern 9: Multi-Tool Workflow

**Use Case:** Complete workflow using multiple tools with recovery

**Why:** Demonstrate real production scenario

**Code:**

```python
from errorrecovery import ErrorRecovery, recover
from synapselink import quick_send
from agenthealth import AgentHealth
from sessionreplay import SessionReplay
from taskqueuepro import TaskQueuePro

# Initialize all tools
recovery = ErrorRecovery()
health = AgentHealth()
replay = SessionReplay()
queue = TaskQueuePro()

def full_workflow(task_data):
    """Complete production workflow with all tools."""
    
    agent = "ATLAS"
    
    # 1. Create task in queue
    task_id = queue.create_task(
        title=task_data['name'],
        agent=agent,
        priority=task_data.get('priority', 2)
    )
    
    # 2. Start session recording
    session_id = replay.start_session(agent, task=task_data['name'])
    
    # 3. Start health monitoring
    health.start_session(agent, session_id=session_id)
    
    try:
        # 4. Mark task started
        queue.start_task(task_id)
        replay.log_input(session_id, f"Starting: {task_data}")
        health.heartbeat(agent, status="working")
        
        # 5. Execute with recovery
        @recovery.wrap
        def do_work():
            return process_task(task_data)
        
        result = do_work()
        
        # 6. Success path
        queue.complete_task(task_id, result=str(result))
        replay.log_output(session_id, f"Result: {result}")
        replay.end_session(session_id, status="COMPLETED")
        health.end_session(agent, session_id=session_id, status="success")
        
        # 7. Notify success
        quick_send("FORGE", "Task Complete", f"Task: {task_data['name']}")
        
        return result
        
    except Exception as e:
        # 8. Failure path
        queue.fail_task(task_id, error=str(e))
        replay.log_error(session_id, str(e))
        replay.end_session(session_id, status="FAILED")
        health.log_error(agent, str(e))
        health.end_session(agent, session_id=session_id, status="failed")
        
        # 9. Alert team
        quick_send(
            "FORGE,LOGAN",
            "Workflow Failed",
            f"Task: {task_data['name']}\nError: {e}",
            priority="HIGH"
        )
        
        raise

# Usage
result = full_workflow({"name": "Build feature X", "priority": 1})
```

**Result:** Fully instrumented, coordinated workflow with recovery

---

## Pattern 10: Full Team Brain Stack

**Use Case:** Ultimate integration - all tools working together

**Why:** Production-grade agent operation

**Code:**

```python
"""
Full Team Brain Stack Integration

This pattern shows how ErrorRecovery integrates with the entire
Team Brain tool ecosystem for production-grade AI agent operations.
"""

import sys
sys.path.append("C:/Users/logan/OneDrive/Documents/AutoProjects")

# Import all tools
from errorrecovery import ErrorRecovery, recover, stats
from synapselink import quick_send
from agenthealth import AgentHealth
from sessionreplay import SessionReplay
from taskqueuepro import TaskQueuePro
from contextcompressor import ContextCompressor
from tokentracker import TokenTracker

class TeamBrainAgent:
    """Full-featured Team Brain agent with all integrations."""
    
    def __init__(self, agent_name):
        self.agent = agent_name
        
        # Initialize all tools
        self.recovery = ErrorRecovery()
        self.health = AgentHealth()
        self.replay = SessionReplay()
        self.queue = TaskQueuePro()
        self.compressor = ContextCompressor()
        self.tracker = TokenTracker()
        
        # Track session
        self.session_id = None
    
    def start_session(self, task_name):
        """Start a fully instrumented session."""
        self.session_id = self.replay.start_session(
            self.agent, task=task_name
        )
        self.health.start_session(
            self.agent, session_id=self.session_id
        )
        return self.session_id
    
    def execute(self, func, *args, **kwargs):
        """Execute function with full Team Brain integration."""
        
        # Log to replay
        self.replay.log_input(
            self.session_id,
            f"Executing: {func.__name__}"
        )
        
        # Health heartbeat
        self.health.heartbeat(self.agent, status="executing")
        
        # Execute with recovery
        success, result = recover(func, *args, **kwargs)
        
        # Log result
        if success:
            self.replay.log_output(self.session_id, f"Success: {result}")
        else:
            self.replay.log_error(self.session_id, f"Failed: {result}")
        
        # Track tokens
        self.tracker.log_usage(
            agent=self.agent,
            model="local",
            input_tokens=100,  # Estimate
            output_tokens=50,
            task=func.__name__
        )
        
        return success, result
    
    def end_session(self, success=True):
        """End session with full cleanup."""
        status = "COMPLETED" if success else "FAILED"
        
        self.replay.end_session(self.session_id, status=status)
        self.health.end_session(
            self.agent,
            session_id=self.session_id,
            status="success" if success else "failed"
        )
        
        # Generate report
        recovery_stats = stats()
        
        # Notify team
        quick_send(
            "FORGE",
            f"Session {status}",
            f"Agent: {self.agent}\n"
            f"Recovery attempts: {recovery_stats['total_attempts']}\n"
            f"Success rate: {recovery_stats['success_rate']:.1%}"
        )

# Usage
agent = TeamBrainAgent("ATLAS")
agent.start_session("Build ErrorRecovery")

success, result = agent.execute(build_tool, "ErrorRecovery")

agent.end_session(success=success)
```

**Result:** Production-grade agent with full tool integration

---

## 📊 RECOMMENDED INTEGRATION PRIORITY

**Week 1 (Essential):**
1. SynapseLink - Team notifications
2. AgentHealth - Health correlation
3. SessionReplay - Debugging

**Week 2 (Productivity):**
4. TaskQueuePro - Task management
5. TokenTracker - Cost tracking
6. ContextCompressor - Token optimization

**Week 3 (Advanced):**
7. CollabSession - Multi-agent coordination
8. MemoryBridge - Shared learnings
9. Full stack integration

---

## 🔧 TROUBLESHOOTING INTEGRATIONS

**Import Errors:**

```python
# Ensure all tools are in Python path
import sys
sys.path.append("C:/Users/logan/OneDrive/Documents/AutoProjects")

# Then import
from errorrecovery import ErrorRecovery
```

**Version Conflicts:**

```bash
# Check versions
errorrecovery --version

# Update if needed
cd AutoProjects/ErrorRecovery
git pull origin main
```

**Configuration Issues:**

```python
# Reset to defaults
import shutil
from pathlib import Path

# Backup and reset
recovery_dir = Path.home() / ".errorrecovery"
if recovery_dir.exists():
    shutil.rmtree(recovery_dir)
```

---

**Last Updated:** January 2026  
**Maintained By:** Forge (Team Brain)
