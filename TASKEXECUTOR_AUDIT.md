# DGM-HUB RUNTIME REALITY AUDIT
## PHASE 5: TASKEXECUTOR AUDIT

**File:** src/dgm_hub/control/task_executor.py  
**Lines:** 86  
**Audit Date:** 2025-06-05

---

## EXECUTIVE SUMMARY

`TaskExecutor` is the **central control point** for all execution in DGM-HUB. Every entrypoint (run_dgm_hub.py, run_cognitive_agent.py, run_agent.py) eventually routes through this single class.

**Critical Role:** Orchestrates repository mutations with safety guardrails.

---

## RESPONSIBILITIES MATRIX

### PRIMARY RESPONSIBILITIES

#### 1. Repository Initialization & Setup
```python
def __init__(self, repository_path: str = "."):
    self.repository_path = Path(repository_path).resolve()
    # Stores resolved repo path
```
**Purpose:** Establish execution context  
**Side Effects:** Creates directories (runtime/journals, runtime/snapshots)  
**Risk Level:** LOW

#### 2. Safety Snapshot Creation
```python
snapshot = self.safety.create_snapshot(str(repo_p))
```
**Purpose:** Backup before execution  
**Operation:**
- Creates UUID-based snapshot directory
- Copies target file/directory to: `runtime/snapshots/{repo_hash}/{uuid}`
- Returns ExecutionSnapshot object

**Side Effects:** Filesystem writes (~copy of entire repo size)  
**Risk Level:** MEDIUM (disk space)

#### 3. Repository Context Generation
```python
context = self.repository.build(str(repo_p))
```
**Purpose:** Introspect repository state  
**Output:**
```python
{
    'root': str,
    'files': list[str],
    'directories': list[str]
}
```
**Side Effects:** Filesystem reads only  
**Risk Level:** LOW

#### 4. Tool Validation & Authorization
```python
if not self.policy.validate_tool(call["name"]):
    raise PermissionError(f"Tool blocked: {call['name']}")
```
**Purpose:** Enforce security policy  
**Operation:** PolicyEngine checks tool name against allowed list  
**Side Effects:** May block execution  
**Risk Level:** LOW

#### 5. Tool Dispatch & Execution
```python
result = self.tools.execute(call["name"], call.get("payload", {}))
```
**Purpose:** Execute requested tools  
**Operation:**
- Delegates to UnifiedToolManager
- UnifiedToolManager dispatches to specific tool implementation
- Each tool is subject to PathGuard constraints

**Side Effects:** **ARBITRARY** — depends on tool
- FilesystemTool: read/write files
- GitTool: modify git state
- CmdTool: execute PowerShell commands
- TestRunnerTool: run subprocess tests
- RepoTool: repository analysis

**Risk Level:** CRITICAL (unrestricted tool execution)

#### 6. Test Pipeline Execution
```python
if test_command:
    test_result = self.runtime.run_tests(test_command, cwd=str(repo_p))
```
**Purpose:** Run arbitrary test commands  
**Operation:**
- Spawns subprocess with shell=True
- No command validation

**Side Effects:** Arbitrary subprocess execution  
**Risk Level:** CRITICAL (shell injection vector)

#### 7. Success Determination
```python
success = test_result.success if test_result is not None else True
```
**Purpose:** Evaluate execution outcome  
**Logic:** If tests run, test result determines success; else defaults to True  
**Risk Level:** LOW

#### 8. Rollback Management
```python
if snapshot:
    self.safety.rollback(snapshot)
```
**Purpose:** Revert filesystem changes on success  
**Operation:** Restores from snapshot via copytree/copy2  
**Timing:** Runs BEFORE returning success result  
**Risk Level:** MEDIUM (can fail silently if backup corrupted)

#### 9. Execution History Recording
```python
self.history.add("task_execute", True)
```
**Purpose:** Track execution success/failure  
**Storage:** In-memory list (lost on process exit)  
**Side Effects:** None (read-only tracking)  
**Risk Level:** LOW

#### 10. Execution Journal Logging
```python
self.journal.log_task_execution(str(repo_p), result)
```
**Purpose:** Persist execution record to JSONL  
**File:** `runtime/journals/{repo_name}_{repo_hash}.jsonl`  
**Contents:** Serialized TaskExecutionResult  
**Side Effects:** Filesystem write  
**Risk Level:** LOW

---

## DEPENDENCY ANALYSIS

### Direct Dependencies (8 modules)

```python
from dgm_hub.execution.execution_history import ExecutionHistory
from dgm_hub.execution.repository_context import RepositoryContextGenerator
from dgm_hub.control.workflow_runtime import WorkflowRuntime
from dgm_hub.tools.unified_tool_manager import UnifiedToolManager
from dgm_hub.security.safe_execution import SafeExecutionManager
from dgm_hub.security.policy_engine import PolicyEngine
from dgm_hub.memory.execution_journal import ExecutionJournal
```

### Transitive Dependencies (10+ additional)
Through UnifiedToolManager:
- FilesystemTool (with PathGuard)
- CmdTool
- PowerShellTool
- RepoTool
- TestRunnerTool
- GitTool (with PathGuard)

