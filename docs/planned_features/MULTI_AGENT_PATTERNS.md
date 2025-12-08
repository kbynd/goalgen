# Multi-Agentic AI Patterns and LangGraph Topologies

Research and analysis of multi-agent patterns for GoalGen implementation.

---

## Overview

Multi-agent systems coordinate multiple AI agents to solve complex tasks. LangGraph provides flexible topologies for implementing these patterns. GoalGen should support generating code for all common patterns based on the goal spec.

---

## LangGraph Core Concepts

### State Graph
- **Nodes**: Functions that process state
- **Edges**: Connections between nodes (conditional or fixed)
- **State**: Shared data structure (typed dict or Pydantic model)
- **Checkpointer**: Persists state between invocations

### Execution Flow
1. Start at entry node
2. Execute node function
3. Update state
4. Route to next node based on edges
5. Repeat until END node or max iterations

---

## Pattern 1: Sequential Chain (Linear Pipeline)

### Description
Agents execute in a fixed sequence, each processing the output of the previous.

### Use Cases
- Data transformation pipelines
- Multi-step document processing
- Sequential validation workflows

### LangGraph Topology
```
START → Agent1 → Agent2 → Agent3 → END
```

### Implementation
```python
from langgraph.graph import StateGraph, END

graph = StateGraph(State)

# Add nodes
graph.add_node("agent1", agent1_node)
graph.add_node("agent2", agent2_node)
graph.add_node("agent3", agent3_node)

# Add edges (sequential)
graph.set_entry_point("agent1")
graph.add_edge("agent1", "agent2")
graph.add_edge("agent2", "agent3")
graph.add_edge("agent3", END)

app = graph.compile()
```

### Goal Spec Configuration
```json
{
  "topology": "sequential",
  "tasks": [
    {"id": "extract_info", "agent": "extractor"},
    {"id": "validate_data", "agent": "validator"},
    {"id": "format_output", "agent": "formatter"}
  ]
}
```

### Advantages
- Simple, predictable flow
- Easy to debug
- Clear responsibility boundaries

### Disadvantages
- No parallelization
- Blocked by slow agents
- Limited flexibility

---

## Pattern 2: Router (Conditional Branching)

### Description
A supervisor/router agent decides which specialist agent to invoke based on input or state.

### Use Cases
- Intent-based routing
- Domain-specific task delegation
- Multi-skill chatbots

### LangGraph Topology
```
            ┌→ Agent1 ┐
START → Router ─→ Agent2 ├→ END
            └→ Agent3 ┘
```

### Implementation
```python
def router_node(state):
    """Routes to specialist based on intent"""
    intent = classify_intent(state["messages"][-1])

    if intent == "flight":
        return "flight_agent"
    elif intent == "hotel":
        return "hotel_agent"
    else:
        return "general_agent"

graph = StateGraph(State)

graph.add_node("router", router_node)
graph.add_node("flight_agent", flight_agent_node)
graph.add_node("hotel_agent", hotel_agent_node)
graph.add_node("general_agent", general_agent_node)

graph.set_entry_point("router")

# Conditional edges
graph.add_conditional_edges(
    "router",
    router_node,  # Returns next node name
    {
        "flight_agent": "flight_agent",
        "hotel_agent": "hotel_agent",
        "general_agent": "general_agent"
    }
)

# All agents return to END
graph.add_edge("flight_agent", END)
graph.add_edge("hotel_agent", END)
graph.add_edge("general_agent", END)

app = graph.compile()
```

### Goal Spec Configuration
```json
{
  "topology": "router",
  "router": {
    "type": "llm_router",
    "routing_prompt": "Classify user intent...",
    "routes": {
      "flight": "flight_agent",
      "hotel": "hotel_agent",
      "general": "general_agent"
    }
  },
  "agents": {
    "flight_agent": {...},
    "hotel_agent": {...},
    "general_agent": {...}
  }
}
```

### Advantages
- Specialist agents for domains
- Efficient resource use
- Scalable (add more specialists)

### Disadvantages
- Router is single point of failure
- No agent collaboration
- Classification errors propagate

---

## Pattern 3: Supervisor + Workers (Hierarchical)

### Description
A supervisor agent coordinates multiple worker agents, can reassign tasks, and aggregates results.

