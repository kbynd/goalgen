"""
PostgreSQL implementation for conversation mapping storage
"""

from frmk.conversation.datastore import ConversationDataStore
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


class PostgreSQLDataStore(ConversationDataStore):
    """
    PostgreSQL implementation for conversation mapping storage

    Schema:
        CREATE TABLE conversation_mappings (
            thread_id VARCHAR(64) PRIMARY KEY,
            tenant_id VARCHAR(128) NOT NULL,
            conversation_id VARCHAR(256) NOT NULL,
            user_id VARCHAR(128) NOT NULL,
            conversation_type VARCHAR(32) NOT NULL,
            user_name VARCHAR(256),
            channel_id VARCHAR(256),
            service_url VARCHAR(512),
            langgraph_workflow_endpoint VARCHAR(512),
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            last_activity_at TIMESTAMP NOT NULL DEFAULT NOW(),
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            metadata JSONB,
            UNIQUE(tenant_id, conversation_id, user_id)
        );

        CREATE INDEX idx_tenant_conversation ON conversation_mappings(tenant_id, conversation_id);
        CREATE INDEX idx_tenant_user ON conversation_mappings(tenant_id, user_id);
        CREATE INDEX idx_last_activity ON conversation_mappings(last_activity_at) WHERE is_active = TRUE;
    """

    def __init__(self, connection_string: str):
        if not POSTGRES_AVAILABLE:
            raise ImportError(
                "psycopg2 package required for PostgreSQLDataStore. "
                "Install with: pip install psycopg2-binary"
            )

        self.connection_string = connection_string
        self._ensure_schema()

    def _get_connection(self):
        return psycopg2.connect(self.connection_string, cursor_factory=RealDictCursor)

    def _ensure_schema(self):
        """Create table if not exists"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS conversation_mappings (
                        thread_id VARCHAR(64) PRIMARY KEY,
                        tenant_id VARCHAR(128) NOT NULL,
                        conversation_id VARCHAR(256) NOT NULL,
                        user_id VARCHAR(128) NOT NULL,
                        conversation_type VARCHAR(32) NOT NULL,
                        user_name VARCHAR(256),
                        channel_id VARCHAR(256),
                        service_url VARCHAR(512),
                        langgraph_workflow_endpoint VARCHAR(512),
                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        last_activity_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        is_active BOOLEAN NOT NULL DEFAULT TRUE,
                        metadata JSONB,
                        UNIQUE(tenant_id, conversation_id, user_id)
                    )
                """)

                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tenant_conversation
                    ON conversation_mappings(tenant_id, conversation_id)
                """)

                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tenant_user
                    ON conversation_mappings(tenant_id, user_id)
                """)

                conn.commit()

    def find_mapping(
        self,
        tenant_id: str,
        conversation_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Find existing mapping"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM conversation_mappings
                    WHERE tenant_id = %s
                    AND conversation_id = %s
                    AND user_id = %s
                    AND is_active = TRUE
                """, (tenant_id, conversation_id, user_id))

                return dict(cur.fetchone()) if cur.rowcount > 0 else None

    def get_by_thread_id(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get mapping by thread_id"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM conversation_mappings
                    WHERE thread_id = %s
                """, (thread_id,))

                return dict(cur.fetchone()) if cur.rowcount > 0 else None

    def create_mapping(self, mapping_data: Dict[str, Any]) -> None:
        """Create new mapping"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO conversation_mappings
                    (thread_id, tenant_id, conversation_id, user_id, conversation_type,
                     user_name, channel_id, service_url, langgraph_workflow_endpoint,
                     created_at, last_activity_at, is_active, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    mapping_data["thread_id"],
                    mapping_data["tenant_id"],
                    mapping_data["conversation_id"],
                    mapping_data["user_id"],
                    mapping_data["conversation_type"],
                    mapping_data.get("user_name"),
                    mapping_data.get("channel_id"),
                    mapping_data.get("service_url"),
                    mapping_data.get("langgraph_workflow_endpoint"),
                    mapping_data["created_at"],
                    mapping_data["last_activity_at"],
                    mapping_data.get("is_active", True),
                    json.dumps(mapping_data.get("metadata", {}))
                ))
                conn.commit()

    def update_activity(self, thread_id: str) -> None:
        """Update last_activity_at"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE conversation_mappings
                    SET last_activity_at = NOW()
                    WHERE thread_id = %s
                """, (thread_id,))
                conn.commit()

    def cleanup_inactive(self, cutoff_date: datetime) -> int:
        """Delete inactive mappings"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM conversation_mappings
                    WHERE last_activity_at < %s
                    AND is_active = TRUE
                """, (cutoff_date,))
                conn.commit()
                return cur.rowcount

    def get_active_conversations(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get active conversations for tenant"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM conversation_mappings
                    WHERE tenant_id = %s
                    AND is_active = TRUE
                    ORDER BY last_activity_at DESC
                """, (tenant_id,))

                return [dict(row) for row in cur.fetchall()]

    def deactivate(self, thread_id: str) -> None:
        """Mark conversation as inactive"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE conversation_mappings
                    SET is_active = FALSE
                    WHERE thread_id = %s
                """, (thread_id,))
                conn.commit()
