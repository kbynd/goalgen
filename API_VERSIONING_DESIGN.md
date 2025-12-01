# API Versioning and OpenAPI Specification Design

Explicit API versioning strategy and OpenAPI compliance for all generated endpoints.

---

## Core Principles

1. **All APIs must follow OpenAPI 3.1 specification**
2. **Explicit versioning from day one**
3. **Backward compatibility maintained across versions**
4. **API evolution without breaking existing clients**
5. **Auto-generated OpenAPI documentation**

---

## API Versioning Strategy

### Version Format

**Semantic Versioning**: `v{major}.{minor}`

- **Major** (v1, v2): Breaking changes
- **Minor** (v1.1, v1.2): Backward-compatible additions
- **Patch**: No API changes (internal fixes only)

### URL Versioning Patterns

#### Pattern 1: URL Path Versioning (Recommended)

```
https://api.example.com/api/v1/goal/{goal_id}/message
https://api.example.com/api/v2/goal/{goal_id}/message
```

**Advantages**:
- ✅ Clear, visible version in URL
- ✅ Easy to route
- ✅ Works with all HTTP clients
- ✅ Cacheable at CDN level

#### Pattern 2: Header Versioning (Alternative)

```
GET /api/goal/{goal_id}/message
Header: API-Version: v1
```

**Advantages**:
- ✅ Clean URLs
- ✅ Same endpoint, multiple versions
- ❌ Less visible
- ❌ More complex routing

#### Pattern 3: Query Parameter (Not Recommended)

```
/api/goal/{goal_id}/message?version=v1
```

**Disadvantages**:
- ❌ Easy to forget
- ❌ Breaks caching
- ❌ Non-standard

---

## Goal Spec API Configuration

### Explicit API Version Declaration

```json
{
  "id": "travel_planning",
  "title": "Travel Planning Assistant",

  "api": {
    "versioning": {
      "strategy": "url_path",
      "current_version": "v1",
      "supported_versions": ["v1"],
      "deprecated_versions": [],
      "base_path": "/api/{version}/goal/{goal_id}"
    },

    "openapi": {
      "version": "3.1.0",
      "title": "Travel Planning API",
      "description": "Multi-agent travel planning assistant",
      "contact": {
        "name": "API Support",
        "email": "api@example.com"
      },
      "license": {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
      },
      "servers": [
        {
          "url": "https://api.example.com",
          "description": "Production"
        },
        {
          "url": "https://api-staging.example.com",
          "description": "Staging"
        }
      ]
    },

    "endpoints": {
      "message": {
        "path": "/message",
        "method": "POST",
        "versions": {
          "v1": {
            "request_schema": "MessageRequestV1",
            "response_schema": "MessageResponseV1",
            "deprecated": false
          }
        }
      },
      "thread": {
        "path": "/thread",
        "method": "POST",
        "versions": {
          "v1": {
            "request_schema": "CreateThreadRequestV1",
            "response_schema": "CreateThreadResponseV1"
          }
        }
      },
      "thread_history": {
        "path": "/thread/{thread_id}/history",
        "method": "GET",
        "versions": {
          "v1": {
            "response_schema": "ThreadHistoryResponseV1"
          }
        }
      }
    },

    "schemas": {
      "MessageRequestV1": {
        "type": "object",
        "required": ["message"],
        "properties": {
          "message": {
            "type": "string",
            "description": "User message",
            "minLength": 1,
            "maxLength": 10000
          },
          "thread_id": {
            "type": "string",
            "description": "Optional thread ID to continue conversation",
            "pattern": "^travel_[a-f0-9-]+$"
          },
          "context": {
            "type": "object",
            "description": "Optional context override",
            "properties": {
              "destination": {"type": "string"},
              "budget": {"type": "number"},
              "dates": {"type": "string"}
            }
          }
        }
      },
      "MessageResponseV1": {
        "type": "object",
        "required": ["response", "thread_id"],
        "properties": {
          "response": {
            "type": "string",
            "description": "Assistant response"
          },
          "thread_id": {
            "type": "string",
            "description": "Thread ID for conversation continuation"
          },
          "context": {
            "type": "object",
            "description": "Current conversation context"
          },
          "suggestions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Suggested follow-up actions"
          }
        }
      }
    },

    "security": {
      "schemes": {
        "BearerAuth": {
          "type": "http",
          "scheme": "bearer",
          "bearerFormat": "JWT"
        },
        "ApiKeyAuth": {
          "type": "apiKey",
          "in": "header",
          "name": "X-API-Key"
        }
      },
      "default": "BearerAuth"
    },

    "rate_limiting": {
      "enabled": true,
      "default_limits": {
        "requests_per_minute": 60,
        "requests_per_hour": 1000
      },
      "headers": {
        "include_limit_headers": true,
        "header_prefix": "X-RateLimit-"
      }
    }
  }
}
```

