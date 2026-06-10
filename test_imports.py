#!/usr/bin/env python3
import sys
sys.stdout.reconfigure(encoding='utf-8')

from dgm_hub.control.workflow_runtime import WorkflowRuntime
from dgm_hub.execution.test_pipeline import TestPipeline
from pathlib import Path
import inspect

# Test 1: Import check
print("[OK] WorkflowRuntime imported successfully")

# Test 2: Create instance
w = WorkflowRuntime()
print(f"[OK] WorkflowRuntime instance created")
print(f"     - TestPipeline instance: {w.tests}")

# Test 3: Check TestPipeline.run signature
sig = inspect.signature(w.tests.run)
print(f"[OK] TestPipeline.run signature: {sig}")

# Test 4: Check WorkflowRuntime.run_tests signature
sig2 = inspect.signature(w.run_tests)
print(f"[OK] WorkflowRuntime.run_tests signature: {sig2}")

print("\n[SUCCESS] All import and signature checks passed!")
