# DGM-HUB RUNTIME REALITY AUDIT
## PHASE 3: EXECUTION PATH TRACE

**Audit Date:** 2025-06-05  
**Scope:** Complete execution flow from entrypoint through all major phases

---

## EXECUTION PATH 1: run_dgm_hub.py (Main Agent Loop)

### Entry Point
```
main() in run_dgm_hub.py
  └─ Line 17: argparse.ArgumentParser()
     ├─ Parse --repo (required)
     ├─ Parse --test (optional)
     └─ Parse --mode (default="run")
```

### Phase 1: Bootstrap & Initialization
```
Line 22: AgentLoop()
  │
  ├─ Line 23: RuntimeSession(repository_path=".")
  │   └─ TaskExecutor(repository_path=".")
  │       ├─ Line 26: Path(repository_path).resolve()
  │       │   └─ Store in self.repository_path
  │       ├─ Line 27: WorkflowRuntime()
  │       │   ├─ RepositoryContextGenerator()
  │       │   ├─ TestPipeline()
  │       │   └─ PatchApplyEngine()
  │       ├─ Line 28: ExecutionHistory()
  │       ├─ Line 29: RepositoryContextGenerator()
  │       ├─ Line 30: UnifiedToolManager(allowed_paths=[str(repository_path)])
  │       │   ├─ ToolRegistry()
  │       │   ├─ PathGuard(allowed_paths)
  │       │   ├─ Register: FilesystemTool(guard)
  │       │   ├─ Register: CmdTool()
  │       │   ├─ Register: PowerShellTool()
  │       │   ├─ Register: RepoTool()
  │       │   ├─ Register: TestRunnerTool()
  │       │   └─ Register: GitTool(guard)
  │       ├─ Line 31: PolicyEngine()
  │       ├─ Line 32: SafeExecutionManager(repository_path)
  │       │   └─ Create runtime/snapshots directory
  │       └─ Line 33-37: ExecutionJournal(path)
  │           └─ Create runtime/journals directory
  │
  ├─ Line 24: ToolReasoner()
  ├─ Line 25: PatchOrchestrator()
  │   ├─ PatchIntelligenceEngine()
  │   ├─ ApprovalEngine()
  │   └─ PatchApplyEngine()
  ├─ Line 26: ErrorAnalyzer()
  ├─ Line 27: FileLoader()
  ├─ Line 28: RuntimeLogger()
  │   └─ Create runtime/logs.jsonl
  ├─ Line 29: ReviewGate()
  └─ Line 30: Telemetry()
      └─ Create runtime/telemetry.jsonl
```

### Phase 2: Execution Start
```
Line 25: agent.run(repository_path, test_command)
  │
  ├─ Line 36-37: RuntimeLogger.log("run_start", {...})
  │   └─ Append to runtime/logs.jsonl
  │
  └─ Line 38: Telemetry.emit("run_start", {...})
      └─ Append to runtime/telemetry.jsonl
```

### Phase 3: Repository Analysis
```
Line 41-43: self.runtime.execute_task(repository_path, test_command)
  │
  └─ RuntimeSession.execute_task()
     │
     └─ TaskExecutor.execute(repository_path, test_command, tool_calls=None)
        │
        ├─ Line 50: SafeExecutionManager.create_snapshot(repo_path)
        │   ├─ Generate UUID for snapshot_id
        │   ├─ Create runtime/snapshots/{repo_hash}/{uuid}
        │   └─ Return ExecutionSnapshot
        │
        ├─ Line 52: RepositoryContextGenerator.build(repo_path)
        │   ├─ List all files in root
        │   ├─ List all directories in root
        │   └─ Return: {root, files[], directories[]}
        │
        └─ Return: execution object with context, test_result
```

### Phase 4: Tool Reasoning
```
Line 44: context = execution.repository_context
│
Line 45: tool_calls = self.reasoner.decide_tools(context)
│
└─ ToolReasoner.decide_tools(context)
   │
   ├─ Check if ".git" in directories
   │   └─ Append: {name: "git_tool", payload: {operation: "status", ...}}
   │
   ├─ Check if len(files) > 10 OR len(directories) > 5
   │   └─ Append: {name: "repo_tool", payload: {operation: "summary", ...}}
   │
   └─ Return: list of tool_calls
```