### Use Cases
- Complex research tasks
- Multi-document analysis
- Parallel task execution

### LangGraph Topology
```
             ┌→ Worker1 ─┐
START → Supervisor ─→ Worker2 ─┤→ Supervisor → END
             └→ Worker3 ─┘
```

### Implementation
```python
def supervisor_node(state):
    """Coordinates workers, decides next action"""
    if not state.get("tasks_assigned"):
        # First call: assign tasks to workers
        return {
            "next": "parallel_workers",
            "tasks": ["task1", "task2", "task3"]
        }

    if all_workers_complete(state):
        # All done, aggregate results
        return {"next": END, "final_result": aggregate(state["results"])}

    # Continue coordinating
    return {"next": "supervisor"}

def worker_node(worker_id):
    def node(state):
        task = state["tasks"][worker_id]
        result = execute_task(task)
        return {"results": {worker_id: result}}
    return node

graph = StateGraph(State)

graph.add_node("supervisor", supervisor_node)
graph.add_node("worker1", worker_node(0))
graph.add_node("worker2", worker_node(1))
graph.add_node("worker3", worker_node(2))

graph.set_entry_point("supervisor")

graph.add_conditional_edges(
    "supervisor",
    lambda state: state.get("next", END),
    {
        "parallel_workers": ["worker1", "worker2", "worker3"],  # Parallel execution
        END: END
    }
)

# Workers return to supervisor
graph.add_edge("worker1", "supervisor")
graph.add_edge("worker2", "supervisor")
graph.add_edge("worker3", "supervisor")

app = graph.compile()
```

### Goal Spec Configuration
```json
{
  "topology": "supervisor",
  "supervisor": {
    "agent": "supervisor_agent",
    "max_iterations": 10,
    "aggregation_strategy": "majority_vote"
  },
  "workers": [
    {"id": "worker1", "agent": "research_agent", "capability": "web_search"},
    {"id": "worker2", "agent": "research_agent", "capability": "document_analysis"},
    {"id": "worker3", "agent": "research_agent", "capability": "data_extraction"}
  ]
}
```

### Advantages
- Parallel execution
- Dynamic task allocation
- Centralized coordination

### Disadvantages
- Supervisor complexity
- Synchronization overhead
- Potential bottleneck

---

## Pattern 4: Collaborative (Agent-to-Agent Communication)

### Description
Agents can communicate directly, negotiate, and collaborate without central coordinator.

### Use Cases
- Multi-agent debates
- Consensus building
- Distributed problem solving

### LangGraph Topology
```
        ┌─────────┐
    ┌→ Agent1 ←─┐ │
START ─┤  ↓   ↑   ├→ END
    └→ Agent2 ←─┘
        └─────────┘
```

### Implementation
```python
def agent1_node(state):
    """Agent 1 processes and may send message to Agent 2"""
    result = agent1.invoke(state)

    if needs_agent2_input(result):
        return {
            "next": "agent2",
            "agent1_output": result,
            "message_to_agent2": "Please review..."
        }
    else:
        return {"next": END, "final_output": result}

def agent2_node(state):
    """Agent 2 processes and may send back to Agent 1"""
    result = agent2.invoke(state["message_to_agent2"])

    if needs_agent1_review(result):
        return {
            "next": "agent1",
            "agent2_output": result,
            "message_to_agent1": "Here's my analysis..."
        }
    else:
        return {"next": END, "final_output": result}

graph = StateGraph(State)

graph.add_node("agent1", agent1_node)
graph.add_node("agent2", agent2_node)

graph.set_entry_point("agent1")

# Bidirectional edges
graph.add_conditional_edges(
    "agent1",
    lambda state: state.get("next"),
    {"agent2": "agent2", END: END}
)

graph.add_conditional_edges(
    "agent2",
    lambda state: state.get("next"),
    {"agent1": "agent1", END: END}
)

app = graph.compile(checkpointer=checkpointer)
```

### Goal Spec Configuration
```json
{
  "topology": "collaborative",
  "agents": {
    "agent1": {
      "can_communicate_with": ["agent2"],
      "max_exchanges": 5
    },
    "agent2": {
      "can_communicate_with": ["agent1"],
      "max_exchanges": 5
    }
  },
  "termination": {
    "type": "consensus",
    "threshold": 0.8
  }
}
```

