# Evaluator Framework Options

Comprehensive analysis of validation and rules engine choices for implementing evaluators in GoalGen.

---

## Evaluator Requirements

Evaluators in GoalGen need to:

1. **Context Validation** - Check if required fields are present
2. **Data Quality Validation** - Validate field values (regex, range, enum, type)
3. **Business Rules** - Complex logic (budget < $10000, dates in future, etc.)
4. **External Validation** - Call external services for validation (e.g., address verification)
5. **Rule Composition** - Support AND, OR, NOT logic
6. **Custom Logic** - Developers can add custom validation functions
7. **Performance** - Fast evaluation (blocking LangGraph execution)
8. **Async Support** - Support async validation (external API calls)
9. **Caching** - Cache validation results
10. **Error Messages** - Clear, actionable error messages for users

---

## Option 1: Schema Validation Libraries

### A. Pydantic (Recommended Baseline)

**What**: Data validation using Python type annotations

```python
from pydantic import BaseModel, validator, Field
from typing import Optional
from datetime import date

class TravelContext(BaseModel):
    destination: str = Field(..., min_length=1)
    dates: Optional[str] = None
    budget: float = Field(..., gt=0, le=50000)
    num_travelers: int = Field(..., ge=1, le=10)

    @validator('dates')
    def validate_dates(cls, v):
        if v:
            # Parse and validate date range
            start, end = v.split(' to ')
            # Validate future dates
            return v
        return v
```

**Pros:**
- Fast (Rust-based validation in v2)
- Type-safe with IDE support
- Built-in validators (min, max, regex, etc.)
- Custom validators via decorators
- JSON schema generation
- Async validator support
- Excellent error messages
- Wide adoption in Python ecosystem

**Cons:**
- Requires Python class definitions (not purely declarative)
- Less flexible for dynamic rule changes
- Not a full rules engine

**Use Case**: Simple field validation, type checking, basic constraints

**Dependencies**: `pydantic ^2.4.0`

---

### B. Cerberus

**What**: Lightweight, extensible data validation

```python
from cerberus import Validator

schema = {
    'destination': {'type': 'string', 'minlength': 1, 'required': True},
    'budget': {'type': 'float', 'min': 0, 'max': 50000, 'required': True},
    'dates': {'type': 'string', 'regex': r'\d{4}-\d{2}-\d{2} to \d{4}-\d{2}-\d{2}'}
}

v = Validator(schema)
v.validate({'destination': 'Japan', 'budget': 5000})
```

**Pros:**
- Purely declarative schemas (dict-based)
- Easy to serialize/store schemas in DB
- Extensible (custom validators)
- Coercion (type conversion)
- Normalization rules
- No dependencies

**Cons:**
- Less type-safe than Pydantic
- Slower than Pydantic v2
- No async support out of box
- Smaller community

**Use Case**: Dynamic schemas that need to be stored/modified at runtime

**Dependencies**: `cerberus ^1.3.5`

---

### C. marshmallow

**What**: Object serialization and validation

```python
from marshmallow import Schema, fields, validate, ValidationError

class TravelSchema(Schema):
    destination = fields.Str(required=True, validate=validate.Length(min=1))
    budget = fields.Float(required=True, validate=validate.Range(min=0, max=50000))
    dates = fields.Str(validate=validate.Regexp(r'\d{4}-\d{2}-\d{2} to \d{4}-\d{2}-\d{2}'))
```

**Pros:**
- Mature, widely used
- Serialization + validation in one
- Pre/post-processing hooks
- Nested schema support
- Custom fields

**Cons:**
- Slower than Pydantic
- More verbose
- No async support
- Losing popularity to Pydantic

**Use Case**: Legacy projects, need serialization + validation together

**Dependencies**: `marshmallow ^3.20.0`

---

## Option 2: JSON Schema Validators

### A. jsonschema (Current Choice)

**What**: Validate data against JSON Schema standard

```python
import jsonschema
from jsonschema import validate

schema = {
    "type": "object",
    "properties": {
        "destination": {"type": "string", "minLength": 1},
        "budget": {"type": "number", "minimum": 0, "maximum": 50000}
    },
    "required": ["destination", "budget"]
}

validate(instance={"destination": "Japan", "budget": 5000}, schema=schema)
```

