# Topology Inference vs Explicit Declaration

Analysis of whether topology should be explicitly declared in spec or inferred from patterns.

---

## The Question

Should the goal spec:
1. **Explicitly declare** the topology type?
2. **Implicitly define** topology through task/agent structure, letting GoalGen infer it?

---

## Option A: Explicit Topology Declaration

### Approach

User explicitly specifies topology in the spec:

```json
{
  "id": "travel_planning",
  "topology": {
    "type": "supervisor",
    "supervisor_agent": "travel_supervisor",
    "workers": ["flight_agent", "hotel_agent", "activity_agent"],
    "parallel_execution": true
  },
  "tasks": [...],
  "agents": {...}
}
```

### Advantages

✅ **Clear Intent** - No ambiguity about desired architecture
✅ **Explicit Control** - User chooses the pattern that fits their needs
✅ **Validation** - Easy to validate spec against topology requirements
✅ **Documentation** - Self-documenting architecture choice
✅ **Predictable Output** - Same spec always generates same topology
✅ **Advanced Patterns** - Enables complex patterns (ensemble, reflection) that are hard to infer
✅ **Override Capability** - Can force specific topology even if task structure suggests otherwise

### Disadvantages

❌ **Steeper Learning Curve** - Users must understand all topology types
❌ **More Verbose** - Additional configuration required
❌ **Potential Conflicts** - Declared topology might not match task structure
❌ **Flexibility** - May lock users into pattern when simple structure would work
❌ **Redundancy** - Task structure may already imply the topology

### Example Specs

**Sequential (Explicit)**
```json
{
  "topology": {"type": "sequential"},
  "tasks": [
    {"id": "extract", "agent": "extractor"},
    {"id": "validate", "agent": "validator"},
    {"id": "format", "agent": "formatter"}
  ]
}
```

**Supervisor (Explicit)**
```json
{
  "topology": {
    "type": "supervisor",
    "supervisor": "coordinator",
    "workers": ["research1", "research2", "research3"],
    "parallel": true
  },
  "agents": {...}
}
```

---

## Option B: Inferred Topology (Pattern Detection)

### Approach

GoalGen analyzes the spec structure and infers the topology:

```json
{
  "id": "travel_planning",
  "tasks": [
    {
      "id": "coordinate",
      "type": "supervisor",
      "subtasks": ["research_flights", "research_hotels", "research_activities"]
    },
    {
      "id": "research_flights",
      "type": "task",
      "agent": "flight_agent"
    },
    {
      "id": "research_hotels",
      "type": "task",
      "agent": "hotel_agent"
    }
  ]
}
```

**Inference**: Task has type="supervisor" with subtasks → **Supervisor topology**

### Inference Rules

#### Rule 1: Sequential Detection
```
IF: tasks[i].next = tasks[i+1].id for all i
THEN: topology = "sequential"
```

```json
{
  "tasks": [
    {"id": "step1", "next": "step2"},
    {"id": "step2", "next": "step3"},
    {"id": "step3"}
  ]
}
```

#### Rule 2: Router Detection
```
IF: task has type="router" OR task has routing_conditions
THEN: topology = "router"
```

```json
{
  "tasks": [
    {
      "id": "classify",
      "type": "router",
      "routes": {
        "flight": "flight_agent",
        "hotel": "hotel_agent",
        "general": "general_agent"
      }
    }
  ]
}
```

#### Rule 3: Supervisor Detection
```
IF: task has type="supervisor" OR task has subtasks
THEN: topology = "supervisor"
```

```json
{
  "tasks": [
    {
      "id": "coordinate",
      "type": "supervisor",
      "subtasks": ["task1", "task2", "task3"]
    }
  ]
}
```

#### Rule 4: Map-Reduce Detection
```
IF: task has type="map_reduce" OR (task has split AND task has reduce)
THEN: topology = "map_reduce"
```

```json
{
  "tasks": [
    {
      "id": "process_documents",
      "type": "map_reduce",
      "map_agent": "processor",
      "reduce_agent": "aggregator"
    }
  ]
}
```

#### Rule 5: Collaborative Detection
```
IF: agents have bidirectional communication edges
THEN: topology = "collaborative"
```

```json
{
  "agents": {
    "agent1": {"communicates_with": ["agent2"]},
    "agent2": {"communicates_with": ["agent1"]}
  }
}
```

