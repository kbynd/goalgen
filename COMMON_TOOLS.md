# Common Tools Reference

Pre-built, production-ready tool implementations in the GoalGen Core SDK (frmk/tools/).

## Overview

GoalGen provides **common tool implementations** that generated applications can use out-of-the-box. These tools handle typical integration patterns:

- ✅ **SQLTool** - Query relational databases (Azure SQL, PostgreSQL, MySQL, SQLite)
- ✅ **VectorDBTool** - Semantic search across vector databases (Azure AI Search, Pinecone, Weaviate, Qdrant, Chroma)
- ✅ **HTTPTool** - Call REST APIs with authentication and retry logic
- ✅ **WebSocketTool** - Real-time bidirectional communication
- ✅ **FunctionTool** - Execute local Python functions

## SQL Tool

### Supported Databases

- Azure SQL Database (with Managed Identity support)
- PostgreSQL
- MySQL
- SQLite

### Configuration

Add to your `goal_spec.json`:

```json
{
  "tools": {
    "customer_db": {
      "type": "sql",
      "description": "Query customer database for order history and preferences",
      "spec": {
        "connection_string": "${CUSTOMER_DB_CONNECTION_STRING}",
        "database_type": "azure_sql",
        "max_results": 100,
        "timeout": 30,
        "read_only": true
      }
    }
  }
}
```

### Usage in Agent

```python
from frmk.core.tool_registry import get_tool_registry
from frmk.utils.data_parser import parse_sql_results

# Get tool from registry
tool_registry = get_tool_registry(goal_config)
customer_db = tool_registry.get("customer_db")

# Execute query
result = await customer_db.execute(
    query="SELECT * FROM orders WHERE customer_id = :customer_id ORDER BY order_date DESC",
    params={"customer_id": 12345}
)

if result.success:
    # Format results for LLM
    formatted = parse_sql_results(result.data, format="markdown")
    print(formatted)

    # Output:
    # | order_id | customer_id | order_date | total |
    # | --- | --- | --- | --- |
    # | 1001 | 12345 | 2025-01-15 | $234.56 |
    # | 1002 | 12345 | 2025-01-10 | $89.99 |
else:
    print(f"Query failed: {result.error}")
```

### Azure SQL with Managed Identity

```json
{
  "tools": {
    "enterprise_db": {
      "type": "sql",
      "spec": {
        "connection_string": "Server=myserver.database.windows.net;Database=mydb",
        "database_type": "azure_sql"
      }
    }
  }
}
```

The `AzureSQLTool` automatically uses `DefaultAzureCredential` for authentication when deployed to Azure.

### Read-Only Safety

By default, `read_only: true` prevents agents from modifying data:

```python
# This will be rejected
result = await db.execute("DELETE FROM orders WHERE customer_id = 123")
# Returns: ToolOutput(success=False, error="Write operations not allowed in read-only mode")
```

Set `read_only: false` only if agents need write access.

## Vector Database Tool

### Supported Providers

- **Azure AI Search** (Cognitive Search with vector support)
- **Pinecone**
- **Weaviate**
- **Qdrant**
- **Chroma**

### Configuration

```json
{
  "tools": {
    "knowledge_base": {
      "type": "vectordb",
      "description": "Search company knowledge base and documentation",
      "spec": {
        "provider": "azure_ai_search",
        "endpoint": "${AZURE_SEARCH_ENDPOINT}",
        "api_key": "${AZURE_SEARCH_KEY}",
        "index_name": "company_docs",
        "embedding_model": "text-embedding-ada-002",
        "top_k": 5,
        "score_threshold": 0.7
      }
    }
  }
}
```

### Usage in Agent

```python
from frmk.core.tool_registry import get_tool_registry
from frmk.utils.data_parser import parse_vector_results

# Get tool
knowledge_base = tool_registry.get("knowledge_base")

# Semantic search
result = await knowledge_base.execute(
    query="How do I reset a customer password?",
    filters={"category": "support"}
)

if result.success:
    # Format for LLM
    formatted = parse_vector_results(result.data, include_scores=True)
    print(formatted)

    # Output:
    # Found 3 relevant documents:
    #
    # **Result 1**
    # Relevance: 89.34%
    # ```
    # To reset a customer password, navigate to Settings > Users...
    # ```
    # Metadata: {"category": "support", "last_updated": "2025-01-15"}
