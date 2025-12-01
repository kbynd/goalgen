Conversation Gist - GoalGen

Context:
- Multi-goal, persistent, cross-device conversation agent using LangGraph and Azure services.
- Evolved to a generator-based project scaffolding system (`goalgen`).

Goals:
1. Persistent multi-goal conversations (long-term memory, multi-device, resumable threads).
2. Goal-oriented architecture (tasks, agents, evaluators, tools, supervisors).
3. Cross-device UX (Teams Bot, Webchat SPA, API, real-time events).
4. Scaffold and code generation (LangGraph, agents, evaluators, API, UX, Bicep infra, deployment, CI/CD, assets).
5. Automation for multi-target deployment with configurable URLs.

Decisions:
1. LangGraph wrapper needed (declarative) for multi-goal workflows.
2. Security: Key Vault + Managed Identity; Cosmos + Redis for sessions.
3. Infra: Bicep per service (Container Apps, Functions, SignalR, Key Vault, Redis, Cosmos).
4. Generator CLI (`goalgen`) orchestrates all sub-generators, template-driven.
5. UX: Teams Bot, Webchat SPA, API endpoint.
6. Workflow: Goal spec -> goalgen -> scaffold code, infra, UX, tools, agents, evaluators.

Feasibilities/Constraints:
1. LangGraph supports graphs, requires wrapper, checkpointing feasible.
2. Azure components feasible; Bicep sufficient.
3. Code generation feasible; assets, prompt templates, deployment scripts auto-generated.
4. UX feasible with Teams + Webchat SPA + Adaptive Cards + SignalR.
5. Limitations: goalgen must exist before generating full projects; agent/task logic manual filling; runtime wiring needed.

Outcomes:
1. GoalGen architecture designed.
2. GoalGen skeleton CLI implemented.
3. GoalGen ZIP scaffold created.
4. Roadmap for full generator defined.
5. Goal spec schema defined.

Next Steps:
1. Implement generator sub-modules.
2. Integrate LangGraph runtime and checkpointers.
3. Generate sample `travel_planning` project.
4. Fill in agent, evaluator, and tool logic.
5. Wire Teams Bot & Webchat SPA.
6. Test CI/CD, deployment, and real-time events.

