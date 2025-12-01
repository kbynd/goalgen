"""
SQL Database Tool
Common implementation for SQL queries across different databases
"""

from typing import Dict, Any, List, Optional
import os
from .base_tool import BaseTool, ToolOutput
from frmk.utils.logging import get_logger


class SQLTool(BaseTool):
    """
    SQL Database tool for querying relational databases

    Supported databases:
    - Azure SQL Database
    - PostgreSQL
    - MySQL
    - SQLite

    Configuration from spec:
    {
      "type": "sql",
      "spec": {
        "connection_string": "${SQL_CONNECTION_STRING}",
        "database_type": "azure_sql|postgresql|mysql|sqlite",
        "max_results": 100,
        "timeout": 30,
        "read_only": true  # Recommended for agent access
      }
    }
    """

    def __init__(self, name: str, description: str, tool_config: Dict[str, Any]):
        super().__init__(name, description, tool_config)

        self.logger = get_logger(f"tool.{name}")

        spec = tool_config.get("spec", {})

        # Resolve connection string from environment
        self.connection_string = self._resolve_env_vars(spec.get("connection_string", ""))
        self.database_type = spec.get("database_type", "azure_sql")
        self.max_results = spec.get("max_results", 100)
        self.timeout = spec.get("timeout", 30)
        self.read_only = spec.get("read_only", True)

        # Initialize database connection (lazy)
        self._connection = None
        self._engine = None

    def _resolve_env_vars(self, value: str) -> str:
        """Resolve ${VAR} in configuration"""
        import re

        def replacer(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))

        return re.sub(r'\$\{(\w+)\}', replacer, value)

    def _get_engine(self):
        """Get SQLAlchemy engine (lazy initialization)"""
        if self._engine is not None:
            return self._engine

        try:
            from sqlalchemy import create_engine

            # Create engine based on database type
            if self.database_type == "azure_sql":
                # Azure SQL requires specific driver
                self._engine = create_engine(
                    self.connection_string,
                    connect_args={"timeout": self.timeout}
                )
            elif self.database_type == "postgresql":
                self._engine = create_engine(
                    self.connection_string,
                    connect_args={"connect_timeout": self.timeout}
                )
            elif self.database_type == "mysql":
                self._engine = create_engine(
                    self.connection_string,
                    connect_args={"connect_timeout": self.timeout}
                )
            elif self.database_type == "sqlite":
                self._engine = create_engine(
                    self.connection_string,
                    connect_args={"timeout": self.timeout}
                )
            else:
                raise ValueError(f"Unsupported database type: {self.database_type}")

            self.logger.info(f"Connected to {self.database_type} database")
            return self._engine

        except ImportError:
            raise ImportError("SQLAlchemy not installed. Install with: pip install sqlalchemy")

    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> ToolOutput:
        """
        Execute SQL query

        Args:
            query: SQL query string (use :param syntax for parameters)
            params: Query parameters (optional)

        Returns:
            ToolOutput with query results
        """

        try:
            self.logger.info(f"Executing SQL query: {query[:100]}...")

            # Validate read-only mode
            if self.read_only:
                query_upper = query.strip().upper()
                if any(keyword in query_upper for keyword in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE"]):
                    self.logger.error("Write operation attempted in read-only mode")
                    return ToolOutput(
                        success=False,
                        error="Write operations not allowed in read-only mode"
                    )

            # Get engine
            engine = self._get_engine()

            # Execute query
            from sqlalchemy import text

            with engine.connect() as connection:
                result = connection.execute(text(query), params or {})

                # Fetch results for SELECT queries
                if result.returns_rows:
                    rows = result.fetchmany(self.max_results)
                    columns = list(result.keys())

                    # Convert to list of dicts
                    data = [
                        dict(zip(columns, row))
                        for row in rows
                    ]

                    self.logger.info(f"Query returned {len(data)} rows")

                    return ToolOutput(
                        success=True,
                        data={
                            "rows": data,
                            "columns": columns,
                            "row_count": len(data),
                            "truncated": len(rows) >= self.max_results
                        },
                        metadata={
                            "query": query,
                            "database_type": self.database_type
                        }
                    )
                else:
                    # DML/DDL query
                    rowcount = result.rowcount
                    self.logger.info(f"Query affected {rowcount} rows")

                    return ToolOutput(
                        success=True,
                        data={"affected_rows": rowcount},
                        metadata={
                            "query": query,
                            "database_type": self.database_type
                        }
                    )

        except Exception as e:
            self.logger.error(f"SQL query failed: {e}")
            return ToolOutput(
                success=False,
                error=str(e),
                metadata={"query": query}
            )

    def get_schema(self) -> Dict[str, Any]:
        """Get JSON schema for SQL query parameters"""

        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": f"SQL query to execute. {'Read-only queries only (SELECT).' if self.read_only else 'Supports SELECT, INSERT, UPDATE, DELETE.'} Use :param syntax for parameters."
                },
                "params": {
                    "type": "object",
                    "description": "Query parameters (optional). Keys should match :param placeholders in query.",
                    "additionalProperties": True
                }
            },
            "required": ["query"]
        }

    async def close(self):
        """Close database connection"""
        if self._engine:
            self._engine.dispose()
            self.logger.info("Database connection closed")


class AzureSQLTool(SQLTool):
    """Azure SQL Database-specific tool with Managed Identity support"""

    def __init__(self, name: str, description: str, tool_config: Dict[str, Any]):
        # Set database type to azure_sql
        tool_config["spec"]["database_type"] = "azure_sql"
        super().__init__(name, description, tool_config)

    def _get_connection_string_with_managed_identity(self) -> str:
        """Get connection string using Azure Managed Identity"""

        try:
            from azure.identity import DefaultAzureCredential
            import struct

            # Get access token for Azure SQL
            credential = DefaultAzureCredential()
            token = credential.get_token("https://database.windows.net/.default")

            # Convert token to bytes for ODBC
            token_bytes = token.token.encode("UTF-16-LE")
            token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)

            # Build connection string
            # Parse server and database from base connection string
            import re
            match = re.search(r"Server=([^;]+);.*Database=([^;]+)", self.connection_string)
            if match:
                server = match.group(1)
                database = match.group(2)

                return f"mssql+pyodbc://@{server}/{database}?driver=ODBC+Driver+18+for+SQL+Server"

            return self.connection_string

        except Exception as e:
            self.logger.warning(f"Failed to use Managed Identity: {e}, falling back to connection string")
            return self.connection_string