### Advantages
- Rich agent interactions
- Emergent behaviors
- No single point of failure

### Disadvantages
- Complex to implement
- Hard to predict/debug
- Potential infinite loops

---

## Pattern 5: Map-Reduce (Parallel Processing + Aggregation)

### Description
Split task into parallel subtasks, process independently, then aggregate results.

### Use Cases
- Batch document processing
- Multi-source data aggregation
- Parallel API calls

### LangGraph Topology
```
           ┌→ Map1 ─┐
START → Split ─→ Map2 ─┤→ Reduce → END
           └→ Map3 ─┘
```

### Implementation
```python
def split_node(state):
    """Split input into chunks"""
    chunks = split_into_chunks(state["input"], chunk_size=1000)
    return {"chunks": chunks, "next": "map_parallel"}

def map_node(chunk_id):
    """Process individual chunk"""
    def node(state):
        chunk = state["chunks"][chunk_id]
        result = process_chunk(chunk)
        return {f"result_{chunk_id}": result}
    return node

def reduce_node(state):
    """Aggregate all results"""
    results = [state[f"result_{i}"] for i in range(len(state["chunks"]))]
    final = aggregate_results(results)
    return {"final_output": final, "next": END}

graph = StateGraph(State)

graph.add_node("split", split_node)
graph.add_node("map1", map_node(0))
graph.add_node("map2", map_node(1))
graph.add_node("map3", map_node(2))
graph.add_node("reduce", reduce_node)

graph.set_entry_point("split")

# Parallel map execution
graph.add_edge("split", ["map1", "map2", "map3"])

# All map nodes go to reduce
graph.add_edge(["map1", "map2", "map3"], "reduce")
graph.add_edge("reduce", END)

app = graph.compile()
```

### Goal Spec Configuration
```json
{
  "topology": "map_reduce",
  "map": {
    "agent": "processor_agent",
    "parallelism": "auto",
    "chunk_strategy": "size",
    "chunk_size": 1000
  },
  "reduce": {
    "agent": "aggregator_agent",
    "strategy": "concatenate"
  }
}
```

### Advantages
- Maximum parallelization
- Scalable to large datasets
- Well-understood pattern

### Disadvantages
- Requires splittable tasks
- Reduce can be bottleneck
- Overhead of chunking

---

## Pattern 6: Human-in-the-Loop (Interactive)

### Description
Workflow pauses for human input, approval, or correction before continuing.

### Use Cases
- Approval workflows
- Quality review
- Ambiguity resolution

### LangGraph Topology
```
START → Agent → HumanApproval → Agent → END
                     ↓
                  Reject
                     ↓
                   Agent (retry)
```

### Implementation
```python
from langgraph.checkpoint import MemorySaver

def agent_node(state):
    result = agent.invoke(state)
    return {"draft": result, "next": "human_review"}

def human_review_node(state):
    """This node raises an interrupt for human input"""
    raise NodeInterrupt(f"Please review: {state['draft']}")

graph = StateGraph(State)

graph.add_node("agent", agent_node)
graph.add_node("human_review", human_review_node)

graph.set_entry_point("agent")
graph.add_edge("agent", "human_review")

# Configure interrupts
app = graph.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["human_review"]
)

# Usage
config = {"configurable": {"thread_id": "123"}}

# First invocation - stops at human_review
result = app.invoke({"input": "..."}, config)

# Human provides feedback
app.update_state(config, {"human_feedback": "Approved"})

# Continue execution
result = app.invoke(None, config)
```

### Goal Spec Configuration
```json
{
  "topology": "human_in_loop",
  "interrupts": [
    {
      "after_node": "draft_generator",
      "prompt": "Review the generated draft",
      "actions": ["approve", "reject", "edit"]
    }
  ],
  "retry_on_reject": true,
  "max_retries": 3
}
```

### Advantages
- Human oversight
- Quality control
- Handles ambiguity

### Disadvantages
- Not fully autonomous
- Latency waiting for human
- Requires UI for input

---

## Pattern 7: Recursive (Self-Improving)

### Description
Agent can invoke itself recursively to break down complex problems.

### Use Cases
- Problem decomposition
- Hierarchical planning
- Iterative refinement

