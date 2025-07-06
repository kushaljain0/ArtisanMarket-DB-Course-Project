import hashlib
import json
from contextlib import suppress
from typing import Any

from sentence_transformers import SentenceTransformer

from src.db.postgres_client import db
from src.db.redis_client import redis_client


class SearchService:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.cache_hits = 0

    def _cache_key(self, query: str, filters: dict) -> str:
        key = json.dumps({"query": query, "filters": filters}, sort_keys=True)
        return "search:" + hashlib.sha256(key.encode()).hexdigest()

    def full_text_search(
        self, query: str, filters: dict = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        filters = filters or {}
        cache_key = self._cache_key(query, filters)

        # Try to get from cache, but don't fail if Redis is not available
        with suppress(Exception):
            cached = redis_client.get_json(cache_key)
            if cached:
                self.cache_hits += 1
                return cached

        # Base SQL query
        if "category" in filters:
            # Need to join with categories table to filter by category name
            sql = """
                SELECT p.* FROM products p
                JOIN categories c ON p.category_id = c.id
                WHERE (p.name ILIKE %s OR p.description ILIKE %s OR p.tags ILIKE %s)
            """
            params = [f"%{query}%"] * 3
            sql += " AND c.name = %s"
            params.append(filters["category"])
        else:
            sql = """
                SELECT * FROM products
                WHERE (name ILIKE %s OR description ILIKE %s OR tags ILIKE %s)
            """
            params = [f"%{query}%"] * 3
        if "min_price" in filters:
            sql += " AND price >= %s"
            params.append(filters["min_price"])
        if "max_price" in filters:
            sql += " AND price <= %s"
            params.append(filters["max_price"])
        sql += " LIMIT %s"
        params.append(limit)
        with db.get_cursor() as cursor:
            cursor.execute(sql, params)
            results = cursor.fetchall()

        # Try to cache results, but don't fail if Redis is not available
        with suppress(Exception):
            redis_client.set_json(cache_key, results, ttl=3600)

        return results

    def semantic_search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search products using semantic similarity."""
        # Generate embedding for search query
        query_embedding = self.model.encode(query)

        # Find similar products using pgvector
        with db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT p.*,
                       1 - (pe.description_embedding <=> %s::vector) as similarity
                FROM products p
                JOIN product_embeddings pe ON p.id = pe.product_id
                ORDER BY pe.description_embedding <=> %s::vector
                LIMIT %s;
                """,
                (query_embedding.tolist(), query_embedding.tolist(), limit),
            )
            return cursor.fetchall()

    def combined_search(
        self, query: str, filters: dict = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Combine full-text and semantic search for better results."""
        filters = filters or {}

        # Get results from both search methods
        text_results = self.full_text_search(query, filters, limit)
        semantic_results = self.semantic_search(query, limit)

        # Create a combined result set
        combined_results = {}

        # Add text search results with higher weight
        for result in text_results:
            product_id = result["id"]
            combined_results[product_id] = {
                "product": result,
                "score": 1.0,  # High weight for exact matches
                "source": "text",
            }

        # Add semantic search results with lower weight
        for result in semantic_results:
            product_id = result["id"]
            if product_id in combined_results:
                # Boost score if found in both searches
                combined_results[product_id]["score"] += result["similarity"] * 0.5
                combined_results[product_id]["source"] = "combined"
            else:
                combined_results[product_id] = {
                    "product": result,
                    "score": result["similarity"] * 0.5,
                    "source": "semantic",
                }

        # Sort by combined score and return top results
        sorted_results = sorted(
            combined_results.values(), key=lambda x: x["score"], reverse=True
        )

        return [item["product"] for item in sorted_results[:limit]]

    def natural_language_search(
        self, query: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Enhanced natural language search with query understanding."""
        # Simple query preprocessing
        query_lower = query.lower()

        # Extract potential filters from query
        filters = {}

        # Check for price indicators
        if "under" in query_lower and "$" in query:
            # Extract price from query like "under $50"
            import re

            price_match = re.search(r"\$(\d+)", query)
            if price_match:
                filters["max_price"] = float(price_match.group(1))

        # Check for category indicators
        categories = ["jewelry", "kitchen", "home", "art", "craft"]
        for category in categories:
            if category in query_lower:
                filters["category"] = category.title()
                break

        # Use combined search with extracted filters
        return self.combined_search(query, filters, limit)

    def get_more_like_this(
        self, product_id: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Find products similar to the given product using semantic search."""
        # Get product description
        with db.get_cursor() as cursor:
            cursor.execute(
                "SELECT description FROM products WHERE id = %s", (product_id,)
            )
            result = cursor.fetchone()

            if not result:
                return []

            # Use the product description for semantic search
            return self.semantic_search(result["description"], limit)


if __name__ == "__main__":
    service = SearchService()
    print("Full-text search results:")
    print(service.full_text_search("wooden bowl", {"category": "Home & Kitchen"}))
    print("Semantic search results:")
    print(service.semantic_search("eco-friendly kitchenware"))
    print(f"Cache hits: {service.cache_hits}")
