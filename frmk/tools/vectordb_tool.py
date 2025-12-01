"""
Vector Database Tool
Common implementation for semantic search and vector operations
"""

from typing import Dict, Any, List, Optional
import os
from .base_tool import BaseTool, ToolOutput
from frmk.utils.logging import get_logger


class VectorDBTool(BaseTool):
    """
    Vector Database tool for semantic search

    Supported vector databases:
    - Azure AI Search (Cognitive Search with vector support)
    - Pinecone
    - Weaviate
    - Qdrant
    - Chroma

    Configuration from spec:
    {
      "type": "vectordb",
      "spec": {
        "provider": "azure_ai_search|pinecone|weaviate|qdrant|chroma",
        "endpoint": "${VECTORDB_ENDPOINT}",
        "api_key": "${VECTORDB_API_KEY}",
        "index_name": "documents",
        "embedding_model": "text-embedding-ada-002",
        "top_k": 5,
        "score_threshold": 0.7
      }
    }
    """

    def __init__(self, name: str, description: str, tool_config: Dict[str, Any]):
        super().__init__(name, description, tool_config)

        self.logger = get_logger(f"tool.{name}")

        spec = tool_config.get("spec", {})

        self.provider = spec.get("provider", "azure_ai_search")
        self.endpoint = self._resolve_env_vars(spec.get("endpoint", ""))
        self.api_key = self._resolve_env_vars(spec.get("api_key", ""))
        self.index_name = spec.get("index_name", "documents")
        self.embedding_model = spec.get("embedding_model", "text-embedding-ada-002")
        self.top_k = spec.get("top_k", 5)
        self.score_threshold = spec.get("score_threshold", 0.7)

        # Lazy initialization
        self._client = None
        self._embedding_client = None

    def _resolve_env_vars(self, value: str) -> str:
        """Resolve ${VAR} in configuration"""
        import re

        def replacer(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))

        return re.sub(r'\$\{(\w+)\}', replacer, value)

    def _get_embedding_client(self):
        """Get OpenAI client for embeddings (lazy initialization)"""
        if self._embedding_client is not None:
            return self._embedding_client

        try:
            from openai import AzureOpenAI

            # Get Azure OpenAI credentials from environment
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_OPENAI_KEY")

            if not endpoint or not api_key:
                raise ValueError("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY required for embeddings")

            self._embedding_client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version="2024-02-01"
            )

            self.logger.info("Embedding client initialized")
            return self._embedding_client

        except ImportError:
            raise ImportError("OpenAI SDK not installed. Install with: pip install openai")

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text"""

        client = self._get_embedding_client()

        response = client.embeddings.create(
            input=text,
            model=self.embedding_model
        )

        return response.data[0].embedding

    def _get_client(self):
        """Get vector database client (lazy initialization)"""
        if self._client is not None:
            return self._client

        if self.provider == "azure_ai_search":
            return self._init_azure_ai_search()
        elif self.provider == "pinecone":
            return self._init_pinecone()
        elif self.provider == "weaviate":
            return self._init_weaviate()
        elif self.provider == "qdrant":
            return self._init_qdrant()
        elif self.provider == "chroma":
            return self._init_chroma()
        else:
            raise ValueError(f"Unsupported vector database: {self.provider}")

    def _init_azure_ai_search(self):
        """Initialize Azure AI Search client"""
        try:
            from azure.search.documents import SearchClient
            from azure.core.credentials import AzureKeyCredential

            self._client = SearchClient(
                endpoint=self.endpoint,
                index_name=self.index_name,
                credential=AzureKeyCredential(self.api_key)
            )

            self.logger.info("Azure AI Search client initialized")
            return self._client

        except ImportError:
            raise ImportError("Azure Search SDK not installed. Install with: pip install azure-search-documents")

    def _init_pinecone(self):
        """Initialize Pinecone client"""
        try:
            from pinecone import Pinecone

            self._client = Pinecone(api_key=self.api_key)
            self.logger.info("Pinecone client initialized")
            return self._client

        except ImportError:
            raise ImportError("Pinecone SDK not installed. Install with: pip install pinecone-client")

    def _init_weaviate(self):
        """Initialize Weaviate client"""
        try:
            import weaviate

            self._client = weaviate.Client(
                url=self.endpoint,
                auth_client_secret=weaviate.AuthApiKey(self.api_key)
            )

            self.logger.info("Weaviate client initialized")
            return self._client

        except ImportError:
            raise ImportError("Weaviate SDK not installed. Install with: pip install weaviate-client")

    def _init_qdrant(self):
        """Initialize Qdrant client"""
        try:
            from qdrant_client import QdrantClient

            self._client = QdrantClient(
                url=self.endpoint,
                api_key=self.api_key
            )

            self.logger.info("Qdrant client initialized")
            return self._client

        except ImportError:
            raise ImportError("Qdrant SDK not installed. Install with: pip install qdrant-client")

    def _init_chroma(self):
        """Initialize Chroma client"""
        try:
            import chromadb

            self._client = chromadb.HttpClient(
                host=self.endpoint.replace("http://", "").replace("https://", ""),
                settings=chromadb.Settings()
            )

            self.logger.info("Chroma client initialized")
            return self._client

        except ImportError:
            raise ImportError("Chroma SDK not installed. Install with: pip install chromadb")

    async def execute(self, query: str, filters: Optional[Dict[str, Any]] = None, **kwargs) -> ToolOutput:
        """
        Search vector database

        Args:
            query: Search query text
            filters: Optional metadata filters
            **kwargs: Provider-specific parameters

        Returns:
            ToolOutput with search results
        """

        try:
            self.logger.info(f"Searching vector DB for: '{query[:50]}...'")

            # Generate embedding for query
            query_vector = await self._generate_embedding(query)

            # Get client
            client = self._get_client()

            # Search based on provider
            if self.provider == "azure_ai_search":
                results = await self._search_azure_ai_search(query, query_vector, filters)
            elif self.provider == "pinecone":
                results = self._search_pinecone(query_vector, filters)
            elif self.provider == "weaviate":
                results = self._search_weaviate(query_vector, filters)
            elif self.provider == "qdrant":
                results = self._search_qdrant(query_vector, filters)
            elif self.provider == "chroma":
                results = self._search_chroma(query_vector, filters)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

            self.logger.info(f"Found {len(results)} results")

            return ToolOutput(
                success=True,
                data={
                    "results": results,
                    "query": query,
                    "count": len(results)
                },
                metadata={
                    "provider": self.provider,
                    "index": self.index_name,
                    "top_k": self.top_k
                }
            )

        except Exception as e:
            self.logger.error(f"Vector search failed: {e}")
            return ToolOutput(
                success=False,
                error=str(e),
                metadata={"query": query}
            )

    async def _search_azure_ai_search(self, query: str, vector: List[float], filters: Optional[Dict]) -> List[Dict]:
        """Search Azure AI Search with vector"""

        from azure.search.documents.models import VectorizedQuery

        vector_query = VectorizedQuery(
            vector=vector,
            k_nearest_neighbors=self.top_k,
            fields="embedding"
        )

        results = self._client.search(
            search_text=query,
            vector_queries=[vector_query],
            select=["id", "content", "metadata"],
            top=self.top_k
        )

        return [
            {
                "id": doc.get("id"),
                "content": doc.get("content"),
                "score": doc.get("@search.score"),
                "metadata": doc.get("metadata", {})
            }
            for doc in results
            if doc.get("@search.score", 0) >= self.score_threshold
        ]

    def _search_pinecone(self, vector: List[float], filters: Optional[Dict]) -> List[Dict]:
        """Search Pinecone"""

        index = self._client.Index(self.index_name)

        results = index.query(
            vector=vector,
            top_k=self.top_k,
            include_metadata=True,
            filter=filters
        )

        return [
            {
                "id": match.id,
                "score": match.score,
                "metadata": match.metadata
            }
            for match in results.matches
            if match.score >= self.score_threshold
        ]

    def _search_weaviate(self, vector: List[float], filters: Optional[Dict]) -> List[Dict]:
        """Search Weaviate"""

        result = (
            self._client.query
            .get(self.index_name, ["content", "metadata"])
            .with_near_vector({"vector": vector})
            .with_limit(self.top_k)
            .do()
        )

        data = result.get("data", {}).get("Get", {}).get(self.index_name, [])

        return [
            {
                "content": item.get("content"),
                "metadata": item.get("metadata", {}),
                "score": item.get("_additional", {}).get("distance", 0)
            }
            for item in data
        ]

    def _search_qdrant(self, vector: List[float], filters: Optional[Dict]) -> List[Dict]:
        """Search Qdrant"""

        results = self._client.search(
            collection_name=self.index_name,
            query_vector=vector,
            limit=self.top_k,
            query_filter=filters
        )

        return [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload
            }
            for hit in results
            if hit.score >= self.score_threshold
        ]

    def _search_chroma(self, vector: List[float], filters: Optional[Dict]) -> List[Dict]:
        """Search Chroma"""

        collection = self._client.get_collection(self.index_name)

        results = collection.query(
            query_embeddings=[vector],
            n_results=self.top_k,
            where=filters
        )

        return [
            {
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            }
            for i in range(len(results["ids"][0]))
        ]

    def get_schema(self) -> Dict[str, Any]:
        """Get JSON schema for vector search parameters"""

        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query text (will be converted to embedding vector)"
                },
                "filters": {
                    "type": "object",
                    "description": f"Metadata filters (provider: {self.provider})",
                    "additionalProperties": True
                }
            },
            "required": ["query"]
        }

    async def close(self):
        """Close connections"""
        if self._client:
            # Close provider-specific connections
            if hasattr(self._client, 'close'):
                self._client.close()
            self.logger.info("Vector DB connection closed")