### LangGraph Topology
```
START → Agent → [Recurse?] → Agent → END
                     ↓
                   Agent (recursive call)
```

### Implementation
```python
def recursive_agent_node(state, depth=0):
    """Agent that can recurse on complex problems"""

    if is_simple(state["problem"]) or depth >= MAX_DEPTH:
        # Base case: solve directly
        solution = solve_simple(state["problem"])
        return {"solution": solution, "next": END}

    # Recursive case: decompose
    subproblems = decompose(state["problem"])

    # Solve each subproblem recursively
    subsolutions = []
    for subproblem in subproblems:
        result = recursive_agent_node(
            {"problem": subproblem},
            depth=depth + 1
        )
        subsolutions.append(result["solution"])

    # Combine subsolutions
    solution = combine(subsolutions)
    return {"solution": solution, "next": END}

graph = StateGraph(State)
graph.add_node("recursive_agent", recursive_agent_node)
graph.set_entry_point("recursive_agent")

graph.add_conditional_edges(
    "recursive_agent",
    lambda state: state.get("next", END),
    {END: END, "recursive_agent": "recursive_agent"}
)

app = graph.compile()
```

### Goal Spec Configuration
```json
{
  "topology": "recursive",
  "agent": "decomposer_agent",
  "recursion": {
    "max_depth": 5,
    "base_case": "is_simple",
    "combine_strategy": "hierarchical_merge"
  }
}
```

### Advantages
- Handles complex problems
- Natural problem decomposition
- Scales with complexity

### Disadvantages
- Stack depth limits
- Hard to debug
- Can be expensive

---

## Pattern 8: Ensemble (Multi-Model Consensus)

### Description
Multiple agents/models solve same problem, results are aggregated via voting or consensus.

### Use Cases
- High-stakes decisions
- Bias mitigation
- Robustness improvement

### LangGraph Topology
```
         ┌→ Agent1 ─┐
START ─→ ├→ Agent2 ─┤→ Consensus → END
         └→ Agent3 ─┘
```

### Implementation
```python
def agent_node(model_name):
    """Create agent with specific model"""
    def node(state):
        agent = create_agent(model_name)
        result = agent.invoke(state["input"])
        return {f"result_{model_name}": result}
    return node

def consensus_node(state):
    """Aggregate results from all agents"""
    results = [
        state["result_gpt4"],
        state["result_claude"],
        state["result_gemini"]
    ]

    # Voting strategy
    final = majority_vote(results)

    # Or consensus strategy
    # final = find_consensus(results, threshold=0.8)

    return {"final_result": final, "confidence": calculate_confidence(results)}

graph = StateGraph(State)

graph.add_node("gpt4_agent", agent_node("gpt-4"))
graph.add_node("claude_agent", agent_node("claude-3"))
graph.add_node("gemini_agent", agent_node("gemini-pro"))
graph.add_node("consensus", consensus_node)

graph.set_entry_point(["gpt4_agent", "claude_agent", "gemini_agent"])  # Parallel start

graph.add_edge(["gpt4_agent", "claude_agent", "gemini_agent"], "consensus")
graph.add_edge("consensus", END)

app = graph.compile()
```

### Goal Spec Configuration
```json
{
  "topology": "ensemble",
  "models": [
    {"name": "gpt4", "provider": "openai", "model": "gpt-4"},
    {"name": "claude", "provider": "anthropic", "model": "claude-3-opus"},
    {"name": "gemini", "provider": "google", "model": "gemini-pro"}
  ],
  "consensus": {
    "strategy": "majority_vote",
    "min_agreement": 0.67
  }
}
```

### Advantages
- Robust results
- Mitigates model bias
- High confidence outputs

### Disadvantages
- Expensive (multiple LLM calls)
- Slower execution
- Conflicts possible

---

## Pattern 9: Reflection (Self-Critique)

### Description
Agent generates output, then critiques and refines it iteratively.

### Use Cases
- Content generation
- Code generation with review
- Essay writing

### LangGraph Topology
```
START → Generate → Critique → [Good?] → END
                       ↓
                    Refine → Critique
```

