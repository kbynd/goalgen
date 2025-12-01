"""
Azure Conversation API Bridge
Tracks conversations for analytics, compliance, and insights
"""

from azure.ai.language.conversations import ConversationAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from typing import Dict, Any, List, Optional
from frmk.utils.logging import get_logger
import os

logger = get_logger("conversation_tracker")


class AzureConversationTracker:
    """
    Track conversations in Azure Conversation API

    Purpose:
    - Analytics and insights (intent, entities, sentiment)
    - Compliance and audit trail
    - Long-term conversation history
    - Product insights

    Note: This is ASYNC and non-blocking - doesn't delay user responses
    """

    def __init__(self, config: Dict[str, Any]):
        conversation_config = config.get("conversation_api", {})

        self.enabled = conversation_config.get("enabled", False)

        if not self.enabled:
            logger.info("Azure Conversation API tracking disabled")
            return

        # Get endpoint and authentication
        endpoint = conversation_config.get("endpoint") or os.getenv("CONVERSATION_API_ENDPOINT")

        if not endpoint:
            logger.warning("Conversation API endpoint not configured")
            self.enabled = False
            return

        # Auth: Managed Identity or API Key
        auth_type = conversation_config.get("auth", "managed_identity")

        if auth_type == "managed_identity":
            credential = DefaultAzureCredential()
            self.client = ConversationAnalysisClient(endpoint, credential)
        elif auth_type == "api_key":
            api_key = conversation_config.get("api_key") or os.getenv("CONVERSATION_API_KEY")
            credential = AzureKeyCredential(api_key)
            self.client = ConversationAnalysisClient(endpoint, credential)
        else:
            raise ValueError(f"Unknown auth type: {auth_type}")

        self.project_name = conversation_config.get("project_name")
        self.deployment_name = conversation_config.get("deployment_name", "production")

        # Features
        features = conversation_config.get("features", {})
        self.intent_recognition = features.get("intent_recognition", True)
        self.entity_extraction = features.get("entity_extraction", True)
        self.sentiment_analysis = features.get("sentiment_analysis", True)

        logger.info(f"Conversation tracker initialized (project: {self.project_name})")

    async def track_message(
        self,
        thread_id: str,
        user_id: str,
        message: str,
        role: str,  # "user" or "assistant"
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Track message in Azure Conversation API

        Args:
            thread_id: Conversation thread ID
            user_id: User ID
            message: Message content
            role: "user" or "assistant"
            metadata: Additional metadata

        Returns:
            Insights (intent, entities, sentiment) or None if disabled
        """

        if not self.enabled:
            return None

        metadata = metadata or {}

        try:
            # Build conversation item
            conversation_item = {
                "id": metadata.get("message_id", f"{thread_id}_{role}_{hash(message)}"),
                "participantId": user_id,
                "text": message,
                "role": role,
                "language": metadata.get("language", "en")
            }

            # Analyze conversation
            result = await self.client.analyze_conversation(
                task={
                    "kind": "Conversation",
                    "analysisInput": {
                        "conversationItem": conversation_item
                    },
                    "parameters": {
                        "projectName": self.project_name,
                        "deploymentName": self.deployment_name,
                        "stringIndexType": "TextElement_V8",
                        "verbose": True
                    }
                }
            )

            # Extract insights
            insights = self._extract_insights(result)

            logger.debug(f"Message tracked: {thread_id}", extra={
                "thread_id": thread_id,
                "role": role,
                "insights": insights
            })

            return insights

        except Exception as e:
            # Don't fail main flow if analytics fails
            logger.error(f"Failed to track message: {e}")
            return None

    def _extract_insights(self, result) -> Dict[str, Any]:
        """Extract insights from Conversation API response"""

        insights = {}

        # Intent
        if hasattr(result, 'prediction') and hasattr(result.prediction, 'top_intent'):
            insights["intent"] = {
                "name": result.prediction.top_intent,
                "confidence": result.prediction.intents[0].confidence if result.prediction.intents else None
            }

        # Entities
        if hasattr(result, 'prediction') and hasattr(result.prediction, 'entities'):
            insights["entities"] = [
                {
                    "text": entity.text,
                    "category": entity.category,
                    "confidence": entity.confidence_score
                }
                for entity in result.prediction.entities
            ]

        # Sentiment
        if hasattr(result, 'sentiment'):
            insights["sentiment"] = {
                "label": result.sentiment,
                "scores": getattr(result, 'confidence_scores', {})
            }

        return insights

    async def get_conversation_summary(
        self,
        thread_id: str,
        time_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Get conversation summary and analytics

        Args:
            thread_id: Thread ID
            time_range: {"start": "2024-01-01", "end": "2024-01-31"}

        Returns:
            Summary with intents, entities, sentiment trends
        """

        if not self.enabled:
            return {}

        try:
            # Query conversation history
            # Note: Implementation depends on Azure Conversation API capabilities

            # For now, return placeholder
            return {
                "thread_id": thread_id,
                "message_count": 0,
                "intents": [],
                "entities": [],
                "sentiment": "neutral"
            }

        except Exception as e:
            logger.error(f"Failed to get conversation summary: {e}")
            return {}

    async def export_conversations(
        self,
        output_path: str,
        filters: Optional[Dict[str, Any]] = None
    ):
        """
        Export conversations for compliance/audit

        Args:
            output_path: Azure Blob path or local path
            filters: Filter criteria (date range, user_id, etc.)
        """

        if not self.enabled:
            return

        try:
            logger.info(f"Exporting conversations to {output_path}")

            # TODO: Implement export logic
            # Could export to:
            # - Azure Blob Storage
            # - Data Lake
            # - Local file

        except Exception as e:
            logger.error(f"Failed to export conversations: {e}")


# Global singleton
_conversation_tracker: Optional[AzureConversationTracker] = None


def get_conversation_tracker(config: Optional[Dict[str, Any]] = None) -> AzureConversationTracker:
    """
    Get or create conversation tracker singleton

    Args:
        config: Goal configuration (required on first call)

    Returns:
        AzureConversationTracker instance
    """
    global _conversation_tracker

    if _conversation_tracker is None:
        if config is None:
            # Load from environment
            config = {
                "conversation_api": {
                    "enabled": os.getenv("CONVERSATION_API_ENABLED", "false").lower() == "true",
                    "endpoint": os.getenv("CONVERSATION_API_ENDPOINT"),
                    "project_name": os.getenv("CONVERSATION_API_PROJECT"),
                }
            }

        _conversation_tracker = AzureConversationTracker(config)

    return _conversation_tracker


def reset_conversation_tracker():
    """Reset global tracker (useful for testing)"""
    global _conversation_tracker
    _conversation_tracker = None