Through SafeExecutionManager:
- shutil (standard library)
- uuid
- hashlib

### Initialization Dependency Chain
```
TaskExecutor()
  ├─ WorkflowRuntime()
  │  ├─ RepositoryContextGenerator()
  │  ├─ TestPipeline()
  │  └─ PatchApplyEngine()
  ├─ ExecutionHistory()
  ├─ RepositoryContextGenerator()
  ├─ UnifiedToolManager()
  │  └─ [6 tool implementations + ToolRegistry + PathGuard]
  ├─ PolicyEngine()
  ├─ SafeExecutionManager()
  └─ ExecutionJournal()
```

---

## SIDE EFFECTS ANALYSIS

### Filesystem Mutations

#### Write Operations (High Risk)
1. **Snapshot Creation:** Copies repo (size-dependent)
2. **Journal Logging:** Appends JSONL (small)
3. **Tool Execution:** Tools may modify files
4. **Test Execution:** Tests may modify repo
5. **Rollback:** Restores from snapshot

#### Read Operations
1. **Repository Context:** Lists files/dirs
2. **History Tracking:** Reads in-memory state

### Repository State Mutations

#### Via Tool Execution
- **FilesystemTool:** Read/write files in allowed paths
- **GitTool:** `git add`, `git commit`, `git status` (can modify .git/)
- **CmdTool/PowerShellTool:** Arbitrary shell commands
- **TestRunnerTool:** Subprocess execution (tests may modify state)
- **RepoTool:** Repository analysis (read-only)

#### Via Rollback
- **Snapshot Restoration:** Reverts target to pre-execution state
- **Careful:** Only runs if snapshot exists AND success=True

---

## ROLLBACK INTERACTION ANALYSIS

### Rollback Trigger Logic
```python
if snapshot:  # Line 62
    self.safety.rollback(snapshot)
```

**CRITICAL ISSUE:** Rollback runs AFTER success determination but BEFORE returning result.

**Question:** Why rollback on success? Purpose unclear.

### Rollback Sequence
```
1. Create snapshot (Line 50)
2. Execute tools/tests (Lines 52-60)
3. Check success (Line 61)
4. Rollback snapshot (Line 62)  ← Undoes ALL changes
5. Return success result (Line 65)  ← Returns success=True but repo reverted
```

**Observation:** Rollback ALWAYS executes (lines 62 and 76), meaning:
- **No persistent execution changes** remain after execute()
- Repository is always restored to pre-execution state
- This may be intentional (test-only mode?)
- Or a bug (changes never persisted?)

### Exception Handling Rollback
```python
except Exception as exc:
    if snapshot:
        try: self.safety.rollback(snapshot)
        except: pass  # Silent failure
```

**Risk:** Silent swallow of rollback exceptions (line 75)

---

## SECURITY BOUNDARIES

### PathGuard Integration
```python
self.tools = UnifiedToolManager(allowed_paths=[str(self.repository_path)])
```

**Effect:** FilesystemTool and GitTool constrained to repository_path

**Gaps:**
1. CmdTool and PowerShellTool NOT constrained (arbitrary shell access)
2. TestRunnerTool NOT constrained (subprocess inherits constraints?)

### Policy Engine
```python
if not self.policy.validate_tool(call["name"]):
    raise PermissionError(f"Tool blocked: {call['name']}")
```

**Effect:** Whitelist validation per tool name

**Gaps:**
1. No payload validation (tool parameters unchecked)
2. No operation-level permission (all operations allowed per tool)

### Test Command Execution
```python
subprocess.run(
    command,
    cwd=cwd,
    shell=True,  # ← SHELL INJECTION VECTOR
    capture_output=True,
    text=True
)
```

**Critical Risk:** `shell=True` without command validation/escaping

---

## FAILURE MODE ANALYSIS

### Scenario 1: Snapshot Creation Fails
```python
snapshot = self.safety.create_snapshot(str(repo_p))
# If shutil.copytree() fails:
#   → snapshot = None
#   → Tools execute WITHOUT backup
#   → Rollback skipped (line 62: if snapshot)
#   → No recovery path
```

**Severity:** CRITICAL  
**Impact:** Unprotected execution if backup fails

### Scenario 2: Tool Execution Fails
```python
result = self.tools.execute(...)  # Exception raised
# Caught at line 74
# Rollback executed (line 76)
# Exception returned in result.error
```

**Severity:** LOW  
**Impact:** Handled gracefully with rollback

### Scenario 3: Rollback Fails Silently
```python
except: pass  # Line 75
# Exception in rollback ignored
# Original exception lost
# User sees no error
```

**Severity:** MEDIUM  
**Impact:** Silent data loss risk

### Scenario 4: Test Command Injection
```python
test_command = "; rm -rf /"  # Attacker input
subprocess.run(test_command, shell=True)  # ← Executed
```

**Severity:** CRITICAL  
**Impact:** Arbitrary command execution

---

## ARCHITECTURE RESPONSIBILITIES

### What TaskExecutor SHOULD Own
1. ✅ Execution orchestration
2. ✅ Tool dispatch coordination
3. ✅ Rollback management
4. ✅ Execution logging
5. ✅ Error handling