```

### Provider-Specific Configuration

**Pinecone:**
```json
{
  "spec": {
    "provider": "pinecone",
    "endpoint": "${PINECONE_ENVIRONMENT}",
    "api_key": "${PINECONE_API_KEY}",
    "index_name": "documents"
  }
}
```

**Weaviate:**
```json
{
  "spec": {
    "provider": "weaviate",
    "endpoint": "https://my-cluster.weaviate.network",
    "api_key": "${WEAVIATE_API_KEY}",
    "index_name": "Documents"
  }
}
```

**Qdrant:**
```json
{
  "spec": {
    "provider": "qdrant",
    "endpoint": "https://xyz.qdrant.io",
    "api_key": "${QDRANT_API_KEY}",
    "index_name": "my_collection"
  }
}
```

### Automatic Embedding Generation

VectorDBTool automatically generates embeddings using Azure OpenAI:

```python
# User query is converted to vector automatically
result = await knowledge_base.execute(query="product documentation")

# Behind the scenes:
# 1. Calls Azure OpenAI embeddings API
# 2. Converts text to 1536-dimensional vector
# 3. Searches vector database
# 4. Returns top_k results above score_threshold
```

## Data Parsing Utilities

Common utilities for formatting tool results for LLM consumption.

### Parse SQL Results

```python
from frmk.utils.data_parser import parse_sql_results

# Markdown table (best for LLM context)
markdown = parse_sql_results(sql_result.data, format="markdown")

# JSON (structured data)
json_str = parse_sql_results(sql_result.data, format="json")

# Plain text table
text = parse_sql_results(sql_result.data, format="text")
```

### Parse Vector Search Results

```python
from frmk.utils.data_parser import parse_vector_results

# Include relevance scores
formatted = parse_vector_results(vector_result.data, include_scores=True)
```

### Format Currency

```python
from frmk.utils.data_parser import format_currency

format_currency(1234.56, "USD")  # "$1,234.56"
format_currency(1000, "EUR")     # "€1,000.00"
format_currency(5000, "JPY")     # "¥5,000"
```

### Format Dates

```python
from frmk.utils.data_parser import format_date

format_date("2025-01-15", "readable")  # "January 15, 2025"
format_date("2025-01-15", "iso")       # "2025-01-15T00:00:00"
format_date("2025-01-15", "short")     # "01/15/2025"
```

### Extract Summary Statistics

```python
from frmk.utils.data_parser import extract_summary_stats

stats = extract_summary_stats(sql_result.data["rows"])
# Returns:
# {
#   "count": 150,
#   "price": {
#     "min": 9.99,
#     "max": 299.99,
#     "avg": 87.45,
#     "sum": 13117.50
#   }
# }
```

### Parse HTTP JSON Response

```python
from frmk.utils.data_parser import parse_http_json_response

# Extract nested data with dot notation
data = {
    "response": {
        "items": [
            {"name": "Product A", "price": 29.99},
            {"name": "Product B", "price": 49.99}
        ]
    }
}

# Extract specific value
price = parse_http_json_response(data, "response.items[0].price")
# Returns: 29.99
```

## Complete Example: E-Commerce Agent

### Goal Spec

```json
{
  "id": "ecommerce_assistant",
  "agents": {
    "order_lookup_agent": {
      "kind": "llm_agent",
      "tools": ["order_db", "product_search"],
      "llm_config": {"model": "gpt-4"}
    }
  },
  "tools": {
    "order_db": {
      "type": "sql",
      "description": "Query customer orders and transaction history",
      "spec": {
        "connection_string": "${ORDER_DB_CONNECTION}",
        "database_type": "postgresql",
        "read_only": true,
        "max_results": 50
      }
    },
    "product_search": {
      "type": "vectordb",
      "description": "Search product catalog semantically",
      "spec": {
        "provider": "azure_ai_search",
        "endpoint": "${SEARCH_ENDPOINT}",
        "api_key": "${SEARCH_KEY}",
        "index_name": "products",
        "top_k": 10
      }
    }
  }
}
```

### Agent Implementation

```python
from frmk.agents.base_agent import BaseAgent
from frmk.utils.data_parser import (
    parse_sql_results,
    parse_vector_results,
    format_currency,
    format_date
)

