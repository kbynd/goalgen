# Multiple Tool Instances

Guide for using multiple instances of the same tool type with different configurations.

## Overview

GoalGen's tool registry supports **multiple instances** of the same tool type, each with independent configurations. This enables scenarios like:

- Multiple databases (production DB, analytics DB, logging DB)
- Multiple vector stores (product catalog, support docs, company policies)
- Multiple API endpoints (staging API, production API, legacy API)

## How It Works

Each tool in `goal_spec.json` is instantiated **independently** with its own configuration:

```json
{
  "tools": {
    "tool_name_1": {
      "type": "sql",
      "spec": { /* config 1 */ }
    },
    "tool_name_2": {
      "type": "sql",
      "spec": { /* config 2 */ }
    }
  }
}
```

The `tool_name` becomes the unique identifier in the registry.

## Example: Multiple SQL Databases

### Scenario: E-Commerce Application

Access three different databases:
- **orders_db** - Transactional database (PostgreSQL)
- **analytics_db** - Read-only analytics (Snowflake via ODBC)
- **cache_db** - Fast lookup cache (SQLite)

### Configuration

```json
{
  "id": "ecommerce_assistant",
  "tools": {
    "orders_db": {
      "type": "sql",
      "description": "Transactional order database for customer purchases",
      "spec": {
        "connection_string": "${ORDERS_DB_CONNECTION}",
        "database_type": "postgresql",
        "read_only": true,
        "max_results": 100,
        "timeout": 30
      }
    },
    "analytics_db": {
      "type": "sql",
      "description": "Analytics warehouse for historical trends and reporting",
      "spec": {
        "connection_string": "${ANALYTICS_DB_CONNECTION}",
        "database_type": "postgresql",
        "read_only": true,
        "max_results": 1000,
        "timeout": 60
      }
    },
    "cache_db": {
      "type": "sql",
      "description": "Local cache for frequently accessed data",
      "spec": {
        "connection_string": "sqlite:///cache/lookup.db",
        "database_type": "sqlite",
        "read_only": false,
        "max_results": 50,
        "timeout": 5
      }
    }
  },
  "agents": {
    "order_agent": {
      "kind": "llm_agent",
      "tools": ["orders_db", "cache_db"]
    },
    "analytics_agent": {
      "kind": "llm_agent",
      "tools": ["analytics_db", "orders_db"]
    }
  }
}
```

### Usage in Agent

```python
from frmk.agents.base_agent import BaseAgent
from frmk.utils.data_parser import parse_sql_results

class OrderAgent(BaseAgent):
    async def lookup_order(self, order_id: int):
        # Check cache first (fast)
        cache_db = self.tool_registry.get("cache_db")
        cache_result = await cache_db.execute(
            query="SELECT * FROM order_cache WHERE order_id = :id",
            params={"id": order_id}
        )

        if cache_result.success and cache_result.data["rows"]:
            return parse_sql_results(cache_result.data)

        # Not in cache, query main database
        orders_db = self.tool_registry.get("orders_db")
        result = await orders_db.execute(
            query="SELECT * FROM orders WHERE order_id = :id",
            params={"id": order_id}
        )

        if result.success:
            # Update cache (cache_db has read_only=false)
            await cache_db.execute(
                query="INSERT INTO order_cache VALUES (:id, :data, :timestamp)",
                params={
                    "id": order_id,
                    "data": str(result.data),
                    "timestamp": "now"
                }
            )

        return parse_sql_results(result.data)

class AnalyticsAgent(BaseAgent):
    async def get_sales_trends(self):
        # Query analytics warehouse (different connection)
        analytics_db = self.tool_registry.get("analytics_db")

        result = await analytics_db.execute(
            query="""
                SELECT
                    DATE_TRUNC('month', order_date) as month,
                    SUM(total) as revenue,
                    COUNT(*) as order_count
                FROM orders_fact
                GROUP BY month
                ORDER BY month DESC
                LIMIT 12
            """
        )

        return parse_sql_results(result.data, format="markdown")
```

### Environment Variables