---

## Generated OpenAPI Specification

### Complete OpenAPI 3.1 Document

```yaml
# orchestrator/openapi/openapi.yaml (generated)

openapi: 3.1.0
info:
  title: Travel Planning API
  description: Multi-agent travel planning assistant
  version: 1.0.0
  contact:
    name: API Support
    email: api@example.com
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: https://api.example.com
    description: Production
  - url: https://api-staging.example.com
    description: Staging

paths:
  /api/v1/goal/travel_planning/message:
    post:
      summary: Send message to travel planning assistant
      description: |
        Send a message to the travel planning assistant. The assistant will
        help plan your trip by asking questions and providing recommendations.

        ## Conversation Flow
        1. Create a new conversation or continue existing one with thread_id
        2. Send messages to build context (destination, budget, dates)
        3. Receive recommendations for flights, hotels, activities

        ## Rate Limits
        - 60 requests per minute
        - 1000 requests per hour
      operationId: sendMessage
      tags:
        - Messages
      security:
        - BearerAuth: []
      parameters:
        - name: X-Request-ID
          in: header
          description: Unique request identifier for tracing
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MessageRequestV1'
            examples:
              new_conversation:
                summary: Start new conversation
                value:
                  message: "I want to plan a 7-day trip to Japan"
              continue_conversation:
                summary: Continue existing conversation
                value:
                  message: "My budget is $5000"
                  thread_id: "travel_a1b2c3d4-e5f6-7890-abcd-ef1234567890"
      responses:
        '200':
          description: Successful response
          headers:
            X-RateLimit-Limit:
              description: Request limit per window
              schema:
                type: integer
            X-RateLimit-Remaining:
              description: Remaining requests in window
              schema:
                type: integer
            X-RateLimit-Reset:
              description: UTC timestamp when limit resets
              schema:
                type: integer
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MessageResponseV1'
              examples:
                initial_response:
                  summary: Initial response with questions
                  value:
                    response: "Great! I'd love to help you plan your trip to Japan. To provide the best recommendations, I need a few more details. What's your budget for this trip?"
                    thread_id: "travel_a1b2c3d4-e5f6-7890-abcd-ef1234567890"
                    context:
                      destination: "Japan"
                      num_travelers: 1
                    suggestions:
                      - "Specify budget"
                      - "Add travel dates"
                      - "Add number of travelers"
        '400':
          description: Bad request
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
              examples:
                invalid_message:
                  summary: Invalid message
                  value:
                    error: "ValidationError"
                    message: "Message is required and cannot be empty"
                    details:
                      field: "message"
                      constraint: "minLength"
        '401':
          description: Unauthorized
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '429':
          description: Too many requests
          headers:
            Retry-After:
              description: Seconds to wait before retry
              schema:
                type: integer
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
              example:
                error: "RateLimitExceeded"
                message: "Rate limit exceeded. Please try again later."
                retry_after: 60
        '500':
          description: Internal server error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/goal/travel_planning/thread:
    post:
      summary: Create new conversation thread
      description: Create a new conversation thread for travel planning
      operationId: createThread
      tags:
        - Threads
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateThreadRequestV1'
      responses:
        '201':
          description: Thread created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateThreadResponseV1'

  /api/v1/goal/travel_planning/thread/{thread_id}/history:
    get:
      summary: Get conversation history
      description: Retrieve the full conversation history for a thread
      operationId: getThreadHistory
      tags:
        - Threads
      security:
        - BearerAuth: []
      parameters:
        - name: thread_id
          in: path
          required: true
          description: Thread identifier
          schema:
            type: string
            pattern: '^travel_[a-f0-9-]+$'
        - name: limit
          in: query
          description: Maximum number of messages to return
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 50
        - name: offset
          in: query
          description: Number of messages to skip
          schema:
            type: integer
            minimum: 0
            default: 0
      responses:
        '200':
          description: Conversation history
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ThreadHistoryResponseV1'

components:
  schemas:
    MessageRequestV1:
      type: object
      required:
        - message
      properties:
        message:
          type: string
          description: User message
          minLength: 1
          maxLength: 10000
          example: "I want to plan a 7-day trip to Japan"
        thread_id:
          type: string
          description: Optional thread ID to continue conversation
          pattern: '^travel_[a-f0-9-]+$'
          example: "travel_a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        context:
          type: object
          description: Optional context override
          properties:
            destination:
              type: string
              example: "Japan"
            budget:
              type: number
              minimum: 0
              example: 5000
            dates:
              type: string
              pattern: '^\d{4}-\d{2}-\d{2} to \d{4}-\d{2}-\d{2}$'
              example: "2024-06-01 to 2024-06-07"
            num_travelers:
              type: integer
              minimum: 1
              maximum: 10
              example: 2

    MessageResponseV1:
      type: object
      required:
        - response
        - thread_id
      properties:
        response:
          type: string
          description: Assistant response
          example: "I'd be happy to help plan your trip to Japan!"
        thread_id:
          type: string
          description: Thread ID for conversation continuation
          example: "travel_a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        context:
          type: object
          description: Current conversation context
          properties:
            destination:
              type: string
            budget:
              type: number
            dates:
              type: string
            num_travelers:
              type: integer
        suggestions:
          type: array
          items:
            type: string
          description: Suggested follow-up actions
          example:
            - "Specify budget"
            - "Add travel dates"
        metadata:
          type: object
          properties:
            timestamp:
              type: string
              format: date-time
            model_used:
              type: string
              example: "gpt-4"
            tokens_consumed:
              type: integer
              example: 250

    CreateThreadRequestV1:
      type: object
      properties:
        metadata:
          type: object
          description: Optional thread metadata
          properties:
            user_id:
              type: string
            session_id:
              type: string

    CreateThreadResponseV1:
      type: object
      required:
        - thread_id
      properties:
        thread_id:
          type: string
          example: "travel_a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        created_at:
          type: string
          format: date-time

    ThreadHistoryResponseV1:
      type: object
      required:
        - thread_id
        - messages
      properties:
        thread_id:
          type: string
        messages:
          type: array
          items:
            $ref: '#/components/schemas/Message'
        total:
          type: integer
          description: Total number of messages in thread
        limit:
          type: integer
        offset:
          type: integer

    Message:
      type: object
      required:
        - role
        - content
        - timestamp
      properties:
        role:
          type: string
          enum: [user, assistant, system]
        content:
          type: string
        timestamp:
          type: string
          format: date-time
        metadata:
          type: object

    ErrorResponse:
      type: object
      required:
        - error
        - message
      properties:
        error:
          type: string
          description: Error code
          example: "ValidationError"
        message:
          type: string
          description: Human-readable error message
          example: "Message is required and cannot be empty"
        details:
          type: object
          description: Additional error details
        request_id:
          type: string
          description: Request ID for debugging
          format: uuid

  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: |
        JWT token obtained from authentication endpoint.
        Include in Authorization header: `Authorization: Bearer <token>`

    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
      description: API key for service-to-service communication

tags:
  - name: Messages
    description: Message operations for conversation
  - name: Threads
    description: Thread management operations
```