#### Rule 6: Reflection Detection
```
IF: task has type="reflection" OR workflow includes critic + refiner
THEN: topology = "reflection"
```

```json
{
  "tasks": [
    {"id": "generate", "agent": "generator"},
    {"id": "critique", "agent": "critic"},
    {"id": "refine", "agent": "refiner", "loops_to": "critique"}
  ]
}
```

### Advantages

✅ **Simpler Specs** - Users describe WHAT, not HOW
✅ **Lower Barrier** - Don't need to understand topology patterns
✅ **Declarative** - Focus on tasks/agents, not architecture
✅ **Flexibility** - System chooses optimal topology
✅ **Evolution** - Specs can be optimized over time without user changes
✅ **Concise** - Less configuration required

### Disadvantages

❌ **Ambiguity** - Same spec might infer different topologies
❌ **Hidden Logic** - Inference rules are "magic" to users
❌ **Limited Control** - Can't force specific pattern
❌ **Debugging** - Harder to understand why a topology was chosen
❌ **Complex Inference** - Some patterns hard to detect (ensemble, plan-execute)
❌ **Edge Cases** - Ambiguous specs might infer wrong topology
❌ **Version Sensitivity** - Inference rules might change across GoalGen versions

### Example Inferred Specs

**Sequential (Inferred from task chain)**
```json
{
  "tasks": [
    {"id": "extract", "agent": "extractor", "next": "validate"},
    {"id": "validate", "agent": "validator", "next": "format"},
    {"id": "format", "agent": "formatter"}
  ]
}
```
**Inferred**: Sequential topology

**Supervisor (Inferred from subtasks)**
```json
{
  "tasks": [
    {
      "id": "research",
      "subtasks": ["flights", "hotels", "activities"],
      "parallel": true
    }
  ]
}
```
**Inferred**: Supervisor topology

---

## Option C: Hybrid Approach (Recommended)

### Approach

**Default to inference, allow explicit override**

```json
{
  "id": "travel_planning",

  // Optional: explicit topology (overrides inference)
  "topology": {
    "type": "supervisor",  // Optional override
    // ... topology-specific config
  },

  // Required: task structure (used for inference if topology not specified)
  "tasks": [
    {
      "id": "coordinate",
      "type": "supervisor",  // Hints at topology
      "subtasks": ["research_flights", "research_hotels"]
    }
  ]
}
```

### Inference with Hints

Tasks can include **type hints** that guide inference:

```json
{
  "tasks": [
    {
      "id": "coordinate",
      "type": "supervisor",  // ← Hint: this is a supervisor task
      "subtasks": ["task1", "task2", "task3"]
    }
  ]
}
```

Without explicit `topology` declaration, GoalGen:
1. Looks for type hints in tasks
2. Analyzes task structure
3. Infers most appropriate topology
4. Logs the inferred topology for user review

### Override Mechanism

Users can override inference:

```json
{
  "topology": {
    "type": "ensemble",  // ← Explicit override
    "models": ["gpt4", "claude", "gemini"]
  },
  "tasks": [
    {
      "id": "analyze",
      "agent": "analyzer"  // Same task, but run as ensemble
    }
  ]
}
```

### Advantages

✅ **Best of Both Worlds** - Simple specs work, advanced users have control
✅ **Progressive Disclosure** - Start simple, add complexity as needed
✅ **Backward Compatible** - Old specs (no topology) still work
✅ **Explicit When Needed** - Complex patterns (ensemble, reflection) can be explicit
✅ **Debugging** - GoalGen can log "Inferred topology: supervisor" for transparency
✅ **Validation** - Can validate explicit topology against task structure

### Disadvantages

⚠️ **Complexity** - Must implement both inference and explicit handling
⚠️ **Documentation** - Must document both approaches
⚠️ **Potential Confusion** - Two ways to do the same thing

---

## Comparison Matrix

| Aspect | Explicit | Inferred | Hybrid |
|--------|----------|----------|--------|
| **Learning Curve** | High | Low | Medium |
| **Spec Complexity** | High | Low | Medium |
| **Control** | Full | Limited | Full (when needed) |
| **Ambiguity** | None | Possible | Minimal |
| **Flexibility** | Low | High | High |
| **Debugging** | Easy | Hard | Medium |
| **Advanced Patterns** | Easy | Hard | Easy |
| **Simple Use Cases** | Verbose | Concise | Concise |
| **Implementation** | Simple | Complex | Complex |

