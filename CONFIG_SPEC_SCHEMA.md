# Enhanced Goal Spec Schema with Configuration Support

Based on the configuration matrix, here's the complete goal spec JSON schema that includes build-time, deploy-time, and runtime configuration sections.

## Complete Goal Spec Structure

```json
{
  "id": "string",
  "title": "string",
  "description": "string",
  "version": "string",

  "triggers": ["string"],
  "context_fields": ["string"],

  "tasks": [
    {
      "id": "string",
      "type": "evaluator|task",
      "tools": ["string"],
      "timeout": "number (optional)",
      "retry_policy": {
        "max_attempts": "number",
        "backoff_strategy": "linear|exponential"
      }
    }
  ],

  "agents": {
    "agent_name": {
      "kind": "supervisor|llm_agent|function_agent",
      "policy": "string (for supervisor)",
      "tools": ["string"],
      "max_loop": "number",
      "prompt_template": "string (path)",
      "pattern": "string (optional: 'react'|'chain_of_thought'|'planning' - v0.3.0+)",
      "reflection": "boolean (optional: enable self-reflection - v0.3.0+)",
      "llm_config": {
        "model": "string (default model)",
        "temperature": "number (default)",
        "max_tokens": "number (default)",
        "streaming": "boolean (default)"
      }
    }
  },

  "tools": {
    "tool_name": {
      "type": "http|internal|function",
      "spec": {
        "url": "string (with placeholders)",
        "method": "string (for http)",
        "auth": "key|oauth|managed_identity",
        "timeout": "number (seconds)",
        "retry_attempts": "number",
        "cache_ttl": "number (seconds, optional)"
      }
    }
  },

  "evaluators": [
    {
      "id": "string",
      "checks": [
        {
          "field": "string",
          "action": "ask_user|set_default|abort",
          "validation": {
            "type": "presence|regex|range|enum",
            "pattern": "string (for regex)",
            "min": "number (for range)",
            "max": "number (for range)",
            "values": ["string"]
          }
        }
      ],
      "timeout": "number (optional)"
    }
  ],

  "ux": {
    "teams": {
      "enabled": "boolean",
      "bot_name": "string",
      "message_style": "text|adaptiveCard",
      "commands": ["string"],
      "multi_language": "boolean"
    },
    "api": {
      "enabled": "boolean",
      "base_path": "string",
      "auth_type": "jwt|api_key|none",
      "cors_origins": ["string"],
      "request_timeout": "number",
      "rate_limits": {
        "requests_per_minute": "number"
      }
    },
    "webchat": {
      "enabled": "boolean",
      "theme": "light|dark|auto",
      "features": {
        "file_upload": "boolean",
        "voice": "boolean",
        "video": "boolean"
      }
    }
  },

  "assets": {
    "logo": "string (path)",
    "images": "string (directory)",
    "prompts": "string (directory)"
  },

  "langgraph": {
    "checkpointer_type": "cosmos|redis|blob",
    "supervisor_policy": "simple_router|llm_router|custom",
    "max_iterations": "number",
    "state_ttl": "number (seconds)",
    "human_in_loop": "boolean"
  },

  "deployment": {
    "targets": ["containerapps", "functions", "aks"],
    "regions": ["string"],
    "high_availability": "boolean",
    "multi_region": "boolean",

    "variables": {
      "VARIABLE_NAME": "string (value or reference)"
    },

    "environments": {
      "dev": {
        "subscription_id": "string",
        "resource_group": "string",
        "location": "string"
      },
      "staging": {
        "subscription_id": "string",
        "resource_group": "string",
        "location": "string"
      },
      "prod": {
        "subscription_id": "string",
        "resource_group": "string",
        "location": "string"
      }
    },

    "resources": {
      "orchestrator": {
        "cpu": "number (cores)",
        "memory": "string (e.g., '2Gi')",
        "min_replicas": "number",
        "max_replicas": "number"
      },
      "cosmos": {
        "throughput": "number (RU/s)",
        "consistency": "eventual|session|strong"
      },
      "redis": {
        "sku": "basic|standard|premium",
        "capacity": "number (0-6)"
      }
    },

    "security": {
      "managed_identity": "system|user",
      "key_vault_name": "string",
      "secrets": [
        {
          "name": "string",
          "source": "manual|reference"
        }
      ],
      "network": {
        "vnet_integration": "boolean",
        "private_endpoints": "boolean"
      }
    },

    "monitoring": {
      "app_insights": "boolean",
      "log_analytics": "boolean",
      "alerts": [
        {
          "metric": "string",
          "threshold": "number",
          "action": "string"
        }
      ]
    },

    "cicd": {
      "provider": "github|azdo|gitlab",
      "branch_strategy": "gitflow|trunk",
      "auto_deploy": {
        "dev": "boolean",
        "staging": "boolean",
        "prod": "boolean"
      },
      "approval_required": {
        "staging": "boolean",
        "prod": "boolean"
      },
      "tests": {
        "unit": "boolean",
        "integration": "boolean",
        "e2e": "boolean",
        "load": "boolean"
      }
    }
  },

  "runtime_config": {
    "feature_flags_provider": "none|azure_app_config|launchdarkly",
    "dynamic_config_refresh": "number (seconds)",
    "scaling": {
      "orchestrator": {
        "cpu_threshold": "number (percentage)",
        "memory_threshold": "number (percentage)",
        "http_queue_threshold": "number"
      }
    }
  }
}
```