---

## Generated FastAPI Code with Versioning

### Main Application with Version Routing

```python
# orchestrator/app/main.py (generated)

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.api.v1 import router as v1_router
from app.config import Settings
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIDMiddleware

settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events"""
    # Startup
    print(f"Starting Travel Planning API v{settings.api_version}")
    yield
    # Shutdown
    print("Shutting down Travel Planning API")

# Create FastAPI app
app = FastAPI(
    title="Travel Planning API",
    description="Multi-agent travel planning assistant",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=settings.rate_limit_per_minute,
    requests_per_hour=settings.rate_limit_per_hour
)

# API Version routers
app.include_router(
    v1_router,
    prefix="/api/v1/goal/travel_planning",
    tags=["v1"]
)

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "Travel Planning API",
        "version": "1.0.0",
        "api_versions": {
            "current": "v1",
            "supported": ["v1"],
            "deprecated": []
        },
        "docs": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        }
    }

# Health check
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "api_version": "v1"
    }

# API version info
@app.get("/api/versions")
async def api_versions():
    return {
        "current": "v1",
        "supported": ["v1"],
        "deprecated": [],
        "endpoints": {
            "v1": "/api/v1/goal/travel_planning"
        }
    }
```

---

### V1 Router

```python
# orchestrator/app/api/v1/__init__.py (generated)

from fastapi import APIRouter
from app.api.v1.endpoints import message, thread

router = APIRouter()

# Include endpoint routers
router.include_router(message.router, tags=["Messages"])
router.include_router(thread.router, tags=["Threads"])
```