### Phase 5: Tool Execution
```
Line 46-48: self.runtime.executor.execute(repository_path, tool_calls)
│
└─ TaskExecutor.execute(repository_path, tool_calls=tool_calls)
   │
   ├─ Line 57-60: For each tool_call in tool_calls:
   │   │
   │   ├─ PolicyEngine.validate_tool(call["name"])
   │   │   └─ Check if tool is permitted
   │   │
   │   ├─ UnifiedToolManager.execute(call["name"], call.get("payload", {}))
   │   │   │
   │   │   └─ ToolRegistry.get(name)
   │   │       ├─ If "git_tool": GitTool.execute(operation="status", ...)
   │   │       ├─ If "repo_tool": RepoTool.execute(operation="summary", ...)
   │   │       └─ Call tool with payload as kwargs
   │   │
   │   └─ Append to tool_results: {tool: name, result: result}
   │
   └─ Return: TaskExecutionResult with tool_results
```

### Phase 6: Test Execution
```
Line 61-62: If test_command:
│
└─ self.runtime.run_tests(test_command, cwd=repository_path)
   │
   └─ WorkflowRuntime.run_tests(command, cwd)
      │
      └─ TestPipeline.run(command, cwd)
         │
         ├─ subprocess.run(command, cwd=cwd, shell=True, capture_output=True)
         │
         └─ Return: TestResult(passed=returncode==0, output, return_code)
```

### Phase 7: Error Analysis & Patching
```
Line 65-76: If test_result.success == False:
│
├─ Line 66: self.errors.parse(test_output)
│   │
│   └─ ErrorAnalyzer.parse(output)
│       ├─ regex: File "(.+?)" → extract file
│       ├─ regex: line (\d+) → extract line
│       ├─ Split by \n and take last line
│       └─ Return: ParsedError(file, line, message, raw)
│
├─ Line 68: if error.file: self.files.read(error.file)
│   │
│   └─ FileLoader.read(path)
│       └─ Return: file content as string
│
└─ Line 69-73: self.patcher.execute_fix(...)
   │
   └─ PatchOrchestrator.execute_fix(file_path, original_code, error, line)
      │
      ├─ Line 13: self.generator.propose_patch(file_path, code, error, line)
      │   │
      │   └─ PatchIntelligenceEngine.propose_patch()
      │       └─ Return: patch_proposal
      │
      ├─ Line 15: self.approval.requires_approval(proposal)
      │   │
      │   └─ ApprovalEngine.requires_approval()
      │       └─ Return: bool
      │
      ├─ If approval required (Line 16-18):
      │   └─ Return: {status: "pending", proposal: proposal}
      │
      └─ Else (Line 20):
          ├─ self.applier.apply(proposal)
          │   └─ PatchApplyEngine.apply(proposal)
          │       └─ Write patched code to file
          └─ Return: {status: "applied", proposal: proposal}
```

### Phase 8: Approval Gate Check
```
Line 78-88: If self.review_gate.requires_human_approval(patch_result):
│
└─ ReviewGate.requires_human_approval(patch_result)
   │
   ├─ If patch_result is None: return False
   ├─ If is dict and status=="pending": return True
   └─ Else: return False
   │
   └─ If True:
      ├─ Telemetry.emit("run_end", {status: "pending_review"})
      └─ Return AgentResult with status="pending_review"
```

### Phase 9: Metrics & Logging
```
Line 89-93: Else (no approval needed):
│
├─ Build metrics dict:
│   ├─ "tools_executed": count of tool_results
│   └─ "patch_generated": bool
│
├─ RuntimeLogger.log("run_end", {success, patch})
│
├─ Telemetry.emit("run_end", {success, patch})
│
└─ Return AgentResult with all fields
```

### Phase 10: Exception Handling
```
Line 94-108: If Exception in try block:
│
├─ SafeExecutionManager.rollback(snapshot)
│   ├─ If target is dir: shutil.rmtree(target), copytree(backup, target)
│   └─ If file: shutil.copy2(backup, target)
│
├─ ExecutionHistory.add("task_execute", False)
│
├─ RuntimeLogger.log("run_end", {success: False, error})
│
├─ Telemetry.emit("run_end", {success: False, error})
│
└─ Return AgentResult(success=False, error=str(exc))
```

### Output
```
print("\n===== DGM-HUB RESULT =====\n")
print("SUCCESS:", result.success)
print("\nCONTEXT:", result.context)
print("\nTOOL RESULTS:", result.tool_results)
print("\nTEST RESULT:", result.test_result)
print("\nPATCH:", result.patch_result)
if result.error:
    print("\nERROR:", result.error)
```

---

## EXECUTION PATH 2: run_cognitive_agent.py (Learning Loop)

### Entry Point & Config Loading
```
main() in run_cognitive_agent.py
  │
  ├─ Line 18-23: ConfigLoader(config_path).load()
  │   └─ yaml.load(config_file)
  │       └─ Return: dict config
  │
  └─ Line 25: build_runtime(config)
```