## Configuration Extraction by Generator

### scaffold
- `id`, `title`, `description` → README.md
- `version` → package metadata

### langgraph
- `context_fields` → QuestState schema
- `tasks` → Node generation
- `langgraph.*` → Checkpointer and supervisor config
- `tasks[].timeout`, `tasks[].retry_policy` → Task wrappers

### agents
- `agents.*` → Agent implementations
- `agents.*.llm_config` → Default LLM settings
- `agents.*.prompt_template` → Prompt loading
- `agents.*.pattern` → Agentic design pattern (react, chain_of_thought, planning) - v0.3.0+
- `agents.*.reflection` → Enable self-reflection loop for quality control - v0.3.0+

### evaluators
- `evaluators.*` → Evaluator logic
- `evaluators[].checks` → Validation rules

### tools
- `tools.*` → Tool implementations
- `tools.*.spec` → HTTP/function configuration

### api
- `ux.api.*` → FastAPI configuration
- `deployment.variables` → Environment variables

### infra
- `deployment.targets` → Which Bicep modules to include
- `deployment.environments` → Parameter files
- `deployment.resources` → Resource sizing in Bicep
- `deployment.security` → Security modules
- `deployment.monitoring` → Monitoring resources

### security
- `deployment.security.*` → Key Vault setup
- Managed Identity configuration

### teams
- `ux.teams.*` → Teams manifest and config

### webchat
- `ux.webchat.*` → React app configuration

### assets
- `assets.*` → Copy files and generate prompts

### cicd
- `deployment.cicd.*` → GitHub Actions configuration

### deployment
- `deployment.environments.*` → Deploy script parameters
- `deployment.regions` → Multi-region logic

### tests
- `deployment.cicd.tests` → Test configuration
- Docker Compose setup for local testing

## Configuration File Generation

Generators should produce these configuration files:

1. **infra/parameters.dev.json**
   ```json
   {
     "orchestratorImage": "...",
     "keyVaultName": "...",
     "cosmosAccountName": "...",
     "location": "...",
     "minReplicas": 1,
     "maxReplicas": 3
   }
   ```

2. **infra/parameters.staging.json** (similar, scaled up)

3. **infra/parameters.prod.json** (similar, production scale)

4. **orchestrator/.env.sample**
   ```
   # Deploy-time configs
   KEYVAULT_URL=https://<keyvault-name>.vault.azure.net/
   COSMOS_ENDPOINT=https://<cosmos-account>.documents.azure.com:443/
   REDIS_HOST=<redis-name>.redis.cache.windows.net
   SIGNALR_CONN=<from-keyvault>

   # Runtime configs
   LOG_LEVEL=INFO
   MAX_RETRIES=3
   REQUEST_TIMEOUT=30
   FEATURE_FLAG_REFRESH_INTERVAL=60
   ```

5. **config/scaling-rules.json**
   ```json
   {
     "orchestrator": {
       "cpu": { "threshold": 70, "scaleUp": 1, "scaleDown": 1 },
       "memory": { "threshold": 80, "scaleUp": 1, "scaleDown": 1 },
       "http": { "queueDepth": 100, "scaleUp": 2 }
     }
   }
   ```

6. **orchestrator/app/config.py**
   ```python
   from azure.identity import DefaultAzureCredential
   from azure.keyvault.secrets import SecretClient
   from pydantic import BaseSettings

   class Settings(BaseSettings):
       # Build-time defaults
       goal_id: str
       max_iterations: int = 10

       # Deploy-time configs
       keyvault_url: str
       cosmos_endpoint: str

       # Runtime configs (from env or App Config)
       log_level: str = "INFO"
       max_retries: int = 3

       class Config:
           env_file = ".env"
   ```

## Validation Requirements

Each generator should validate:
1. Required fields in spec are present
2. Referenced resources exist (e.g., tool names in agent.tools)
3. Configuration values are in valid ranges
4. Conflicting configurations (e.g., can't enable Teams without bot_name)