---

### V1 Message Endpoint

```python
# orchestrator/app/api/v1/endpoints/message.py (generated)

from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
from pydantic import BaseModel, Field, validator

from app.api.v1.schemas import MessageRequestV1, MessageResponseV1, ErrorResponse
from app.dependencies import get_session_store, get_current_user
from app.session_store import SessionStore

router = APIRouter()

@router.post(
    "/message",
    response_model=MessageResponseV1,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Send message to travel planning assistant",
    description="""
    Send a message to the travel planning assistant.

    ## Conversation Flow
    1. Create a new conversation or continue existing one with thread_id
    2. Send messages to build context (destination, budget, dates)
    3. Receive recommendations for flights, hotels, activities

    ## Rate Limits
    - 60 requests per minute
    - 1000 requests per hour
    """,
    operation_id="sendMessage"
)
async def send_message(
    request: MessageRequestV1,
    session_store: SessionStore = Depends(get_session_store),
    current_user: dict = Depends(get_current_user),
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID")
):
    """
    Send message to travel planning assistant.

    Generated from spec:
    - Goal: travel_planning
    - API Version: v1
    - Endpoint: /message
    """

    try:
        # Create or resume thread
        if request.thread_id:
            # Resume existing thread
            thread_id = request.thread_id
            if not await session_store.resume_session(thread_id, current_user["user_id"]):
                raise HTTPException(
                    status_code=404,
                    detail=f"Thread {thread_id} not found or expired"
                )
        else:
            # Create new thread
            thread_id = await session_store.create_session(current_user["user_id"])

        # Invoke LangGraph
        result = await session_store.invoke(
            thread_id=thread_id,
            user_id=current_user["user_id"],
            message=request.message,
            context_override=request.context
        )

        # Build response
        response = MessageResponseV1(
            response=result["response"],
            thread_id=thread_id,
            context=result.get("context", {}),
            suggestions=result.get("suggestions", []),
            metadata={
                "timestamp": result.get("timestamp"),
                "model_used": result.get("model_used"),
                "tokens_consumed": result.get("tokens_consumed")
            }
        )

        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log error
        print(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

### V1 Schemas

```python
# orchestrator/app/api/v1/schemas.py (generated)

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List, Any
from datetime import datetime

class MessageRequestV1(BaseModel):
    """Message request schema for API v1"""

    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="User message",
        example="I want to plan a 7-day trip to Japan"
    )

    thread_id: Optional[str] = Field(
        None,
        regex=r"^travel_[a-f0-9-]+$",
        description="Optional thread ID to continue conversation",
        example="travel_a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    )

    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional context override"
    )

    @validator('message')
    def message_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v

    class Config:
        schema_extra = {
            "example": {
                "message": "I want to plan a 7-day trip to Japan",
                "thread_id": "travel_a1b2c3d4-e5f6-7890-abcd-ef1234567890"
            }
        }


class MessageResponseV1(BaseModel):
    """Message response schema for API v1"""

    response: str = Field(
        ...,
        description="Assistant response",
        example="I'd be happy to help plan your trip to Japan!"
    )

    thread_id: str = Field(
        ...,
        description="Thread ID for conversation continuation",
        example="travel_a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    )

    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Current conversation context"
    )

    suggestions: List[str] = Field(
        default_factory=list,
        description="Suggested follow-up actions"
    )

    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Response metadata"
    )

    class Config:
        schema_extra = {
            "example": {
                "response": "Great! I'd love to help you plan your trip to Japan.",
                "thread_id": "travel_a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "context": {
                    "destination": "Japan",
                    "num_travelers": 1
                },
                "suggestions": [
                    "Specify budget",
                    "Add travel dates"
                ]
            }
        }


class ErrorResponse(BaseModel):
    """Error response schema"""

    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request ID for debugging")

    class Config:
        schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Message is required and cannot be empty",
                "details": {
                    "field": "message",
                    "constraint": "minLength"
                }
            }
        }