---

## Inference Algorithm (for Hybrid Approach)

```python
def infer_topology(spec: dict) -> str:
    """Infer topology from spec structure"""

    # 1. Check for explicit topology
    if "topology" in spec and "type" in spec["topology"]:
        return spec["topology"]["type"]

    # 2. Analyze task structure for hints
    tasks = spec.get("tasks", [])

    # Sequential detection
    if is_sequential_chain(tasks):
        return "sequential"

    # Router detection
    if has_router_task(tasks):
        return "router"

    # Supervisor detection
    if has_supervisor_task(tasks):
        return "supervisor"

    # Map-Reduce detection
    if has_map_reduce_pattern(tasks):
        return "map_reduce"

    # Collaborative detection
    if has_bidirectional_communication(spec.get("agents", {})):
        return "collaborative"

    # Reflection detection
    if has_reflection_pattern(tasks):
        return "reflection"

    # Plan-Execute detection
    if has_plan_execute_pattern(tasks):
        return "plan_execute"

    # 3. Default fallback
    logger.warning(f"Could not infer topology for {spec['id']}, defaulting to sequential")
    return "sequential"


def is_sequential_chain(tasks: list) -> bool:
    """Check if tasks form a sequential chain"""
    if len(tasks) <= 1:
        return True

    # Check if each task (except last) has 'next' pointing to next task
    for i, task in enumerate(tasks[:-1]):
        if task.get("next") != tasks[i+1]["id"]:
            return False

    return True


def has_supervisor_task(tasks: list) -> bool:
    """Check if any task is a supervisor"""
    for task in tasks:
        if task.get("type") == "supervisor":
            return True
        if "subtasks" in task:
            return True
    return False


def has_router_task(tasks: list) -> bool:
    """Check if any task is a router"""
    for task in tasks:
        if task.get("type") == "router":
            return True
        if "routes" in task or "routing_conditions" in task:
            return True
    return False


# ... more detection functions
```

---

## Recommended Approach: **Hybrid with Smart Defaults**

### Strategy

1. **Simple specs** → Infer topology from structure
2. **Complex patterns** → Require explicit topology
3. **Ambiguous specs** → Infer + warn user
4. **Override capability** → Always honor explicit topology

### Inference Complexity Tiers

#### Tier 1: Easy to Infer (Auto-detect)
- **Sequential** - Linear task chain
- **Router** - Task with routing logic
- **Supervisor** - Task with subtasks
- **Map-Reduce** - Task with map/reduce agents

#### Tier 2: Medium Inference (Type hints help)
- **Collaborative** - Agent communication graph
- **Human-in-Loop** - Tasks with approval flags
- **Reflection** - Generate → Critique → Refine cycle

#### Tier 3: Hard to Infer (Require explicit)
- **Recursive** - Not obvious from structure
- **Ensemble** - Requires multiple models
- **Plan-Execute** - Complex multi-stage pattern

### Spec Design Principles

1. **Type Hints**: Tasks can have `type` field to hint at topology
2. **Structural Markers**: Use `subtasks`, `routes`, `map`/`reduce` to indicate patterns
3. **Explicit Override**: `topology.type` always takes precedence
4. **Validation**: Warn if explicit topology conflicts with task structure
5. **Documentation**: Log inferred topology for user awareness

---

## Example: Travel Planning Spec (Hybrid)

### Minimal Spec (Inferred as Supervisor)

```json
{
  "id": "travel_planning",
  "title": "Plan 7-day Japan trip",

  "tasks": [
    {
      "id": "research",
      "subtasks": ["flights", "hotels", "activities"],
      "parallel": true
    },
    {
      "id": "flights",
      "agent": "flight_agent",
      "tools": ["flight_api"]
    },
    {
      "id": "hotels",
      "agent": "hotel_agent",
      "tools": ["hotel_api"]
    },
    {
      "id": "activities",
      "agent": "activity_agent",
      "tools": ["places_api"]
    }
  ]
}
```

**GoalGen inference**:
```
[INFO] Inferred topology: supervisor
       Reason: Task 'research' has subtasks with parallel=true
```

### Explicit Spec (Override to Ensemble)

