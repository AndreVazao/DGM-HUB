DGM-HUB NEXT CHAT CONTEXT

MISSION
Build a local engineering runtime where conversational AI can safely inspect repositories, propose patches, run tests, execute commands, and operate inside permission boundaries.

CURRENT STATE
- Runtime execution path exists
- Tool layer exists
- Test pipeline exists
- Git integration exists
- Approval gates exist
- Chaos testing completed
- Real repository validation completed
- Benchmark system completed
- Local UI approval flow designed
- Streaming log architecture designed

PRIMARY GOAL NOW
Turn DGM-HUB from validated framework into daily-driver engineering runtime.

EXPECTED WORKFLOW
Conversation
-> Repository Inspection
-> Approval Request
-> Patch / Command / Tests
-> Live Logs
-> Validation
-> Rollback if needed
-> Return Results

IMPORTANT CONSTRAINTS
- No silent modifications
- Approval before impactful actions
- Prefer reliability over autonomy theater
- Everything must be testable locally
- Runtime state isolated from target repositories

ACTIVE FOCUS AREAS
1. Approval UI integration
2. Live execution logs
3. Multi-LLM routing
4. Runtime hardening
5. Real usage loops against actual repositories

SUCCESS CONDITION
A user talks to the system, approves actions, watches logs live, and the system safely edits/tests repositories with rollback capability.
