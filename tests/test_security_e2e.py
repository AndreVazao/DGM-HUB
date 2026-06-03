import sys
import os
from pathlib import Path

# Add src to PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent / "src"))

from dgm_hub.security.policy_engine import PolicyEngine

def test_policy_engine():
    print("Testing Policy Engine...")
    policy = PolicyEngine()

    # Test blocked paths
    assert policy.validate_path(".git/config") == False
    assert policy.validate_path("src/main.py") == True

    # Test allowed tools
    assert policy.validate_tool("cmd_tool") == True
    assert policy.validate_tool("malicious_tool") == False

    print("Policy Engine Test Passed!")

if __name__ == "__main__":
    try:
        test_policy_engine()
        print("\nSecurity tests completed successfully!")
    except Exception as e:
        print(f"\nSecurity tests failed: {e}")
        sys.exit(1)
