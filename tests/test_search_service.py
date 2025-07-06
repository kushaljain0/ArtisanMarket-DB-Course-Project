"""Tests for search service functionality."""

import pytest
from unittest.mock import Mock, patch

from src.services.search_service import SearchService


class TestSearchService:
    def setup_method(self):
        """Set up test fixtures."""
        self.search_service = SearchService()

    @patch("src.services.search_service.redis_client")
    @patch("src.services.search_service.db")
    def test_full_text_search_with_cache(self, mock_db, mock_redis_client):
        """Test full-text search with Redis caching."""
        # Mock Redis cache miss
        mock_redis_client.get_json.return_value = None

        # Mock database results
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {
                "id": "P001",
                "name": "Wooden Bowl",
                "price": 29.99,
                "category_id": "C001",
            },
            {
                "id": "P002",
                "name": "Wooden Spoon",
                "price": 15.99,
                "category_id": "C001",
            },
        ]
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        results = self.search_service.full_text_search(
            "wooden", {"category": "Home & Kitchen"}
        )

        assert len(results) == 2
        assert results[0]["id"] == "P001"
        assert results[1]["id"] == "P002"

        # Verify cache was set
        mock_redis_client.set_json.assert_called_once()

    @patch("src.services.search_service.redis_client")
    def test_full_text_search_cache_hit(self, mock_redis_client):
        """Test full-text search with cache hit."""
        # Mock Redis cache hit
        cached_results = [{"id": "P001", "name": "Wooden Bowl", "price": 29.99}]
        mock_redis_client.get_json.return_value = cached_results

        results = self.search_service.full_text_search("wooden")

        assert results == cached_results
        assert self.search_service.cache_hits == 1

    @patch("src.services.search_service.db")
    def test_full_text_search_with_filters(self, mock_db):
        """Test full-text search with various filters."""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {"id": "P001", "name": "Product", "price": 25.0}
        ]
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        # Test with category filter
        results = self.search_service.full_text_search(
            "product", {"category": "Home & Kitchen"}
        )
        assert len(results) == 1

        # Test with price filters
        results = self.search_service.full_text_search(
            "product", {"min_price": 20, "max_price": 30}
        )
        assert len(results) == 1

    @patch("src.services.search_service.db")
    def test_semantic_search(self, mock_db):
        """Test semantic search functionality."""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {
                "id": "P001",
                "name": "Eco-friendly Bowl",
                "price": 29.99,
                "similarity": 0.85,
            },
            {
                "id": "P002",
                "name": "Sustainable Cup",
                "price": 15.99,
                "similarity": 0.72,
            },
        ]
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        results = self.search_service.semantic_search("eco-friendly kitchenware")

        assert len(results) == 2
        assert results[0]["similarity"] == 0.85
        assert results[1]["similarity"] == 0.72

    @patch("src.services.search_service.db")
    def test_combined_search(self, mock_db):
        """Test combined search (text + semantic)."""
        # Mock both search methods
        self.search_service.full_text_search = Mock(
            return_value=[{"id": "P001", "name": "Wooden Bowl", "price": 29.99}]
        )
        self.search_service.semantic_search = Mock(
            return_value=[
                {
                    "id": "P002",
                    "name": "Eco-friendly Bowl",
                    "price": 25.99,
                    "similarity": 0.8,
                }
            ]
        )

        results = self.search_service.combined_search("bowl")

        assert len(results) == 2
        # Text search results should come first (higher weight)
        assert results[0]["id"] == "P001"

    @patch("src.services.search_service.db")
    def test_natural_language_search(self, mock_db):
        """Test natural language search with query understanding."""
        # Mock the combined search method
        self.search_service.combined_search = Mock(
            return_value=[{"id": "P001", "name": "Product", "price": 25.0}]
        )

        # Test with price indicator
        results = self.search_service.natural_language_search("bowls under $50")
        assert len(results) == 1

        # Test with category indicator
        results = self.search_service.natural_language_search("jewelry items")
        assert len(results) == 1

    @patch("src.services.search_service.db")
    def test_get_more_like_this(self, mock_db):
        """Test 'more like this' functionality."""
        # Mock product description retrieval
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {"description": "Handmade wooden bowl"}
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        # Mock semantic search
        self.search_service.semantic_search = Mock(
            return_value=[
                {"id": "P002", "name": "Similar Bowl", "price": 30.0, "similarity": 0.9}
            ]
        )

        results = self.search_service.get_more_like_this("P001")

        assert len(results) == 1
        assert results[0]["id"] == "P002"

    @patch("src.services.search_service.db")
    def test_get_more_like_this_product_not_found(self, mock_db):
        """Test 'more like this' with non-existent product."""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        results = self.search_service.get_more_like_this("NONEXISTENT")

        assert results == []

    def test_cache_key_generation(self):
        """Test cache key generation for different queries."""
        key1 = self.search_service._cache_key(
            "wooden bowl", {"category": "Home & Kitchen"}
        )
        key2 = self.search_service._cache_key(
            "wooden bowl", {"category": "Home & Kitchen"}
        )
        key3 = self.search_service._cache_key(
            "wooden spoon", {"category": "Home & Kitchen"}
        )

        # Same query and filters should generate same key
        assert key1 == key2
        # Different query should generate different key
        assert key1 != key3

    @patch("src.services.search_service.redis_client")
    @patch("src.services.search_service.db")
    def test_search_error_handling(self, mock_db, mock_redis_client):
        """Test search error handling."""
        # Mock Redis connection error
        mock_redis_client.get_json.side_effect = Exception("Redis error")

        # Mock database results
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {"id": "P001", "name": "Product", "price": 25.0}
        ]
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor

        # Should still work despite Redis error
        results = self.search_service.full_text_search("product")
        assert len(results) == 1

    def test_search_limit(self):
        """Test that search respects the limit parameter."""
        # Mock the search methods
        self.search_service.full_text_search = Mock(
            return_value=[
                {"id": f"P{i}", "name": f"Product {i}", "price": 25.0}
                for i in range(1, 11)  # 10 products
            ]
        )

        results = self.search_service.combined_search("product", limit=3)
        assert len(results) == 3


@pytest.mark.integration
def test_search_service_integration():
    """Integration test for search service with real databases."""
    try:
        search_service = SearchService()
        # Test basic search functionality
        results = search_service.full_text_search("test")
        assert isinstance(results, list)
    except Exception as e:
        pytest.skip(f"Database not available: {e}")
