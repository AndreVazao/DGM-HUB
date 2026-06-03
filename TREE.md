DGM-HUB/
├─ config/
│  ├─ default_config.yaml
│  └─ permissions.yaml
├─ docs/
│  ├─ context/
│  │  ├─ agent_memory.json
│  │  └─ runtime_state.md
│  ├─ ARCHITECTURE.md
│  └─ PROJECT_CONTEXT.md
├─ runtime/
│  ├─ backups/
│  │  ├─ 58cc2111a03217825186ee2945c5fc93750a6437df72aab67a2eeec88799638d.json
│  │  └─ 5e15c5462ca0b54db0979395efeacd7ddfe97f0b1e2abb0fa45e1c7e378542ec.json
│  ├─ genome.json
│  └─ memory.json
├─ src/
│  └─ dgm_hub/
│     ├─ agent/
│     │  ├─ __init__.py
│     │  ├─ active_patch_engine.py
│     │  ├─ architect_mode.py
│     │  ├─ auto_dev.py
│     │  ├─ autonomous_dev.py
│     │  ├─ cognitive_engine.py
│     │  ├─ engine.py
│     │  ├─ evolution_loop.py
│     │  ├─ evolution_orchestrator.py
│     │  ├─ evolution_to_patch.py
│     │  ├─ governor.py
│     │  ├─ self_repair.py
│     │  └─ self_rewriting_engine.py
│     ├─ bridge/
│     │  ├─ __init__.py
│     │  ├─ agent_client.py
│     │  └─ server.py
│     ├─ control/
│     │  ├─ approval_workflow.py
│     │  ├─ manager.py
│     │  ├─ queue.py
│     │  ├─ runtime_session.py
│     │  ├─ task_graph.py
│     │  ├─ task.py
│     │  ├─ tool_contract_layer.py
│     │  ├─ worker.py
│     │  └─ workflow_runtime.py
│     ├─ core/
│     │  ├─ bootstrap.py
│     │  ├─ config.py
│     │  └─ runtime.py
│     ├─ evolution/
│     │  ├─ __init__.py
│     │  ├─ evolution_engine.py
│     │  ├─ execution_genome.py
│     │  └─ mutation_engine.py
│     ├─ execution/
│     │  ├─ command_runner.py
│     │  ├─ diff_engine.py
│     │  ├─ execution_history.py
│     │  ├─ patch_apply.py
│     │  ├─ patch_proposal.py
│     │  ├─ repository_context.py
│     │  └─ test_pipeline.py
│     ├─ mcp/
│     │  ├─ router.py
│     │  └─ server.py
│     ├─ memory/
│     │  ├─ execution_memory.py
│     │  └─ vault.py
│     ├─ security/
│     │  ├─ approval.py
│     │  ├─ audit.py
│     │  ├─ evolution_guard.py
│     │  ├─ patch_authority.py
│     │  ├─ path_guard.py
│     │  └─ permissions.py
│     ├─ swarm/
│     │  ├─ agent_node.py
│     │  ├─ coordinator.py
│     │  ├─ debate_engine.py
│     │  ├─ role_types.py
│     │  ├─ swarm_coordinator.py
│     │  ├─ swarm_loop.py
│     │  ├─ voting_system.py
│     │  └─ worker_node.py
│     ├─ tools/
│     │  ├─ base.py
│     │  ├─ cmd_tool.py
│     │  ├─ contracts.py
│     │  ├─ filesystem_guard.py
│     │  ├─ filesystem_tool.py
│     │  ├─ git_tool.py
│     │  ├─ manager.py
│     │  ├─ powershell_tool.py
│     │  ├─ registry.py
│     │  ├─ repo_tool.py
│     │  └─ test_runner.py
│     ├─ __init__.py
│     └─ main.py
├─ .gitignore
├─ DGM-HUB_CONTEXT.md
├─ DGM-HUB_TREE.txt
├─ logs.txt
├─ pyproject.toml
├─ README.md
├─ run_agent.py
├─ run_cognitive_agent.py
├─ run_task.py
└─ TREE.md