**Pros:**
- Standard (JSON Schema spec)
- Language-agnostic schemas
- Can store schemas as JSON
- Good for API validation
- Supports $ref (schema composition)

**Cons:**
- Slower than Pydantic
- Error messages less friendly
- No custom validation logic
- Limited to JSON Schema capabilities

**Use Case**: API validation, need language-agnostic schemas

**Dependencies**: `jsonschema ^4.19.0`

---

### B. fastjsonschema

**What**: Fast JSON Schema validator (code generation)

```python
import fastjsonschema

schema = {...}  # Same as jsonschema
validate = fastjsonschema.compile(schema)
validate({"destination": "Japan", "budget": 5000})
```

**Pros:**
- 5-10x faster than jsonschema (compiled)
- Same JSON Schema spec
- Drop-in replacement

**Cons:**
- Must compile schema (not dynamic)
- Same limitations as jsonschema

**Use Case**: Performance-critical JSON Schema validation

**Dependencies**: `fastjsonschema ^2.19.0`

---

## Option 3: Rules Engines (Lightweight)

### A. business-rules (Recommended for Complex Rules)

**What**: Lightweight Python rules engine

```python
from business_rules import run_all
from business_rules.variables import BaseVariables, numeric_rule_variable, string_rule_variable
from business_rules.actions import BaseActions, rule_action

class TravelVariables(BaseVariables):
    def __init__(self, context):
        self.context = context

    @numeric_rule_variable
    def budget(self):
        return self.context.get('budget', 0)

    @string_rule_variable
    def destination(self):
        return self.context.get('destination', '')

class TravelActions(BaseActions):
    @rule_action(params={"message": FIELD_TEXT})
    def ask_user(self, message):
        print(f"Ask user: {message}")

rules = [
    {
        "conditions": {
            "all": [
                {"name": "budget", "operator": "less_than", "value": 1000}
            ]
        },
        "actions": [
            {"name": "ask_user", "params": {"message": "Budget seems low for international travel"}}
        ]
    }
]

run_all(rule_list=rules, defined_variables=TravelVariables(context), defined_actions=TravelActions())
```

**Pros:**
- Declarative rules (can store in DB/JSON)
- Rule composition (all, any)
- Custom operators
- Separate variables from actions
- Easy to extend
- Good for business logic

**Cons:**
- Not actively maintained
- No async support
- Limited built-in operators
- Small community

**Use Case**: Complex business rules that need to be configurable

**Dependencies**: `business-rules ^1.0.1`

---

### B. durable-rules (Forward-Chaining Rules Engine)

**What**: Forward-chaining rules engine with pattern matching

```python
from durable.lang import *

with ruleset('travel'):
    @when_all((m.budget < 1000) & (m.destination == 'Japan'))
    def low_budget_japan(c):
        print('Budget too low for Japan')
        c.assert_fact({'alert': 'low_budget'})

    @when_all(m.alert == 'low_budget')
    def handle_alert(c):
        print('Handling low budget alert')

assert_fact('travel', {'budget': 500, 'destination': 'Japan'})
```

**Pros:**
- Forward-chaining (rules fire automatically)
- Pattern matching
- Stateful (facts persist)
- Complex event processing
- Good for expert systems

**Cons:**
- Heavyweight for simple validation
- Steep learning curve
- Overkill for most use cases
- C++ dependency

**Use Case**: Complex stateful rule evaluation, expert systems

**Dependencies**: `durable-rules ^2.0.28`

---

### C. python-rules (Simple Rule Engine)

**What**: Minimalist Python rule engine

```python
from rules import Rule

def budget_check(context):
    return context['budget'] < 1000

def japan_check(context):
    return context['destination'] == 'Japan'

low_budget_japan = Rule(
    condition=lambda c: budget_check(c) and japan_check(c),
    action=lambda c: print('Budget too low for Japan')
)

context = {'budget': 500, 'destination': 'Japan'}
if low_budget_japan.condition(context):
    low_budget_japan.action(context)
```

**Pros:**
- Simple, Pythonic
- No DSL to learn
- Lightweight
- Easy to test