### Runtime Building
```
build_runtime(config) in dgm_hub.core.bootstrap
  │
  ├─ Line 10: Runtime()
  │   └─ Create runtime.registry (ToolRegistry)
  │
  ├─ Line 12: PathGuard(config["allowed_paths"])
  │
  ├─ Line 16: runtime.registry.register(FilesystemTool(guard))
  ├─ Line 19: runtime.registry.register(PowerShellTool())
  ├─ Line 22: runtime.registry.register(CmdTool())
  ├─ Line 25: runtime.registry.register(RepoTool())
  ├─ Line 28: runtime.registry.register(TestRunnerTool())
  ├─ Line 31: runtime.registry.register(GitTool(guard))
  │
  └─ runtime.start() [if implemented]
```

### Agent Initialization & Loop
```
CognitiveAgent(runtime) initialization
  │
  ├─ self.runtime = runtime
  ├─ self.repo_root = Path.cwd()
  └─ self.evolution = EvolutionEngine()
      ├─ ExecutionGenome()
      └─ MutationEngine()
```

### Main Loop Execution
```
agent.run(objective, max_iterations=6)
  │
  └─ For iteration in range(max_iterations):
     │
     ├─ If plan is None:
     │   │
     │   └─ Line 52: _plan(objective, state)
     │       │
     │       ├─ Check if "git" in objective.lower()
     │       │   └─ Return: {tool: "git", operation: "status"}
     │       │
     │       ├─ Check if "repo" or "inspect" in objective.lower()
     │       │   └─ Return: {tool: "repo", operation: "tree"}
     │       │
     │       ├─ Check if "hello" in objective.lower()
     │       │   └─ Return: {tool: "cmd", command: "echo hello"}
     │       │
     │       └─ Default: {tool: "git", operation: "status"}
     │
     ├─ Line 54: _execute(plan)
     │   │
     │   ├─ Line 106: tool_name = plan["tool"]
     │   ├─ Line 107: plan_args = {all except "tool"}
     │   │
     │   ├─ Line 109: args = runtime.contract_layer.resolve(tool_name, plan_args)
     │   │   └─ [CONTRACT LAYER - patches plan arguments]
     │   │
     │   ├─ Line 111: tool = runtime.registry.get(tool_name)
     │   │
     │   ├─ Line 113: if tool is None: raise ValueError
     │   │
     │   └─ Line 115: return tool.execute(**args)
     │
     ├─ Line 56-59: Append to steps with result
     │
     ├─ Line 61: state.success = True
     │
     ├─ Line 63-68: self.evolution.learn(objective, plan, True, result)
     │   │
     │   └─ ExecutionGenome.store(objective, plan, success, score, result)
     │       └─ Store successful plan in genome
     │
     └─ Line 70: return state
   
   On Exception:
   │
   ├─ Line 71-80: Append error to steps
   ├─ Line 82: state.fixes += 1
   │
   ├─ Line 84-89: self.evolution.learn(objective, plan, False, {error})
   │   └─ ExecutionGenome.store() for failed attempt
   │
   ├─ Line 91-93: plan = self.evolution.evolve_plan(plan, failed=True)
   │   │
   │   └─ MutationEngine.mutate(plan)
   │       └─ Return: mutated plan (retry with variation)
   │
   └─ Continue to next iteration
```

### Output
```
print("\n====================")
print("COGNITIVE RESULT")
print("====================")
print("SUCCESS:", result.success)
print("FIXES:", result.fixes)
for s in result.steps:
    print(s)
```

---

## EXECUTION PATH 3: run_agent.py (HTTP Bridge)

### Entry Point
```
main() in run_agent.py
  │
  ├─ Line 8: AgentClient(base_url="http://127.0.0.1:8000")
  │
  ├─ Line 20: agent.execute_loop(objective, max_iters=5)
  │
  └─ For i in range(max_iters):
     │
     ├─ Line 27: result = agent.run_task(objective)
     │   │
     │   └─ AgentClient.run_task(objective)
     │       │
     │       ├─ payload = {objective: objective}
     │       │
     │       ├─ requests.post(f"{base_url}/run", json=payload)
     │       │   └─ HTTP POST to bridge server /run endpoint
     │       │
     │       └─ Return: response.json()
     │
     ├─ Line 29: state["iterations"].append(result)
     │
     ├─ Line 31-34: if result.get("status") == "ok" and "error" not in result:
     │   │
     │   └─ print("[LOOP] success detected")
     │   └─ break
     │
     └─ Line 36: time.sleep(1)
        └─ Retry delay
```

### Output
```
return state = {
    "objective": str,
    "iterations": [result1, result2, ...]
}
```

---

## EXECUTION PATH 4: run_ui.py (Server)

### Entry Point
```
uvicorn.run(
    "dgm_hub.ui.server:app",
    host="127.0.0.1",
    port=8765,
    reload=False
)

Server starts at: http://127.0.0.1:8765
```