```bash
# Production order database
ORDERS_DB_CONNECTION="postgresql://user:pass@prod-db.company.com:5432/orders"

# Analytics warehouse
ANALYTICS_DB_CONNECTION="postgresql://user:pass@analytics-db.company.com:5432/warehouse"

# SQLite cache is local, no env var needed
```

## Example: Multiple Vector Databases

### Scenario: Multi-Domain Knowledge Search

Search across different knowledge domains:
- **product_catalog** - Product information (Azure AI Search)
- **support_docs** - Customer support articles (Pinecone)
- **company_policies** - HR and legal policies (Weaviate)

### Configuration

```json
{
  "tools": {
    "product_catalog": {
      "type": "vectordb",
      "description": "Product catalog with specifications and reviews",
      "spec": {
        "provider": "azure_ai_search",
        "endpoint": "${PRODUCT_SEARCH_ENDPOINT}",
        "api_key": "${PRODUCT_SEARCH_KEY}",
        "index_name": "products",
        "top_k": 10,
        "score_threshold": 0.75
      }
    },
    "support_docs": {
      "type": "vectordb",
      "description": "Customer support documentation and FAQs",
      "spec": {
        "provider": "pinecone",
        "endpoint": "${PINECONE_ENVIRONMENT}",
        "api_key": "${PINECONE_API_KEY}",
        "index_name": "support_articles",
        "top_k": 5,
        "score_threshold": 0.70
      }
    },
    "company_policies": {
      "type": "vectordb",
      "description": "Company policies, procedures, and guidelines",
      "spec": {
        "provider": "weaviate",
        "endpoint": "${WEAVIATE_ENDPOINT}",
        "api_key": "${WEAVIATE_API_KEY}",
        "index_name": "Policies",
        "top_k": 3,
        "score_threshold": 0.80
      }
    }
  },
  "agents": {
    "support_agent": {
      "kind": "llm_agent",
      "tools": ["product_catalog", "support_docs"]
    },
    "hr_agent": {
      "kind": "llm_agent",
      "tools": ["company_policies"]
    }
  }
}
```

### Usage in Agent

```python
from frmk.agents.base_agent import BaseAgent
from frmk.utils.data_parser import parse_vector_results

class SupportAgent(BaseAgent):
    async def answer_product_question(self, question: str):
        # Search both product catalog AND support docs
        product_catalog = self.tool_registry.get("product_catalog")
        support_docs = self.tool_registry.get("support_docs")

        # Parallel search across both indexes
        import asyncio

        product_results, support_results = await asyncio.gather(
            product_catalog.execute(query=question),
            support_docs.execute(query=question)
        )

        # Combine results
        response = "## Product Information\n\n"
        if product_results.success:
            response += parse_vector_results(product_results.data)

        response += "\n## Support Documentation\n\n"
        if support_results.success:
            response += parse_vector_results(support_results.data)

        return response

class HRAgent(BaseAgent):
    async def lookup_policy(self, policy_topic: str):
        # Search company policies (different vector DB)
        company_policies = self.tool_registry.get("company_policies")

        result = await company_policies.execute(
            query=policy_topic,
            filters={"category": "hr", "status": "active"}
        )

        return parse_vector_results(result.data, include_scores=True)
```

## Example: Multi-Region APIs

### Scenario: Global Service with Regional Endpoints

Call different API endpoints based on user location:
- **us_api** - US region endpoint
- **eu_api** - EU region endpoint
- **asia_api** - Asia-Pacific region endpoint

### Configuration

```json
{
  "tools": {
    "us_api": {
      "type": "http",
      "description": "US region API endpoint",
      "spec": {
        "url": "https://us-api.company.com/v1",
        "method": "POST",
        "auth": "bearer",
        "timeout": 30
      }
    },
    "eu_api": {
      "type": "http",
      "description": "EU region API endpoint",
      "spec": {
        "url": "https://eu-api.company.com/v1",
        "method": "POST",
        "auth": "bearer",
        "timeout": 30
      }
    },
    "asia_api": {
      "type": "http",
      "description": "Asia-Pacific region API endpoint",
      "spec": {
        "url": "https://asia-api.company.com/v1",
        "method": "POST",
        "auth": "bearer",
        "timeout": 30
      }
    }
  }
}
```