**Cons:**
- Not declarative (rules are code)
- Can't easily serialize rules
- No built-in operators
- Minimal features

**Use Case**: Simple rule evaluation where rules are code

**Dependencies**: `python-rules ^0.1.0` (or custom implementation)

---

## Option 4: Expression Evaluation

### A. simpleeval (Safe Expression Evaluation)

**What**: Safely evaluate Python-like expressions

```python
from simpleeval import simple_eval

context = {'budget': 5000, 'num_travelers': 2}

# Safe evaluation
result = simple_eval("budget / num_travelers > 1000", names=context)
# True

# Support functions
from simpleeval import SimpleEval
s = SimpleEval()
s.functions['len'] = len
s.names = {'destination': 'Japan'}
s.eval("len(destination) > 3")  # True
```

**Pros:**
- Safe (no access to dangerous functions)
- Python-like syntax
- Store expressions as strings
- Custom functions
- Fast

**Cons:**
- Limited to expressions (no statements)
- No control flow
- Security concerns if not carefully configured

**Use Case**: User-defined validation expressions

**Dependencies**: `simpleeval ^0.9.13`

---

### B. asteval (AST-based Evaluation)

**What**: Safe, more powerful expression evaluator

```python
from asteval import Interpreter

aeval = Interpreter()
aeval.symtable['budget'] = 5000
aeval.symtable['destination'] = 'Japan'

result = aeval("budget > 1000 and destination in ['Japan', 'Korea']")
# True
```

**Pros:**
- More powerful than simpleeval
- Support for loops, conditionals
- Custom functions
- Safe (restricted AST)

**Cons:**
- Slower than simpleeval
- Still security concerns
- More complex

**Use Case**: Complex user-defined logic

**Dependencies**: `asteval ^0.9.31`

---

## Option 5: Data Quality Frameworks

### A. Great Expectations

**What**: Data validation and documentation framework

```python
import great_expectations as ge

context = ge.from_pandas(df)  # Or dict
context.expect_column_values_to_be_between('budget', min_value=0, max_value=50000)
context.expect_column_values_to_match_regex('dates', regex=r'\d{4}-\d{2}-\d{2}')

result = context.validate()
```

**Pros:**
- Comprehensive data validation
- Built-in profiling
- Data documentation
- Many built-in expectations
- Great for data pipelines

**Cons:**
- Heavy (lots of dependencies)
- Overkill for simple validation
- Designed for batch data
- Steep learning curve

**Use Case**: Data pipeline validation, data quality monitoring

**Dependencies**: `great-expectations ^0.18.0` (avoid for our use case)

---

### B. Pandera

**What**: DataFrame validation (pandas-focused)

```python
import pandera as pa

schema = pa.DataFrameSchema({
    "budget": pa.Column(float, pa.Check.between(0, 50000)),
    "destination": pa.Column(str, pa.Check.str_length(min_value=1))
})

# Validate dict (convert to DataFrame)
import pandas as pd
df = pd.DataFrame([context])
schema.validate(df)
```

**Pros:**
- Type-safe DataFrame validation
- Hypothesis testing integration
- Good error messages

**Cons:**
- Requires pandas (heavy dependency)
- DataFrame-focused (not dict-friendly)
- Overkill for simple validation

**Use Case**: Validating tabular data

**Dependencies**: `pandera ^0.17.0` (avoid for our use case)

---

## Option 6: Custom Approaches

### A. Strategy Pattern (Custom Classes)

```python
from abc import ABC, abstractmethod

class Evaluator(ABC):
    @abstractmethod
    def evaluate(self, context: dict) -> bool:
        pass

    @abstractmethod
    def get_error_message(self) -> str:
        pass

class BudgetEvaluator(Evaluator):
    def __init__(self, min_budget: float, max_budget: float):
        self.min_budget = min_budget
        self.max_budget = max_budget

    def evaluate(self, context: dict) -> bool:
        budget = context.get('budget', 0)
        return self.min_budget <= budget <= self.max_budget

    def get_error_message(self) -> str:
        return f"Budget must be between {self.min_budget} and {self.max_budget}"

# Usage
evaluators = [
    BudgetEvaluator(0, 50000),
    PresenceEvaluator('destination'),
    # ... more evaluators
]

for evaluator in evaluators:
    if not evaluator.evaluate(context):
        print(evaluator.get_error_message())
```