### What TaskExecutor SHOULD NOT Own
1. ❌ Repository introspection (RepositoryContextGenerator handles this)
2. ❌ Tool implementations (UnifiedToolManager handles)
3. ❌ Security policy (PolicyEngine handles)
4. ❌ Path guarding (PathGuard handles)
5. ❌ Snapshot creation (SafeExecutionManager handles)

**Assessment:** Responsibilities correctly distributed. TaskExecutor is thin orchestrator.

---

## CODE QUALITY OBSERVATIONS

### Strengths
1. ✅ Clean separation of concerns
2. ✅ Defensive exception handling
3. ✅ Snapshot-based safety model
4. ✅ JSONL journaling for auditability
5. ✅ Path resolution normalization

### Weaknesses
1. ❌ Rollback ALWAYS runs (unclear semantics)
2. ❌ Silent exception swallowing in rollback
3. ❌ No validation of tool parameters
4. ❌ No command validation for tests
5. ❌ Repository path re-detection in execute() (lines 44-49)
6. ❌ Hash computation every call (performance)

---

## EXECUTION SEMANTICS CONFUSION

### Unclear: Why Rollback on Success?

**Line 62 always rolls back:**
```python
if snapshot:
    self.safety.rollback(snapshot)
```

**This means:**
- All tool execution changes are reverted
- Test pipeline changes are reverted
- Repository ALWAYS returns to pre-execution state
- But result reports success=True

**Possible Interpretations:**
1. **Test-only mode:** Everything runs but nothing persists (intentional?)
2. **Bug:** Changes should persist but don't
3. **Design:** Safe execution with manual commit elsewhere
4. **Incomplete:** Future versions will have conditional rollback

**Recommendation:** Clarify in code comments or rename to execute_and_rollback()

---

## RECOMMENDATIONS

### KEEP
- ✅ Core orchestration pattern
- ✅ Snapshot/rollback mechanism
- ✅ JSONL journaling
- ✅ Policy validation layer
- ✅ Exception handling structure

### MOVE
- ❌ Tool management → Consider caching UnifiedToolManager (recreate per repo_path is inefficient)
- ❌ Path hashing → Move to SafeExecutionManager
- ❌ Journal path construction → Move to ExecutionJournal

### SPLIT
- ⚠️ Exception handling: Separate success-path from error-path rollback
- ⚠️ Repository path validation: Extract to utility
- ⚠️ Tool execution loop: Extract to separate method

### DELETE
- ❌ Lines 75 silent exception swallow (log or re-raise)
- ❌ Redundant path resolution (lines 44-49 duplicate __init__)
- ❌ Unused imports validation (if any)

### AUDIT REQUIREMENTS
1. **Clarify rollback semantics:** Is this test-only execution?
2. **Add command validation:** Sanitize test_command before subprocess
3. **Fail-fast on snapshot:** Raise exception if snapshot creation fails
4. **Log rollback failures:** Remove silent exception suppression
5. **Add parameter validation:** Validate tool payloads

---

## CRITICAL BUGS TO ADDRESS

### Bug 1: Silent Rollback Failure
**Severity:** CRITICAL  
**Location:** Line 75  
**Issue:**
```python
except: pass
```
**Fix:**
```python
except Exception as rollback_err:
    self.logger.error(f"Rollback failed: {rollback_err}")
    raise RuntimeError(f"Rollback after error failed: {rollback_err}") from exc
```

### Bug 2: Snapshot Creation Not Validated
**Severity:** CRITICAL  
**Location:** Line 50  
**Issue:** If create_snapshot() fails, continue without protection  
**Fix:**
```python
snapshot = self.safety.create_snapshot(str(repo_p))
if not snapshot:
    raise RuntimeError("Failed to create execution snapshot")
```

### Bug 3: Shell Injection Vector
**Severity:** CRITICAL  
**Location:** TestPipeline (not TaskExecutor directly)  
**Issue:** test_command not validated  
**Fix:** Add command validation or use list argument instead of shell

### Bug 4: Unclear Rollback Intent
**Severity:** MEDIUM  
**Location:** Line 62  
**Issue:** Always rollback on success — unclear why  
**Fix:** Add comment explaining test-only semantics or change logic

### Bug 5: Exception Info Lost on Rollback Error
**Severity:** MEDIUM  
**Location:** Lines 74-76  
**Issue:** Original exception overwritten if rollback fails  
**Fix:** Chain exceptions using `raise ... from ...`

---

## TASKEXECUTOR FINAL ASSESSMENT

| Aspect | Status | Score |
|--------|--------|-------|
| Responsibility Clarity | ✅ Good | 8/10 |
| Security | ⚠️ Medium | 5/10 |
| Error Handling | ⚠️ Partial | 6/10 |
| Code Clarity | ✅ Good | 7/10 |
| Test Coverage | ❓ Unknown | ? |
| Documentation | ❌ Low | 3/10 |
| Exception Safety | ❌ Weak | 4/10 |

**Overall:** Core orchestration solid, but security and error handling gaps need attention.