### Implementation
```python
def generate_node(state):
    """Generate initial output"""
    output = generator_agent.invoke(state["input"])
    return {"draft": output, "iteration": 0, "next": "critique"}

def critique_node(state):
    """Critique the current draft"""
    draft = state["draft"]
    critique = critic_agent.invoke(f"Review: {draft}")

    score = extract_score(critique)

    if score >= THRESHOLD or state["iteration"] >= MAX_ITERATIONS:
        return {"next": END, "final_output": draft}
    else:
        return {
            "next": "refine",
            "critique": critique,
            "score": score
        }

def refine_node(state):
    """Refine based on critique"""
    refined = refiner_agent.invoke({
        "draft": state["draft"],
        "critique": state["critique"]
    })

    return {
        "draft": refined,
        "iteration": state["iteration"] + 1,
        "next": "critique"
    }

graph = StateGraph(State)

graph.add_node("generate", generate_node)
graph.add_node("critique", critique_node)
graph.add_node("refine", refine_node)

graph.set_entry_point("generate")

graph.add_conditional_edges(
    "critique",
    lambda state: state.get("next"),
    {"refine": "refine", END: END}
)

graph.add_edge("refine", "critique")

app = graph.compile()
```

### Goal Spec Configuration
```json
{
  "topology": "reflection",
  "stages": {
    "generate": {"agent": "generator_agent"},
    "critique": {"agent": "critic_agent", "scoring": true},
    "refine": {"agent": "refiner_agent"}
  },
  "termination": {
    "min_score": 0.8,
    "max_iterations": 3
  }
}
```

### Advantages
- Improved output quality
- Self-correcting
- Works with single model

### Disadvantages
- More LLM calls
- Slower execution
- May not always improve

---

## Pattern 10: Plan-Execute (Strategic Planning)

### Description
Planner creates a plan, executor carries it out, monitor tracks progress.

### Use Cases
- Complex workflows
- Multi-step tasks
- Goal achievement

### LangGraph Topology
```
START → Planner → Executor → Monitor → [Done?] → END
                     ↑            ↓
                     └─ Replan ←─┘
```

### Implementation
```python
def planner_node(state):
    """Create execution plan"""
    plan = planner_agent.invoke(state["goal"])
    steps = parse_plan(plan)
    return {
        "plan": plan,
        "steps": steps,
        "current_step": 0,
        "next": "executor"
    }

def executor_node(state):
    """Execute current step"""
    step = state["steps"][state["current_step"]]
    result = executor_agent.invoke(step)

    return {
        "step_results": state.get("step_results", []) + [result],
        "current_step": state["current_step"] + 1,
        "next": "monitor"
    }

def monitor_node(state):
    """Monitor progress and decide next action"""
    if state["current_step"] >= len(state["steps"]):
        # All steps complete
        return {"next": END, "final_result": aggregate(state["step_results"])}

    # Check if current step succeeded
    last_result = state["step_results"][-1]

    if is_success(last_result):
        # Continue to next step
        return {"next": "executor"}
    else:
        # Need to replan
        return {"next": "replan"}

def replan_node(state):
    """Adjust plan based on failures"""
    context = {
        "original_plan": state["plan"],
        "completed_steps": state["step_results"],
        "failed_step": state["steps"][state["current_step"] - 1]
    }

    new_plan = replanner_agent.invoke(context)
    new_steps = parse_plan(new_plan)

    return {
        "plan": new_plan,
        "steps": new_steps,
        "current_step": 0,  # Restart
        "next": "executor"
    }

graph = StateGraph(State)

graph.add_node("planner", planner_node)
graph.add_node("executor", executor_node)
graph.add_node("monitor", monitor_node)
graph.add_node("replan", replan_node)

graph.set_entry_point("planner")

graph.add_conditional_edges(
    "monitor",
    lambda state: state.get("next"),
    {"executor": "executor", "replan": "replan", END: END}
)

graph.add_edge("executor", "monitor")
graph.add_edge("replan", "executor")

app = graph.compile()
```

### Goal Spec Configuration
```json
{
  "topology": "plan_execute",
  "agents": {
    "planner": "planner_agent",
    "executor": "executor_agent",
    "monitor": "monitor_agent",
    "replanner": "replanner_agent"
  },
  "execution": {
    "max_replans": 2,
    "step_timeout": 300
  }
}
```

### Advantages
- Strategic execution
- Handles failures gracefully
- Adaptive to changes