**Pros:**
- Full control
- Type-safe
- Easy to test
- No dependencies
- Extensible

**Cons:**
- More code to write
- Not declarative
- Can't easily serialize

**Use Case**: Full control, type safety, custom logic

---

### B. Decorator-Based Validators

```python
from functools import wraps
from typing import Callable

def evaluator(error_message: str):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(context: dict):
            if not func(context):
                raise ValidationError(error_message)
            return True
        return wrapper
    return decorator

@evaluator("Budget must be positive")
def validate_budget(context: dict) -> bool:
    return context.get('budget', 0) > 0

@evaluator("Destination is required")
def validate_destination(context: dict) -> bool:
    return bool(context.get('destination'))

# Usage
validators = [validate_budget, validate_destination]
for validator in validators:
    validator(context)
```

**Pros:**
- Clean, Pythonic
- Easy to compose
- Type hints support
- Testable

**Cons:**
- Not serializable
- Validators are code
- No dynamic rules

**Use Case**: Clean validation code, good for small number of rules

---

### C. Chain of Responsibility Pattern

```python
class ValidationHandler:
    def __init__(self, next_handler=None):
        self.next_handler = next_handler

    def handle(self, context: dict) -> tuple[bool, list[str]]:
        errors = []

        # Current validation
        is_valid, current_errors = self.validate(context)
        errors.extend(current_errors)

        # Next handler
        if self.next_handler:
            next_valid, next_errors = self.next_handler.handle(context)
            is_valid = is_valid and next_valid
            errors.extend(next_errors)

        return is_valid, errors

    def validate(self, context: dict) -> tuple[bool, list[str]]:
        return True, []

class BudgetValidator(ValidationHandler):
    def validate(self, context: dict) -> tuple[bool, list[str]]:
        budget = context.get('budget', 0)
        if budget <= 0:
            return False, ["Budget must be positive"]
        if budget > 50000:
            return False, ["Budget exceeds maximum of $50,000"]
        return True, []

# Build chain
chain = BudgetValidator(
    DestinationValidator(
        DatesValidator()
    )
)

is_valid, errors = chain.handle(context)
```

**Pros:**
- Composable
- Each validator independent
- Easy to add/remove validators
- Collects all errors

**Cons:**
- Verbose
- Not declarative
- More boilerplate

**Use Case**: Complex validation pipelines, need all errors

---

## Recommendation Matrix

| Use Case | Recommended Framework | Rationale |
|----------|----------------------|-----------|
| **Simple field validation** | Pydantic | Fast, type-safe, excellent DX |
| **Dynamic schemas (DB-stored)** | Cerberus or jsonschema | Serializable schemas |
| **Complex business rules** | business-rules + Pydantic | Declarative rules + schema validation |
| **User-defined expressions** | simpleeval + Pydantic | Safe evaluation + base validation |
| **Custom logic only** | Strategy Pattern | Full control, type-safe |
| **Rule composition (AND/OR/NOT)** | business-rules | Built-in composition |
| **External API validation** | Custom async + Pydantic | Async support needed |
| **High performance** | Pydantic v2 | Rust-based speed |

---

## Recommended Hybrid Approach for GoalGen

**Primary Stack:**
```
Pydantic (base validation) + Custom Evaluator Classes (business logic) + Optional business-rules (complex rules)
```

### Architecture:

```python
from pydantic import BaseModel, validator
from typing import Optional
from abc import ABC, abstractmethod

# Layer 1: Pydantic for schema validation
class ContextSchema(BaseModel):
    destination: str
    budget: float
    dates: Optional[str] = None

    class Config:
        extra = 'allow'  # Allow additional context fields

# Layer 2: Custom Evaluators for business logic
class BaseEvaluator(ABC):
    """Base evaluator interface"""

    @abstractmethod
    async def evaluate(self, context: dict) -> tuple[bool, str]:
        """Returns (is_valid, error_message)"""
        pass

    @abstractmethod
    def get_id(self) -> str:
        pass

class PresenceEvaluator(BaseEvaluator):
    """Check if field is present"""

    def __init__(self, field: str, action: str = "ask_user"):
        self.field = field
        self.action = action

    async def evaluate(self, context: dict) -> tuple[bool, str]:
        if self.field not in context or not context[self.field]:
            return False, f"Missing required field: {self.field}"
        return True, ""

    def get_id(self) -> str:
        return f"presence_{self.field}"

class RangeEvaluator(BaseEvaluator):
    """Check if numeric field is in range"""

    def __init__(self, field: str, min_val: float, max_val: float):
        self.field = field
        self.min_val = min_val
        self.max_val = max_val

    async def evaluate(self, context: dict) -> tuple[bool, str]:
        value = context.get(self.field)
        if value is None:
            return True, ""  # Field not present, handled by PresenceEvaluator

        if not (self.min_val <= value <= self.max_val):
            return False, f"{self.field} must be between {self.min_val} and {self.max_val}"
        return True, ""

    def get_id(self) -> str:
        return f"range_{self.field}"

class RegexEvaluator(BaseEvaluator):
    """Check if string field matches regex"""

    def __init__(self, field: str, pattern: str):
        self.field = field
        self.pattern = pattern
        self.compiled = re.compile(pattern)

    async def evaluate(self, context: dict) -> tuple[bool, str]:
        value = context.get(self.field)
        if value is None:
            return True, ""

        if not self.compiled.match(str(value)):
            return False, f"{self.field} does not match required format"
        return True, ""

    def get_id(self) -> str:
        return f"regex_{self.field}"

class CustomEvaluator(BaseEvaluator):
    """Custom evaluation logic"""

    def __init__(self, eval_id: str, eval_func: callable):
        self.eval_id = eval_id
        self.eval_func = eval_func

    async def evaluate(self, context: dict) -> tuple[bool, str]:
        return await self.eval_func(context)

    def get_id(self) -> str:
        return self.eval_id

# Layer 3: Evaluator Manager
class EvaluatorManager:
    """Manages and runs all evaluators"""

    def __init__(self, evaluators: list[BaseEvaluator]):
        self.evaluators = evaluators
        self.cache = {}  # Cache results

    async def evaluate_all(self, context: dict, use_cache: bool = True) -> tuple[bool, list[str]]:
        """Run all evaluators, collect errors"""

        # First, validate schema with Pydantic
        try:
            ContextSchema(**context)
        except Exception as e:
            return False, [str(e)]

        errors = []
        for evaluator in self.evaluators:
            eval_id = evaluator.get_id()

            # Check cache
            if use_cache and eval_id in self.cache:
                is_valid, error = self.cache[eval_id]
            else:
                is_valid, error = await evaluator.evaluate(context)
                if use_cache:
                    self.cache[eval_id] = (is_valid, error)

            if not is_valid:
                errors.append(error)

        return len(errors) == 0, errors
```

### Dependencies for Recommended Approach:

```python
# requirements.txt
pydantic>=2.4.0          # Schema validation
python-dotenv>=1.0.0     # Config
# Optional:
# business-rules>=1.0.1  # If complex rules needed
# simpleeval>=0.9.13     # If user-defined expressions needed
```

### Why This Approach:

1. **Pydantic**: Fast schema validation, type safety, great DX
2. **Custom Evaluators**: Full flexibility for business logic, async support, testable
3. **Composable**: Easy to add new evaluator types
4. **Performant**: Pydantic v2 is fast, caching for repeated evaluations
5. **Extensible**: Developers can add custom evaluators easily
6. **Serializable**: Evaluator configs can be generated from spec

---

## Summary

**Recommended Primary Choice**: **Pydantic + Custom Evaluator Classes**

**Optional Additions**:
- **business-rules**: If you need declarative, DB-stored complex rules
- **simpleeval**: If you need user-defined validation expressions
- **jsonschema**: If you need language-agnostic validation schemas

**Avoid**:
- Heavy data frameworks (Great Expectations, Pandera) - overkill
- Forward-chaining engines (durable-rules) - too complex
- marshmallow - being replaced by Pydantic in ecosystem