```json
{
  "id": "travel_planning",
  "title": "Plan 7-day Japan trip",

  "topology": {
    "type": "ensemble",
    "models": ["gpt-4", "claude-3", "gemini-pro"],
    "consensus": "majority_vote"
  },

  "tasks": [
    {
      "id": "plan",
      "agent": "planner_agent"
    }
  ]
}
```

**GoalGen behavior**:
```
[INFO] Using explicit topology: ensemble
       Running planner_agent across 3 models
```

---

## Implementation in GoalGen

### Config Schema (Hybrid)

```json
{
  "topology": {
    // Optional: explicit topology type
    "type": "sequential|router|supervisor|...",

    // Optional: topology-specific config
    "supervisor": {...},
    "router": {...},
    // ... pattern-specific config
  },

  "tasks": [
    {
      "id": "string",

      // Optional: type hint for inference
      "type": "task|evaluator|supervisor|router|map_reduce",

      // Optional: structural hints
      "subtasks": ["string"],
      "routes": {...},
      "parallel": boolean,
      "next": "string",

      // Standard fields
      "agent": "string",
      "tools": ["string"]
    }
  ]
}
```

### Generator Logic

```python
# In langgraph generator

def generate(spec, out_dir, dry_run=False):
    # 1. Infer or extract topology
    topology = infer_topology(spec)

    logger.info(f"[langgraph] Topology: {topology}")

    # 2. Validate topology against spec
    validate_topology_spec(topology, spec)

    # 3. Select appropriate template
    template = select_topology_template(topology)

    # 4. Generate code
    code = template.render(spec=spec, topology=topology)

    # 5. Write output
    write_file(out_dir / "langgraph/quest_builder.py", code)
```

---

## Validation Rules

### Rule 1: Explicit Topology Validation

If topology is explicitly declared, validate task structure matches:

```python
def validate_topology_spec(topology: str, spec: dict):
    if topology == "supervisor":
        # Must have at least one task with subtasks
        assert any(t.get("subtasks") for t in spec["tasks"]), \
            "Supervisor topology requires task with subtasks"

    elif topology == "sequential":
        # Tasks should form a chain
        assert is_sequential_chain(spec["tasks"]), \
            "Sequential topology requires linear task chain"

    elif topology == "ensemble":
        # Must specify models
        assert "models" in spec.get("topology", {}), \
            "Ensemble topology requires models specification"

    # ... more validations
```

### Rule 2: Inference Warnings

Warn if inference is ambiguous:

```python
def infer_topology(spec: dict) -> str:
    matches = []

    if is_sequential_chain(spec["tasks"]):
        matches.append("sequential")

    if has_supervisor_task(spec["tasks"]):
        matches.append("supervisor")

    if len(matches) == 0:
        logger.warning("No topology pattern detected, using sequential")
        return "sequential"

    if len(matches) > 1:
        logger.warning(f"Multiple topologies possible: {matches}, using {matches[0]}")

    return matches[0]
```

---

## Recommendation: **Hybrid Approach**

### Why Hybrid?

1. **Progressive Complexity** - Start simple, add detail as needed
2. **Smart Defaults** - Most specs just work without topology knowledge
3. **Power User Control** - Advanced users can specify exact topology
4. **Future Proof** - Can add new inference rules without breaking specs
5. **Best UX** - Balances simplicity and control

### Implementation Priority

1. **Phase 1**: Implement explicit topology (easier, validates approach)
2. **Phase 2**: Add inference for common patterns (sequential, supervisor, router)
3. **Phase 3**: Expand inference to all 10 patterns
4. **Phase 4**: Add validation and warnings

### Documentation Strategy

**For Users**:
- Show simple examples without topology (inferred)
- Show when explicit topology is needed (ensemble, plan-execute)
- Explain type hints that aid inference

**For Developers**:
- Document inference algorithm
- Explain how to add new patterns
- Provide debugging tools (--show-topology flag)

---

## Decision: Use Hybrid Approach ✅

**Default**: Infer from task structure
**Override**: Explicit `topology.type` field
**Validation**: Warn on conflicts or ambiguity
**Documentation**: Log inferred topology

This gives us:
- ✅ Simple specs for common cases
- ✅ Full control for advanced patterns
- ✅ Clear upgrade path (start simple, add explicitness)
- ✅ Validation to catch errors
- ✅ Transparency (users see what was inferred)