### Usage with Dynamic Selection

```python
class GlobalAgent(BaseAgent):
    def get_regional_api(self, user_region: str):
        """Get appropriate API based on user region"""
        region_mapping = {
            "us": "us_api",
            "eu": "eu_api",
            "asia": "asia_api"
        }

        tool_name = region_mapping.get(user_region, "us_api")  # Default to US
        return self.tool_registry.get(tool_name)

    async def process_request(self, user_region: str, data: dict):
        # Select the right API based on region
        api = self.get_regional_api(user_region)

        # Make request to region-specific endpoint
        result = await api.execute(**data)

        return result.data if result.success else result.error
```

## Example: Staging vs Production

### Scenario: Safe Testing Before Production

Use staging database/API for testing, production for live queries:

```json
{
  "tools": {
    "prod_db": {
      "type": "sql",
      "description": "Production customer database",
      "spec": {
        "connection_string": "${PROD_DB_CONNECTION}",
        "database_type": "azure_sql",
        "read_only": true
      }
    },
    "staging_db": {
      "type": "sql",
      "description": "Staging database for testing queries",
      "spec": {
        "connection_string": "${STAGING_DB_CONNECTION}",
        "database_type": "azure_sql",
        "read_only": false  // Allow testing writes in staging
      }
    }
  }
}
```

### Usage with Environment-Based Selection

```python
import os

class DataAgent(BaseAgent):
    def get_database(self):
        """Get database based on environment"""
        env = os.getenv("ENVIRONMENT", "staging")

        if env == "production":
            return self.tool_registry.get("prod_db")
        else:
            return self.tool_registry.get("staging_db")

    async def query_customers(self, customer_id: int):
        db = self.get_database()

        result = await db.execute(
            query="SELECT * FROM customers WHERE id = :id",
            params={"id": customer_id}
        )

        return result.data
```

## Key Points

### ✅ **Each Tool Instance is Independent**

- Separate connections
- Separate configurations (timeouts, max_results, etc.)
- Separate authentication
- No shared state

### ✅ **Tool Names Must Be Unique**

```json
{
  "tools": {
    "primary_db": { "type": "sql", ... },    // ✅ Unique name
    "secondary_db": { "type": "sql", ... },  // ✅ Different name, same type
    "cache": { "type": "sql", ... }          // ✅ Also unique
  }
}
```

### ✅ **Agents Can Access Multiple Tools**

```json
{
  "agents": {
    "data_agent": {
      "tools": ["primary_db", "secondary_db", "cache"]  // Access all three
    }
  }
}
```

### ✅ **Connection Pooling per Instance**

Each SQLTool instance has its own SQLAlchemy engine with connection pooling:

```python
# These maintain separate connection pools
orders_db = tool_registry.get("orders_db")      # Pool 1
analytics_db = tool_registry.get("analytics_db") # Pool 2
cache_db = tool_registry.get("cache_db")        # Pool 3
```

## Best Practices

### 1. Use Descriptive Tool Names

❌ **Bad:**
```json
{
  "db1": { "type": "sql" },
  "db2": { "type": "sql" }
}
```

✅ **Good:**
```json
{
  "customer_orders_db": { "type": "sql" },
  "inventory_db": { "type": "sql" }
}
```

### 2. Document Purpose in Description

```json
{
  "orders_db": {
    "type": "sql",
    "description": "Transactional order database - contains current order status and history"
  }
}
```

### 3. Use Environment Variables for Secrets

```json
{
  "connection_string": "${ORDERS_DB_CONNECTION}"  // ✅ From environment
}
```

Not:
```json
{
  "connection_string": "postgresql://user:password@..."  // ❌ Hardcoded secret
}
```

### 4. Set Appropriate Permissions

```json
{
  "prod_db": {
    "spec": {
      "read_only": true   // ✅ Safe for production
    }
  },
  "staging_db": {
    "spec": {
      "read_only": false  // ✅ Allow testing in staging
    }
  }
}
```

---

**Generated by GoalGen** | [Documentation](https://github.com/yourorg/goalgen)