### Disadvantages
- Complex state management
- Multiple agent types needed
- Planning overhead

---

## Topology Selection Matrix

| Pattern | Complexity | Parallelization | Robustness | Use When |
|---------|------------|-----------------|------------|----------|
| **Sequential** | Low | None | Low | Simple, ordered tasks |
| **Router** | Low | None | Medium | Domain classification |
| **Supervisor** | Medium | High | Medium | Parallel work coordination |
| **Collaborative** | High | Medium | High | Agent negotiation needed |
| **Map-Reduce** | Medium | High | Medium | Batch processing |
| **Human-in-Loop** | Medium | None | High | Approval/review required |
| **Recursive** | High | None | Medium | Problem decomposition |
| **Ensemble** | Medium | High | High | High-stakes decisions |
| **Reflection** | Medium | None | High | Quality critical |
| **Plan-Execute** | High | Low | High | Complex multi-step goals |

---

## Goal Spec Topology Configuration

### Unified Topology Schema

```json
{
  "topology": {
    "type": "sequential|router|supervisor|collaborative|map_reduce|human_in_loop|recursive|ensemble|reflection|plan_execute",

    "sequential": {
      "tasks": ["task1", "task2", "task3"]
    },

    "router": {
      "router_agent": "classifier",
      "routes": {
        "intent1": "agent1",
        "intent2": "agent2"
      }
    },

    "supervisor": {
      "supervisor_agent": "coordinator",
      "workers": ["worker1", "worker2"],
      "parallel": true
    },

    "collaborative": {
      "agents": ["agent1", "agent2"],
      "communication_graph": {
        "agent1": ["agent2"],
        "agent2": ["agent1"]
      },
      "max_exchanges": 5
    },

    "map_reduce": {
      "map_agent": "processor",
      "reduce_agent": "aggregator",
      "chunk_size": 1000
    },

    "human_in_loop": {
      "interrupt_before": ["approval_node"],
      "interrupt_after": ["draft_generation"]
    },

    "recursive": {
      "agent": "decomposer",
      "max_depth": 5,
      "base_condition": "is_simple"
    },

    "ensemble": {
      "models": ["gpt4", "claude", "gemini"],
      "consensus_strategy": "majority_vote"
    },

    "reflection": {
      "generator": "writer_agent",
      "critic": "reviewer_agent",
      "refiner": "editor_agent",
      "max_iterations": 3,
      "quality_threshold": 0.8
    },

    "plan_execute": {
      "planner": "planner_agent",
      "executor": "executor_agent",
      "monitor": "monitor_agent",
      "replanner": "replanner_agent"
    }
  }
}
```

---

## GoalGen Implementation Strategy

### For Each Topology Pattern

The LangGraph generator should:

1. **Detect topology type** from spec
2. **Generate appropriate graph structure** (nodes, edges)
3. **Create routing logic** (conditional edges)
4. **Add state management** (checkpointer, state schema)
5. **Generate tests** for the topology

### Template Organization

```
templates/langgraph/
├── base/
│   ├── graph_setup.py.j2
│   ├── state_schema.py.j2
│   └── checkpointer.py.j2
├── topologies/
│   ├── sequential.py.j2
│   ├── router.py.j2
│   ├── supervisor.py.j2
│   ├── collaborative.py.j2
│   ├── map_reduce.py.j2
│   ├── human_in_loop.py.j2
│   ├── recursive.py.j2
│   ├── ensemble.py.j2
│   ├── reflection.py.j2
│   └── plan_execute.py.j2
└── nodes/
    ├── supervisor_node.py.j2
    ├── router_node.py.j2
    ├── worker_node.py.j2
    └── aggregator_node.py.j2
```

---

## Summary

Multi-agent patterns provide different trade-offs:

- **Sequential**: Simple, predictable
- **Router**: Specialist delegation
- **Supervisor**: Parallel coordination
- **Collaborative**: Rich interactions
- **Map-Reduce**: Batch parallelization
- **Human-in-Loop**: Human oversight
- **Recursive**: Problem decomposition
- **Ensemble**: Robust consensus
- **Reflection**: Quality improvement
- **Plan-Execute**: Strategic execution

GoalGen should support all 10 patterns with topology-specific code generation based on the goal spec configuration.