---

## SNAPSHOT & ROLLBACK MECHANISM

### Snapshot Creation
```
SafeExecutionManager.create_snapshot(target_path)
  │
  ├─ snapshot_id = uuid.uuid4()
  ├─ backup_path = snapshots_dir / snapshot_id
  │
  ├─ If target.is_dir():
  │   └─ shutil.copytree(target, backup_path)
  │
  ├─ Else:
  │   └─ shutil.copy2(target, backup_path)
  │
  └─ Return: ExecutionSnapshot(id, path, backup_path)
```

### Rollback Execution
```
SafeExecutionManager.rollback(snapshot)
  │
  ├─ target = Path(snapshot.path)
  ├─ backup = Path(snapshot.backup_path)
  │
  ├─ If target.is_dir():
  │   ├─ shutil.rmtree(target)
  │   └─ shutil.copytree(backup, target)
  │
  └─ Else:
      └─ shutil.copy2(backup, target)
```

---

## LOGGING & TELEMETRY CHANNELS

### Execution Logs (runtime/logs.jsonl)
```json
{
  "timestamp": "ISO8601",
  "event": "run_start" | "run_end" | ...,
  "data": {...}
}
```

### Telemetry (runtime/telemetry.jsonl)
```json
{
  "time": "ISO8601",
  "event": "run_start" | "run_end" | ...,
  "data": {...}
}
```

### Execution Journal (runtime/journals/*.jsonl)
```json
{
  "type": "plan" | "result" | "task_execution",
  "timestamp": "ISO8601",
  "data": {...}
}
```

---

## SEQUENCE DIAGRAM: Complete Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ USER STARTS: python run_dgm_hub.py --repo . --test "pytest"    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                    [BOOTSTRAP]
                    │
                    ├─ enable_src_imports()
                    ├─ import AgentLoop
                    └─ All components initialized
                         │
                         ▼
                  ┌──────────────────┐
                  │  AgentLoop.run() │
                  └────────┬─────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
    ┌────────┐      ┌─────────┐        ┌────────────┐
    │ LOG    │      │SNAPSHOT │        │REPOSITORY  │
    │(START) │      │(CREATE) │        │CONTEXT     │
    └────────┘      └─────────┘        └────────────┘
                           │                  │
                           └──────────┬───────┘
                                      ▼
                           ┌────────────────────┐
                           │ ToolReasoner.      │
                           │ decide_tools()     │
                           └─────────┬──────────┘
                                     │
                                     ▼
                           ┌────────────────────┐
                           │ UnifiedToolManager │
                           │ .execute()         │
                           └─────────┬──────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
              [GIT TOOL]      [REPO TOOL]      [OTHER TOOLS]
                    │                │                │
                    └────────────────┼────────────────┘
                                     │
                                     ▼
                           ┌────────────────────┐
                           │ TestPipeline.run() │
                           │ (subprocess)       │
                           └─────────┬──────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                                 │
              ┌─────▼─────┐                    ┌─────▼─────┐
              │TESTS PASS │                    │TESTS FAIL │
              └─────┬─────┘                    └─────┬─────┘
                    │                               │
                    │                         ┌─────▼──────────┐
                    │                         │ErrorAnalyzer.  │
                    │                         │parse()         │
                    │                         └─────┬──────────┘
                    │                               │
                    │                         ┌─────▼──────────┐
                    │                         │Patch.generate()│
                    │                         └─────┬──────────┘
                    │                               │
                    │                    ┌──────────┼──────────┐
                    │                    │                     │
                    │              ┌─────▼────────┐    ┌──────▼────────┐
                    │              │APPROVAL      │    │AUTO-APPLY     │
                    │              │REQUIRED?     │    │               │
                    │              └─────┬────────┘    └──────┬────────┘
                    │                    │                    │
                    │              ┌─────▼────────┐           │
                    │              │PENDING_      │           │
                    │              │REVIEW        │           │
                    │              └─────┬────────┘           │
                    │                    │                    │
                    └────────────────┬───┴────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
            ┌─────────────┐    ┌───────────┐    ┌──────────┐
            │ROLLBACK     │    │METRICS    │    │LOG END   │
            │SNAPSHOT     │    │COLLECTION │    │TELEMETRY │
            └─────────────┘    └───────────┘    └──────────┘
                    │                │                │
                    └────────────────┼────────────────┘
                                     │
                                     ▼
                          ┌────────────────────┐
                          │ RETURN AgentResult │
                          └────────────────────┘
                                     │
                                     ▼
                          ┌────────────────────┐
                          │ PRINT RESULTS      │
                          └────────────────────┘
```