class OrderLookupAgent(BaseAgent):
    async def handle_order_inquiry(self, customer_id: int, state: dict):
        # Query order history
        order_db = self.tool_registry.get("order_db")

        order_result = await order_db.execute(
            query="""
                SELECT order_id, order_date, total, status
                FROM orders
                WHERE customer_id = :customer_id
                ORDER BY order_date DESC
                LIMIT 5
            """,
            params={"customer_id": customer_id}
        )

        if not order_result.success:
            return f"Unable to retrieve orders: {order_result.error}"

        # Format for LLM context
        orders_table = parse_sql_results(order_result.data, format="markdown")

        # Calculate stats
        stats = extract_summary_stats(
            order_result.data["rows"],
            numeric_columns=["total"]
        )

        # Build response
        response = f"""
Customer Order History:

{orders_table}

Summary:
- Total orders: {stats['count']}
- Average order: {format_currency(stats['total']['avg'])}
- Total spent: {format_currency(stats['total']['sum'])}
"""

        return response

    async def search_products(self, query: str):
        # Semantic search
        product_search = self.tool_registry.get("product_search")

        result = await product_search.execute(
            query=query,
            filters={"in_stock": True}
        )

        if not result.success:
            return f"Search failed: {result.error}"

        # Format results
        return parse_vector_results(result.data, include_scores=True)
```

## Environment Variables

### Required for SQL Tools

```bash
# Connection strings
ORDER_DB_CONNECTION="postgresql://user:pass@host:5432/db"
CUSTOMER_DB_CONNECTION_STRING="Server=myserver.database.windows.net;Database=mydb;User=admin;Password=xxx"

# For SQLite
ANALYTICS_DB_CONNECTION="sqlite:///data/analytics.db"
```

### Required for Vector DB Tools

```bash
# Azure AI Search
AZURE_SEARCH_ENDPOINT="https://mysearch.search.windows.net"
AZURE_SEARCH_KEY="xxx"

# Embeddings (required for all vector tools)
AZURE_OPENAI_ENDPOINT="https://myopenai.openai.azure.com/"
AZURE_OPENAI_KEY="xxx"

# Pinecone
PINECONE_API_KEY="xxx"
PINECONE_ENVIRONMENT="us-west1-gcp"

# Weaviate
WEAVIATE_API_KEY="xxx"

# Qdrant
QDRANT_API_KEY="xxx"
```

## Dependencies

Add to your `requirements.txt`:

```txt
# SQL Tools
sqlalchemy>=2.0.0
pyodbc>=5.0.0           # For Azure SQL
psycopg2-binary>=2.9.0  # For PostgreSQL
pymysql>=1.1.0          # For MySQL

# Vector DB Tools
azure-search-documents>=11.4.0  # For Azure AI Search
pinecone-client>=3.0.0          # For Pinecone
weaviate-client>=4.0.0          # For Weaviate
qdrant-client>=1.7.0            # For Qdrant
chromadb>=0.4.0                 # For Chroma

# Embeddings
openai>=1.0.0

# Azure Identity (for Managed Identity)
azure-identity>=1.15.0
```

## Best Practices

### 1. Use Read-Only Mode for Agents

```json
{
  "spec": {
    "read_only": true  // Prevents accidental data modification
  }
}
```

### 2. Limit Result Set Size

```json
{
  "spec": {
    "max_results": 100  // Prevent overwhelming LLM context
  }
}
```

### 3. Use Parameterized Queries

❌ **Bad** (SQL injection risk):
```python
query = f"SELECT * FROM users WHERE email = '{email}'"
```

✅ **Good**:
```python
query = "SELECT * FROM users WHERE email = :email"
params = {"email": email}
```

### 4. Format Results for LLMs

Always use parsing utilities to format data:

```python
# Raw data is hard for LLM to parse
raw_data = result.data["rows"]

# Formatted data is clear
formatted = parse_sql_results(result.data, format="markdown")
```

### 5. Handle Errors Gracefully

```python
result = await tool.execute(query)

if result.success:
    return parse_sql_results(result.data)
else:
    return f"Unable to query database: {result.error}"
```

## Testing Common Tools

All tools can be tested locally without deployment:

```python
# Test SQL tool
from frmk.tools.sql_tool import SQLTool

config = {
    "spec": {
        "connection_string": "sqlite:///test.db",
        "database_type": "sqlite",
        "read_only": True
    }
}

tool = SQLTool("test_db", "Test database", config)
result = await tool.execute("SELECT * FROM users LIMIT 5")
print(result.data)
```

---

**Generated by GoalGen** | [Documentation](https://github.com/yourorg/goalgen)