```

---

## API Evolution Strategy

### Adding New Version (v2)

When breaking changes are needed:

1. **Create new router**:
   ```python
   # app/api/v2/__init__.py
   from fastapi import APIRouter
   from app.api.v2.endpoints import message

   router = APIRouter()
   router.include_router(message.router)
   ```

2. **Update main.py**:
   ```python
   from app.api.v2 import router as v2_router

   app.include_router(
       v2_router,
       prefix="/api/v2/goal/travel_planning",
       tags=["v2"]
   )
   ```

3. **Update versions endpoint**:
   ```python
   @app.get("/api/versions")
   async def api_versions():
       return {
           "current": "v2",
           "supported": ["v1", "v2"],
           "deprecated": [],
           "sunset": {
               "v1": "2025-12-31"  # Deprecation date
           }
       }
   ```

4. **Deprecation headers** in v1:
   ```python
   @router.post("/message")
   async def send_message_v1(...):
       response.headers["Sunset"] = "Wed, 31 Dec 2025 23:59:59 GMT"
       response.headers["Deprecation"] = "true"
       response.headers["Link"] = '</api/v2/goal/travel_planning/message>; rel="successor-version"'
       ...
   ```

---

## API Documentation Generation

### Automatic OpenAPI Generation

```bash
# scripts/generate_openapi.sh

#!/usr/bin/env bash
set -euo pipefail

# Generate OpenAPI spec from FastAPI app
python -c "
from app.main import app
import json

openapi_schema = app.openapi()

with open('orchestrator/openapi/openapi.json', 'w') as f:
    json.dump(openapi_schema, f, indent=2)

print('Generated OpenAPI specification')
"

# Convert to YAML
python -c "
import json
import yaml

with open('orchestrator/openapi/openapi.json') as f:
    spec = json.load(f)

with open('orchestrator/openapi/openapi.yaml', 'w') as f:
    yaml.dump(spec, f, default_flow_style=False)

print('Converted to YAML format')
"
```

---

## Testing API Versions

### Version Compatibility Tests

```python
# tests/api/test_versioning.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_versions_endpoint():
    """Test API versions endpoint"""
    response = client.get("/api/versions")
    assert response.status_code == 200

    data = response.json()
    assert "current" in data
    assert "supported" in data
    assert "v1" in data["supported"]

def test_v1_message_endpoint():
    """Test v1 message endpoint"""
    response = client.post(
        "/api/v1/goal/travel_planning/message",
        json={"message": "Plan trip to Japan"},
        headers={"Authorization": "Bearer test-token"}
    )
    assert response.status_code == 200
    assert "response" in response.json()
    assert "thread_id" in response.json()

def test_openapi_spec_valid():
    """Test OpenAPI spec is valid"""
    response = client.get("/openapi.json")
    assert response.status_code == 200

    spec = response.json()
    assert spec["openapi"] == "3.1.0"
    assert "paths" in spec
    assert "/api/v1/goal/travel_planning/message" in spec["paths"]

def test_backward_compatibility():
    """Test v1 still works when v2 exists"""
    # This test ensures v1 continues to work even after v2 is added
    response_v1 = client.post(
        "/api/v1/goal/travel_planning/message",
        json={"message": "Test"},
        headers={"Authorization": "Bearer test-token"}
    )
    assert response_v1.status_code == 200

def test_version_in_response_headers():
    """Test API version in response headers"""
    response = client.post(
        "/api/v1/goal/travel_planning/message",
        json={"message": "Test"},
        headers={"Authorization": "Bearer test-token"}
    )
    assert "X-API-Version" in response.headers
    assert response.headers["X-API-Version"] == "v1"
```

---

## Summary

### Explicit API Versioning

All APIs must declare:
1. ✅ **Versioning strategy** (URL path recommended)
2. ✅ **Current version** (v1, v2, etc.)
3. ✅ **Supported versions**
4. ✅ **Deprecated versions** with sunset dates

### OpenAPI Compliance

All APIs must provide:
1. ✅ **Complete OpenAPI 3.1 spec**
2. ✅ **Request/Response schemas** with validation
3. ✅ **Error responses** with error codes
4. ✅ **Security schemes** (Bearer, API Key)
5. ✅ **Rate limiting headers**
6. ✅ **Examples** for all endpoints

### Generated Code

GoalGen generates:
1. ✅ **Versioned routers** (/api/v1, /api/v2)
2. ✅ **Pydantic schemas** with validation
3. ✅ **OpenAPI documentation** (auto-generated)
4. ✅ **API version endpoint** (/api/versions)
5. ✅ **Deprecation headers** for sunset versions
6. ✅ **Version compatibility tests**

### Evolution Path

- **v1**: Initial API
- **v1.1**: Backward-compatible additions (new optional fields)
- **v2**: Breaking changes (new major version)
- **Deprecation**: v1 marked deprecated with Sunset header
- **Sunset**: v1 removed after grace period

This ensures **production-ready, evolvable APIs** from day one.
